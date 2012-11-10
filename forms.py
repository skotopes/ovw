from flaskext.wtf import Form, TextField, Required, BooleanField, PasswordField, HiddenField, SelectMultipleField, validators
import re

name_validators = [
	validators.Required(),
	validators.Regexp(r'[a-zA-Z0-9]{5,25}', re.IGNORECASE, "Require to be [a-zA-Z0-9]{5,25}")
]

class UserLoginForm(Form):
	name		= TextField('Name', name_validators)
	password	= PasswordField('Password', [ validators.Required() ])
	remember	= BooleanField('Remember for 1 month')
	next		= HiddenField('next', [ validators.Required() ], default="/")

class CertificateForm(Form):
	name		= TextField('Name', name_validators)
	server		= BooleanField('add server features')
