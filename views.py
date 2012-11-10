from application import *
from forms import *
from jinja2 import Template

from os import path, mkdir
from shutil import rmtree, copy, make_archive

import config

from remote import *
from easyRSA import *
e = EasyRSA(config.APP_KEYDIR)

@app.route("/login", methods=['GET', 'POST'])
def login():
	f = UserLoginForm(request.form)
	if request.method == 'POST' and f.validate():
		if config.APP_USERS.has_key(f.name.data) and config.APP_USERS[f.name.data] == f.password.data:
			if f.remember.data:
				session.permanent = True
			session['u'] = f.name.data
			session['p'] = f.password.data
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
	e.buildDH()
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
	f.write(t.render(name=name, servers=config.APP_VPN_SERVERS))
	f.close()
	
	make_archive(kd, 'zip', kd)
	return send_from_directory(config.APP_TMPDIR, '%s.zip' % name, as_attachment=True)
