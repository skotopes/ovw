#!/usr/bin/env python

from optparse import OptionParser
from application import app
from os import environ

import config
import views

class Main(object):
	def __init__(self):
		self.parser = OptionParser("usage: %prog [options] arg")
		self.parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
		self.parser.add_option("-f", "--force", action="store_true", dest="force")
		(self.options, self.args) = self.parser.parse_args()
	
	def __call__(self):
		actions = []
		for i in Main.__dict__.keys():
			if i.startswith('action'):
				actions.append(i.lstrip('action'))

		if len(self.args) == 0:
			self.parser.error("No action specified\nAvaliabel actions: %s" % ' '.join(actions))

		if self.args[0] not in actions:
			self.parser.error("action %s not supported.\nuse one of that: %s" % (self.args[0], actions))
		else:
			getattr(self, 'action'+self.args[0])(*self.args[1:])
	
	def actionStartWeb(self):
		app.run()

	def actionStartFCGI(self):
		from flup.server.fcgi import WSGIServer
		from daemon import DaemonContext
		from lockfile import FileLock
		from os import getpid
		ctx = DaemonContext(
			working_directory='.',
			pidfile=FileLock('/tmp/wl-fcgi'),
		)
		ctx.stderr = open('error.log', 'w+')
		ctx.stdout = ctx.stderr
		with ctx:
			open('wl-fcgi.pid', 'w').write(str(getpid()))
			WSGIServer(app, bindAddress='fcgi.sock', umask=0000).run()

	def actionStopFCGI(self):
		from lockfile import FileLock
		from os import kill
		from time import sleep
		kill(int(open('wl-fcgi.pid', 'r').read()), 15)
		lock = FileLock('/tmp/wl-fcgi')
		countdown = 15
		while lock.is_locked() and countdown > 0:
			countdown -= 1
		if lock.is_locked():
			exit(1)
	
if __name__ == '__main__':
	Main()()
