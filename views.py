from ovw import *
from forms import *
from jinja2 import Template

from os import path, mkdir, listdir, unlink
from shutil import rmtree, copy
from zipfile import ZipFile, ZIP_DEFLATED
from functools import wraps

import hashlib

from easyRSA import *
e = EasyRSA(app.config['KEY_DIR'], app.config['KEY_ENV'])

@app.before_request
def before_request():
	if session.has_key('u') and session.has_key('p'):
		if app.config['USERS'].has_key(session['u']) and app.config['USERS'][session['u']] == session['p']:
			g.user = session['u']
		else:
			g.user = None
	else:
		g.user = None

def require_login(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if g.user is None:
			return redirect(url_for('login', next=request.url))
		return f(*args, **kwargs)
	return decorated_function

@app.errorhandler(404)
def page_not_found(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(error):
	return render_template('500.html'), 500

@app.route("/login", methods=['GET', 'POST'])
def login():
	f = UserLoginForm(request.form)
	if request.method == 'POST' and f.validate():
		phash = hashlib.sha256(f.password.data).hexdigest()
		if app.config['USERS'].has_key(f.name.data) and app.config['USERS'][f.name.data] == phash:
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
	e.buildDH()
	e.buildKey("server", server=True)
	return redirect('/')

@app.route("/generate", methods=['GET', 'POST'])
@require_login
def generate():
	f = CertificateForm(request.form)
	if request.method == 'POST' and f.validate():
		e.buildKey(f.name.data, password=f.password.data)
		return redirect('/')
	return render_template('form.html', form=f, title="Generate certificate")
	
@app.route("/revoke/<string:name>")
@require_login
def revoke(name):
	e.revokeKey(name)
	# TODO: bug in Crypto - initialization should be prformed from worker thread
	from remote import sync_file
	if not sync_file(e.file_crl, app.config['VPN_CRL'], app.config['VPN_SERVERS'], app.config['VPN_SERVERS_USER']):
		flash('Crl not synced, check logs' ,'error')
	else:
		flash('Crl synced, certificate revoked' ,'success')
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
	archive_name = '%s.zip' % name
	
	l = e.listKeySet(name)
	kd = path.join(app.config['TMP_DIR'], name)
	if path.exists(kd):
		rmtree(kd)
	mkdir(kd)
	for i in l:
		copy(i, path.join(kd, path.split(i)[1]))
	
	t = Template(open(asset("openvpn.tmpl"), "r").read())
	f = open(path.join(kd, "openvpn.ovpn"), "w")
	f.write(t.render(name=name, servers=app.config['VPN_TMPL_SERVERS']))
	f.close()
	
	z = ZipFile(path.join(app.config['TMP_DIR'], archive_name), mode='w')
	recursive_zip(z, kd)
	z.close()
	
	@after_this_request
	def add_header(response):
		rmtree(kd)
		unlink(path.join(app.config['TMP_DIR'], archive_name))
		return response
	
	return send_from_directory(app.config['TMP_DIR'], archive_name, as_attachment=True)
