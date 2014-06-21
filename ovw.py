from os import path
from flask import *

app = Flask(__name__)
app.config.from_object('config')

def is_active(name):
	if request.endpoint and request.endpoint.startswith(name):
		return 'active'
	else:
		return ''

app.jinja_env.globals['is_active'] = is_active

def asset(name):
	return path.join(app.config['ASSETS_DIR'], name)
