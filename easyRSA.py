from os import path, mkdir
from subprocess import Popen, PIPE, CalledProcessError
from ovw import asset, app
from datetime import datetime

def asntime_to_datetime(asn_time):
	if len(asn_time) != 13 and asn_time[12:] != 'Z':
		return None
	return datetime(
		year	= 2000+int(asn_time[:2]),
		month	= int(asn_time[2:4]),
		day		= int(asn_time[4:6]),
		hour	= int(asn_time[6:8]),
		minute	= int(asn_time[8:10]),
		second	= int(asn_time[10:12])
	)

class EasyCert(object):
	def __init__(self, content):
		self.state		= content[0]
		self.expire_at	= asntime_to_datetime(content[1])
		self.revoked_at	= asntime_to_datetime(content[2])
		self.serial		= int(content[3], 16)
		self.uknown		= content[4]
		self.identity	= {}
		for i in content[5].split('/'):
			if len(i.strip()) == 0:
				continue
			k,v = i.split('=')
			self.identity[k] = v.strip()
		self.name 		= self.identity['CN']

	def getProperty(self, p):
		return self.identity[p]
	
	@property
	def is_revokable(self):
		if self.serial==1:
			return False
		return True
	
	def __repr__(self):
		return "EasyCert(%s)" % self.name

class EasyRSA(object):
	"""
	e = EasyRSA('test')
	e.initInfrastructure()
	e.buildDH()
	e.buildCA()
	e.buildKey("server", True)
	e.buildKey("client1")
	print e.listCerts()
	e.revokeKey("client1")
	"""
	def __init__(self, key_dir, env = {}):
		self.key_dir = path.abspath(key_dir)
		# global env
		self.env = {
			"KEY_DIR"				: self.key_dir,
			"KEY_SIZE"				: "1024",
			"KEY_DAYS"				: "3650",
			"KEY_COUNTRY"			: "US",
			"KEY_PROVINCE"			: "CA",
			"KEY_CITY"				: "SanFrancisco",
			"KEY_ORG"				: "Fort-Funston",
			"KEY_EMAIL"				: "me@myhost.mydomain",
			"KEY_OU"				: "openvpn",
			"KEY_CN"				: "",
			"KEY_NAME"				: "",
			"PKCS11_MODULE_PATH"	: "dummy",
			"PKCS11_PIN"			: "dummy"
		}
		self.env.update(env)
		# other options
		self.key_index		= path.join(self.key_dir, 'index.txt')
		self.key_serial		= path.join(self.key_dir, 'serial')
		self.file_dh		= path.join(self.key_dir, 'dh1024.pem')
		self.file_ca_crt	= path.join(self.key_dir, 'ca.crt')
		self.file_ca_key	= path.join(self.key_dir, 'ca.key')
		self.file_crl		= path.join(self.key_dir, 'crl.pem')
		self.file_openssl	= path.abspath(asset('openssl.cnf'))
		
	def _exec(self, args):
		p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=self.key_dir, env=self.env)
		stdout, stderr = p.communicate()
		retcode = p.poll()
		if retcode:
			app.logger.error("openssl returned error: %s" % stderr)
			raise CalledProcessError(retcode, args, output=stderr)
		return stdout
	
	def initInfrastructure(self):
		if not path.exists(self.key_dir):
			mkdir(self.key_dir)
			open(self.key_index, "w").close()
			f = open(self.key_serial, "w")
			f.write("01")
			f.close()
	
	def buildDH(self):
		if path.exists(self.file_dh):
			print "DH already exists:", self.file_dh
		else:
			args = [ "openssl", "dhparam", "-out", self.file_dh, self.env["KEY_SIZE"] ]
			self._exec(args)
	
	def buildCA(self):
		self.env['KEY_CN'] = "ca"
		self.env['KEY_NAME'] = "ca"
		if path.exists(self.file_ca_key) and path.exists(self.file_ca_crt):
			print "CA already exists:", self.file_ca_crt, self.file_ca_key
		else:
			args = [ "openssl", "req", 
				"-batch", "-days", self.env["KEY_DAYS"], "-nodes", "-new", 
				"-newkey", "rsa:%s" % self.env["KEY_SIZE"], 
				"-sha1", "-x509", 
				"-keyout", self.file_ca_key, 
				"-out", self.file_ca_crt, 
				"-config", self.file_openssl
			]
			self._exec(args)
			self.updateCRL()

	def buildKey(self, name, password=None, server=False):
		self.env['KEY_CN'] = name
		self.env['KEY_NAME'] = name
		key = path.join(self.key_dir, '%s.key' % name)
		csr = path.join(self.key_dir, '%s.csr' % name)
		crt = path.join(self.key_dir, '%s.crt' % name)

		if path.exists(key) and path.exists(csr) and path.exists(crt):
			print "Cert already exists:", self.file_ca_crt, self.file_ca_key
		else:
			extensions = []
			if server:
				extensions += [ "-extensions", "server" ]
			# gen keys
			args = [ "openssl", "req" ]
			args += [ "-batch", "-days", self.env["KEY_DAYS"] ]
			if password:
				args += [ "-passout", "pass:%s" % password ]
			else:
				args += [ "-nodes" ]
			args += [ "-new" ]
			args += [ "-newkey", "rsa:%s" % self.env["KEY_SIZE"] ]
			args += [ "-keyout", key ]
			args += [ "-out", csr ]
			args += [ "-config", self.file_openssl ]
			self._exec(args + extensions)
			# sign
			args = [ "openssl", "ca", 
				"-batch", "-days", self.env["KEY_DAYS"], 
				"-out", crt, 
				"-in", csr, 
				"-md", "sha1", 
				"-config", self.file_openssl
			]
			self._exec(args + extensions)

	def listKeySet(self, name):
		key_set = []
		key_set.append(self.file_ca_crt)
		key_set.append(path.join(self.key_dir, '%s.key' % name))
		key_set.append(path.join(self.key_dir, '%s.crt' % name))
		for i in key_set:
			if not path.exists(i):
				return None
		return key_set

	def updateCRL(self):
		args = [ "openssl", "ca",
			"-gencrl",
			"-out", "crl.pem",
			"-config", self.file_openssl
		]
		self._exec(args)

	def updateDB(self):
		args = [ "openssl", "ca",
			"-updatedb",
			"-config", self.file_openssl
		]
		self._exec(args)

	def revokeKey(self, name):
		self.env['KEY_CN'] = name
		self.env['KEY_NAME'] = name
		key = path.join(self.key_dir, '%s.key' % name)
		csr = path.join(self.key_dir, '%s.csr' % name)
		crt = path.join(self.key_dir, '%s.crt' % name)

		if path.exists(key) and path.exists(csr) and path.exists(crt):
			args = [ "openssl", "ca",
				"-revoke", crt,
				"-config", self.file_openssl
			]
			self._exec(args)
			self.updateCRL()
		else:
			print "Cert not exists:", self.file_ca_crt, self.file_ca_key

	def listCerts(self):
		if not path.exists(self.key_index):
			return None

		self.updateDB()
		ls = []
		f = open(self.key_index)
		for l in f.readlines():
			a = l.split('\t')
			c = EasyCert(a)
			ls.append(c)
		return ls