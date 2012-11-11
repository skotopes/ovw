from application import *
from forms import *
from jinja2 import Template

from os import path, mkdir, listdir
from shutil import rmtree, copy
from zipfile import ZipFile, ZIP_DEFLATED

import config, hashlib

from remote import *
from easyRSA import *
e = EasyRSA(config.APP_KEY_DIR, config.APP_KEY_ENV)

@app.route("/login", methods=['GET', 'POST'])
def login():
	f = UserLoginForm(request.form)
	if request.method == 'POST' and f.validate():
		phash = hashlib.sha256(f.password.data).hexdigest()
		if config.APP_USERS.has_key(f.name.data) and config.APP_USERS[f.name.data] == phash:
			if f.remember.data:
				session.permanent = True
			session['u'] = f.name.data
			session['p'] = phash
			g.user = f.name.data
			flash('Hi %s, Nice to see you again!' % g.user,'success')
			# insure that we do not redirect user outside.
			if f.next.data.startswith(request.host_url):
				return redirect(f.next.data)
			else:
				return redirect('/')
	return render_template('form.html', form=f, title="Login")

@app.route("/logout", methods=['GET', 'POST'])
@require_login
def logout():
	session.clear()
	g.user = None
	flash('Sessions wiped, bye-bye!', 'success')
	return redirect('/')

@app.route("/")
@require_login
def index():
	l = e.listCerts()
	return render_template('index.html', keylist = l)

@app.route("/initialize", methods=['GET', 'POST'])
@require_login
def initialize():
	e.initInfrastructure()
	e.buildCA()
	return redirect('/')

@app.route("/generate", methods=['GET', 'POST'])
@require_login
def generate():
	f = CertificateForm(request.form)
	if request.method == 'POST' and f.validate():
		e.buildKey(f.name.data, f.server.data)
		if not sync_file(e.file_crl, config.APP_VPN_CRL, config.APP_VPN_SERVERS):
			flash('Crl not synced, check logs' ,'error')
		return redirect('/')
	return render_template('form.html', form=f, title="Generate certificate")
	
@app.route("/revoke/<string:name>")
@require_login
def revoke(name):
	e.revokeKey(name)
	if not sync_file(e.file_crl, config.APP_VPN_CRL, config.APP_VPN_SERVERS):
		flash('Crl not synced, check logs' ,'error')
	return redirect('/')

def recursive_zip(zipf, base, ptr=None):
	if not ptr:
		ptr = base
	nodes = listdir(ptr)
	for item in nodes:
		item = path.join(ptr, item)
		if path.isfile(item):
			zipf.write(item, path.relpath(item, base))
		elif path.isdir(item):
			recursive_zip(zipf, base, item)

@app.route("/download/<string:name>")
@require_login
def download(name):
	l = e.listKeySet(name)
	kd = path.join(config.APP_TMPDIR, name)
	if path.exists(kd):
		rmtree(kd)
	mkdir(kd)
	for i in l:
		copy(i, path.join(kd, path.split(i)[1]))
	
	t = Template(open("openvpn.tmpl").read())
	f = open(path.join(kd, "openvpn.conf"), "w")
	f.write(t.render(name=name, servers=config.APP_VPN_TMPL_SERVERS))
	f.close()
	
	z = ZipFile(path.join(config.APP_TMPDIR, '%s.zip' % name), mode='w')
	recursive_zip(z, kd)
	z.close()
	return send_from_directory(config.APP_TMPDIR, '%s.zip' % name, as_attachment=True)
