from os import path

# Application
APP_SECRET		= '412eb10d76c1aaabae094cc3a0148ee875b84331d8e7f8ca70f7d94d9b44fbcf'
APP_USERS		= {
	'admin': 'qwe123qwe',
}

APP_DEBUG		= True
APP_KEYDIR		= 'keys'
APP_TMPDIR		= 'tmp'

APP_VPN_SERVERS	= [ '127.0.0.1' ]
APP_VPN_CRL		= "/etc/openvpn/crl.pem"

if path.isfile('config_local.py'):
	execfile('config_local.py')
