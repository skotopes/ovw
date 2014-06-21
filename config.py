from os import path

# Application secret key for session encryption
SECRET_KEY		= '412eb10d76c1aaabae094cc3a0148ee875b84331d8e7f8ca70f7d94d9b44fbcf'
# Disable debug to enable session store encryption
DEBUG			= True
# Passwords should be hashed by sha256
# Use echo -n 'newpass' | shasum -a 256 # on mac os
# Use echo -n 'newpass' | sha256sum # on linux
USERS			= {
	'admin': '78154df5f5e4241b03b5dd352a62286aedb397be10f1c66961ed13cb336e4229', # qwe123qwe
}

# environment for key generation, use only strings
KEY_ENV	= {
	"KEY_SIZE"				: "1024",
	"KEY_DAYS"				: "3650",
	"KEY_COUNTRY"			: "US",
	"KEY_PROVINCE"			: "CA",
	"KEY_CITY"				: "SanFrancisco",
	"KEY_ORG"				: "Fort-Funston",
	"KEY_EMAIL"				: "me@myhost.mydomain",
	"KEY_OU"				: "openvpn",
	"PKCS11_MODULE_PATH"	: "dummy",
	"PKCS11_PIN"			: "dummy"
}
# directory where CA will store database and keys
ASSETS_DIR		= 'assets'
KEY_DIR			= 'keys'
TMP_DIR			= 'tmp'
# vpn server host where we want to sync crl. Use empty list to disable sync
VPN_SERVERS	= [ '127.0.0.1' ]
# username for connection
VPN_SERVERS_USER = 'openvpn'
# path where crl should be placed
VPN_CRL		= "/etc/openvpn/crl.pem"
# this host will be shown in client openvpn.conf
VPN_TMPL_SERVERS = [ 'vpn.mycompany.com' ]

# your configuration can override some part of mine ;-)
if path.isfile('config_local.py'):
	execfile('config_local.py')
