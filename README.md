# WTF

WEB CA management for OpenVPN.

What it can do:

- act as Certificate Authority
- generate client or server certificates
- revoke certificates and sync revocation list with your openvpn server(s)

# Wanna see how it works?

- Installing dependences: pip install -r requirements.txt
- Running web server: ./manage.py StartWeb
- open in your browser http://127.0.0.1:5000/

# Production deploy

- Installing dependences: pip install -r requirements.txt
- Set everything you need in config_local.py
- Start FastCGI daemon: ./manage.py StartFCGI
- Install nginx(or other fastcgi capable server) and use fcgi.sock for application upstream.

# CRL Syncronization

Use ssh keys if you need it. Or disable it in your local configuration file.

# Example configuration for nginx

		server {
				listen			80;
				server_name		_;

				location / {
						fastcgi_pass	unix:/opt/ovw/fcgi.sock;
						fastcgi_param	REQUEST_METHOD	  $request_method;
						fastcgi_param	SCRIPT_NAME		  /;
						fastcgi_param	PATH_INFO		  $uri;
						fastcgi_param	QUERY_STRING	  $query_string;
						fastcgi_param	CONTENT_TYPE	  $content_type;
						fastcgi_param	CONTENT_LENGTH	  $content_length;
						fastcgi_param	SERVER_NAME		  $server_name;
						fastcgi_param	SERVER_PORT		  $server_port;
						fastcgi_param	SERVER_PROTOCOL	  $server_addr;
				}

				location /static {
						root /opt/ovw;
				}
		}
