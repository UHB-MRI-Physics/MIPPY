#!/usr/bin/env python
import sys
from datetime import datetime
import os


class RedirectText(object):
	def __init__(self, log):
		self.logfile = log
	def write(self, string):
		with open(self.logfile,'a') as f:
			f.write('\n'+string)
try:
	if sys.argv [1]=='debug':
		debug_mode=True
	else:
		debug_mode=False
except:
	debug_mode=False
if not debug_mode:
	logpath = os.path.join(os.getcwd(),"logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
	with open(logpath,'w') as logout:
		logout.write('LOG FILE\n')

	redir_out = RedirectText(logpath)
	redir_err = RedirectText(logpath)
	sys.stdout = redir_out
	sys.stderr = redir_err

import source.main