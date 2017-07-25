# This is necessary until MIPPY is installed in Python site-packages
import sys
import os
sys.path.append(os.getcwd())



#~ from multiprocessing import freeze_support
from Tkinter import *
from ttk import *

#~ if sys.argv[1]=="debug":
	#~ pass # for now

if __name__=='__main__':
	#~ freeze_support()
        # Set up logfile in logs directory
        try:
                if sys.argv[1]=='debug':
                        debug=True
                else:
                        debug=False
        except:
                debug=False
        if not debug:
                from mippy import logging
                from datetime import datetime
                logpath=os.path.join(os.getcwd(),"MIPPY-logs",str(datetime.now()).replace(":",".").replace(" ","_")+".txt")
                # Add capture for stdout and stderr output for log file, and scrollable text box
                # self.master.logoutput = ScrolledText.ScrolledText(self.master,height=6)
                redir_out = logging.RedirectText(logpath)
                redir_err = logging.RedirectText(logpath)
                sys.stdout = redir_out
                sys.stderr = redir_err
        
	import mippy.splash as splash
	from pkg_resources import resource_filename
	splashimage = resource_filename('mippy','resources/splash3.jpg')
	root_window = Tk()
	with splash.SplashScreen(root_window,splashimage,3.0):
		from mippy.application import MIPPYMain
		root_app = MIPPYMain(master = root_window)
	root_app.mainloop()
