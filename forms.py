from flask_wtf import Form
from wtforms import Form, TextField, BooleanField, PasswordField, HiddenField, SelectMultipleField, validators
import re

name_validators = [
	validators.Required(),
	validators.Regexp(r'[a-zA-Z0-9]{3,25}', re.IGNORECASE, "Require to be [a-zA-Z0-9]{3,25}")
]
password_validators = [
	validators.Regexp(r'[a-zA-Z0-9]{0,25}', re.IGNORECASE, "Require to be [a-zA-Z0-9]{3,25}"),
	validators.EqualTo('confirm', message='Passwords must match')
]
class UserLoginForm(Form):
	name		= TextField('Name', name_validators)
	password	= PasswordField('Password', [ validators.DataRequired() ])
	remember	= BooleanField('Remember for 1 month')
	next		= HiddenField('next', [ validators.DataRequired() ], default="/")

class CertificateForm(Form):
	name		= TextField('Name', name_validators)
	password	= PasswordField('Certificate Password (optional)', password_validators)
	confirm		= PasswordField('Password Confirmation', [])
