import sys
from datetime import datetime
import os


class RedirectText(object):
	def __init__(self, log):
		self.logfile = log
	def write(self, string):
		with open(self.logfile,'a') as f:
			f.write('\n'+string)

if not sys.argv[1]=='debug':
	logpath = os.path.join(os.getcwd(),"logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
	with open(logpath,'w') as logout:
		logout.write('LOG FILE\n')

	redir_out = RedirectText(logpath)
	redir_err = RedirectText(logpath)
	sys.stdout = redir_out
	sys.stderr = redir_err

import source.main