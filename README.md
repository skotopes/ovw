WTF
==================================

This is WEB CA management for openvpn

What it can do:
# act as Certificate Authority
# generate client or server certificates
# revoke certificates and sync revocation list with your openvpn server(s)

Wanna see how it works?
==================================

00) Installing dependences: pip install -r requirements.txt
01) Running web server: ./manage.py StartWeb
10) open in your browser http://127.0.0.1:5000/

Production deploy
==================================

00) Installing dependences: pip install -r requirements.txt
01) Set everything you need in config_local.py
10) Start FastCGI daemon: ./manage.py StartFCGI
11) Install nginx(or other fastcgi capable server) and use fcgi.sock for application upstream.
