from os import path, mkdir
from subprocess import Popen, PIPE, CalledProcessError

class EasyCert(object):
	def __init__(self, content):
		self.state		= content[0]
		self.issued		= content[1]
		self.revoked	= content[2]
		self.serial		= content[3]
		self.uknown		= content[4]
		self.identity	= {}
		for i in content[5].split('/'):
			if len(i.strip()) == 0:
				continue
			k,v = i.split('=')
			self.identity[k] = v.strip()
		self.name 		= self.identity['name']

	def getProperty(self, p):
		return self.identity[p]
	
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
	def __init__(self, dir):
		dir = path.abspath(dir)
		# global env
		self.env = {
			"KEY_DIR"				: path.join(dir, 'keys'),
			"KEY_SIZE"				: "1024",
			"KEY_COUNTRY"			: "US",
			"KEY_PROVINCE"			: "CA",
			"KEY_CITY"				: "SanFrancisco",
			"KEY_ORG"				: "Fort-Funston",
			"KEY_EMAIL"				: "me@myhost.mydomain",
			"KEY_OU"				: "openvpn",
			"PKCS11_MODULE_PATH"	: "dummy",
			"PKCS11_PIN"			: "dummy"
		}
		
		self.base_dir		= dir;
		self.key_dir		= path.join(dir, 'keys')
		self.key_index		= path.join(dir, 'keys', 'index.txt')
		self.key_serial		= path.join(dir, 'keys', 'serial')

		self.file_dh		= path.join(dir, 'keys', 'dh1024.pem')
		self.file_ca_crt	= path.join(dir, 'keys', 'ca.crt')
		self.file_ca_key	= path.join(dir, 'keys', 'ca.key')
		self.file_crl		= path.join(dir, 'keys', 'crl.pem')
		self.file_openssl	= path.join(path.abspath(path.dirname(__file__)), 'openssl.cnf')
		
	def _exec(self, args):
		p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=self.key_dir, env=self.env)
		stdout, stderr = p.communicate()
		retcode = p.poll()
		if retcode:
			raise CalledProcessError(retcode, args, output=stderr)
		return stdout
	
	def initInfrastructure(self):
		if not path.exists(self.base_dir):
			mkdir(self.base_dir)
			mkdir(self.key_dir)
			open(self.key_index, "w").close()
			f = open(self.key_serial, "w")
			f.write("01")
			f.close()
	
	def buildDH(self):
		if path.exists(self.file_dh):
			print "DH already exists:", self.file_dh
		else:
			args = [ "openssl", "dhparam", "-out", self.file_dh, "1024" ]
			self._exec(args)
	
	def buildCA(self):
		self.env['KEY_CN'] = "ca"
		self.env['KEY_NAME'] = "ca"
		if path.exists(self.file_ca_key) and path.exists(self.file_ca_crt):
			print "CA already exists:", self.file_ca_crt, self.file_ca_key
		else:
			args = [ "openssl", "req", 
				"-batch", "-days", "3650", "-nodes", "-new", 
				"-newkey", "rsa:1024", 
				"-sha1", "-x509", 
				"-keyout", self.file_ca_key, 
				"-out", self.file_ca_crt, 
				"-config", self.file_openssl
			]
			self._exec(args)
			self.updateCRL()

	def buildKey(self, name, server=False):
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
			args = [ "openssl", "req", 
				"-batch", "-days", "3650", "-nodes", "-new", 
				"-newkey", "rsa:1024", 
				"-keyout", key, 
				"-out", csr, 
				"-config", self.file_openssl
				]
			self._exec(args + extensions)
			# sign
			args = [ "openssl", "ca", 
				"-batch", "-days", "3650", 
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
		key_set.append(path.join(self.key_dir, '%s.csr' % name))
		key_set.append(path.join(self.key_dir, '%s.crt' % name))
		for i in key_set:
			if not path.exists(i):
				return None
		return key_set

	def updateCRL(self):
		args = [ "openssl", "ca",
			"-gencrl", "-out", "crl.pem",
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
			print "Cert already exists:", self.file_ca_crt, self.file_ca_key

	def listCerts(self):
		if not path.exists(self.key_index):
			return None
		
		ls = []
		f = open(self.key_index)
		for l in f.readlines():
			a = l.split('\t')
			c = EasyCert(a)
			ls.append(c)
		return ls