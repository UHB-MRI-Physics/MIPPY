from datetime import datetime

class RedirectText(object):
	def __init__(self, log):
		self.logfile = log
		self.write("LOG FILE: "+str(datetime.now()))
	def write(self, stringobj):
		with open(self.logfile,'a') as f:
			f.write(stringobj)