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
	import mippy.splash as splash
	from pkg_resources import resource_filename
	splashimage = resource_filename('mippy','resources/splash.jpg')
	root_window = Tk()
	with splash.SplashScreen(root_window,splashimage,2.0):
		from mippy.application import MIPPYMain
		root_app = MIPPYMain(master = root_window)
	root_app.mainloop()