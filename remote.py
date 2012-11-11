from fabric.network import disconnect_all
from fabric.tasks import execute
from fabric import state

from fabric.contrib.files import *
from fabric.api import *

def sync_file(src, dst, hosts):
	if len(hosts) == 0:
		return True
	try:
		for i in state.output:
			state.output[i] = False
		state.env.abort_on_prompts = True
		state.output.aborts = True
		state.env.parallel = False
		state.env.user = "root"
		
		execute(_sync_file, src, dst, hosts=hosts)
	except:
		return False
	finally:
		disconnect_all()
	return True

def _sync_file(src,dst):
	put(src, dst)