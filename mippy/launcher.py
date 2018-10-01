from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
from subprocess import check_output, PIPE, call, Popen
import json
import sys

def launch_mippy():
        import mippy.splash as splash
        from pkg_resources import resource_filename
        splashimage = resource_filename('mippy','resources/splash3.jpg')
        root_window = Tk()
        with splash.SplashScreen(root_window,splashimage,3.0):
                # Check for new version of MIPPY on PyPI
                pip_output = check_output(['pip','list','--outdated','--format=json'])
                if 'mippy' in [row['name'] for row in json.loads(pip_output)]:
                        #~ print("Warning! Outdated version of MIPPY detected!")
                        update = messagebox.askyesno("Update available","An update for MIPPY is available from PyPI.  Would you like to install?")
                        if update:
                                #~ call('pip install mippy --upgrade',shell=True)
                                p = Popen(['pip','install','mippy','--upgrade','--no-cache-dir'],stdin=PIPE,stdout=PIPE,stderr=PIPE)
                                output,err = p.communicate()
                                rc = p.returncode
                                if len(err)>0:
                                        print(err.decode("utf-8"))
                                if rc==0:
                                        messagebox.showinfo("MIPPY Updated","Update successful! Please restart MIPPY.")
                                else:
                                        messagebox.showwarning("Oops","Something went wrong. Please restart MIPPY.")
                                sys.exit()
                
                from mippy.application import MIPPYMain
                root_app = MIPPYMain(master = root_window)
        root_app.mainloop()




if __name__=='__main__':
        launch_mippy()
        #~ from tkinter import *
        #~ from tkinter.ttk import *


        #~ import mippy.splash as splash
        #~ from pkg_resources import resource_filename
        #~ splashimage = resource_filename('mippy','resources/splash3.jpg')
        #~ root_window = Tk()
        #~ with splash.SplashScreen(root_window,splashimage,3.0):
                
                #~ # Check for new version of MIPPY on PyPI
                #~ p - Popen(['program','arg'],stdin=PIPE,stdout=PIPE,stderr=PIPE)
                #~ output,err = p.communicate(b'pip list --outdated')
                #~ rc = p.returncode
                #~ print(output)
                
                #~ from mippy.application import MIPPYMain
                #~ root_app = MIPPYMain(master = root_window)
        #~ root_app.mainloop()