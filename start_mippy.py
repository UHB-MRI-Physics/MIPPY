# This is necessary until MIPPY is installed in Python site-packages
import sys
import os
sys.path.append(os.getcwd())

###########################################
# Use built in logging feature
# From https://www.loggly.com/ultimate-guide/python-logging-basics/

############################################


#~ from multiprocessing import freeze_support
from Tkinter import *
from ttk import *

#~ if sys.argv[1]=="debug":
	#~ pass # for now

if __name__=='__main__':
        #~ # Set up logfile in logs directory
        #~ debug=False
        #~ print sys.path
        #~ try:
                #~ print sys.argv[1]
                #~ if sys.argv[1]=='debug':
                        #~ debug=True
                #~ else:
                        #~ debug=False
        #~ except:
                #~ debug=False
        #~ if not debug:
                #~ from mippy.mlogging import setup_logging
		#~ setup_logging()
	
	
	
	
                #~ from datetime import datetime
                #~ logdir=os.path.join(os.getcwd(),"MIPPY-logs")
                #~ try:
                        #~ os.makedirs(logdir)
                #~ except WindowsError:
                        #~ pass
                #~ logpath=os.path.join(logdir,str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
                #~ # Add capture for stdout and stderr output for log file, and scrollable text box
                #~ # self.master.logoutput = ScrolledText.ScrolledText(self.master,height=6)
                #~ #with open(logpath,'w') as logfile:
                #~ redir_out = logging.RedirectText(logpath)
                #~ redir_err = logging.RedirectText(logpath)
                #~ sys.stdout = redir_out
                #~ sys.stderr = redir_err

	import mippy.splash as splash
	from pkg_resources import resource_filename
	splashimage = resource_filename('mippy','resources/splash3.jpg')
	root_window = Tk()
	with splash.SplashScreen(root_window,splashimage,3.0):
		from mippy.application import MIPPYMain
		root_app = MIPPYMain(master = root_window)
	root_app.mainloop()