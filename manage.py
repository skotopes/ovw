#!/usr/bin/env python

from flask.ext.script import Manager, Server, Shell
from ovw import app

import config
import views

manager = Manager(app)

if __name__ == "__main__":
	manager.run()