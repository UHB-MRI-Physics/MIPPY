#!/usr/bin/env python
import sys
from datetime import datetime
import os
from Tkinter import *


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


import source.splash as splash


root_window = Tk()
root_window.title("MIPPY: Modular Image Processing in Python")
root_window.minsize(650,400)
root_path = os.getcwd()
if "nt" == os.name:
	root_window.wm_iconbitmap(bitmap = "source/images/brain_orange.ico")
else:
	root_window.wm_iconbitmap('@'+os.path.join(root_path,'source','images','brain_bw.xbm'))
				
with splash.SplashScreen(root_window,'source/images/brain_orange.png', 3.0):
	from source.main import *

root_app = ToolboxHome(master = root_window)
root_app.mainloop()