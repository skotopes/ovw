from functools import wraps
from flask import *

import config

app = Flask(__name__)

app.debug = config.APP_DEBUG
app.secret_key = config.APP_SECRET

@app.errorhandler(404)
def page_not_found(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(error):
	return render_template('500.html'), 500

@app.before_request
def before_request():
	g.is_active = is_active
	if session.has_key('u') and session.has_key('p'):
		if config.APP_USERS.has_key(session['u']) and config.APP_USERS[session['u']] == session['p']:
			g.user = session['u']
		else:
			g.user = None
	else:
		g.user = None
	
@app.after_request
def after_request(response):
	return response

def is_active(name):
	if request.endpoint and request.endpoint.startswith(name):
		return 'active'
	else:
		return ''

def require_login(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if g.user is None:
			return redirect(url_for('login', next=request.url))
		return f(*args, **kwargs)
	return decorated_function
