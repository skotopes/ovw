# WTF

WEB CA management for OpenVPN.

What it can do:

- act as Certificate Authority
- generate client or server certificates
- revoke certificates and sync revocation list with your openvpn server(s)

# Wanna see how it works?

- Installing dependences: pip install -r requirements.txt
- Running web server: ./manage.py runserver
- open in your browser http://127.0.0.1:5000/

# Production deploy

- Installing dependences: pip install -r requirements.txt
- Set everything you need in config_local.py
- Use your favorite app server. For example gunicorn.

# CRL Syncronization

Use ssh keys if you need it. Or disable it in your local configuration file.
