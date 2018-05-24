from datetime import datetime
import os
from . import logging
from . import logging.handlers
import sys

class RedirectText(object):
        def __init__(self, log):
                self.logfile = log
                self.write("LOG FILE: "+str(datetime.now())+'\n')
        def write(self, stringobj):
                with open(self.logfile,'a') as f:
                        f.write(stringobj)

class StdOutCatcher(object):
        def __init__(self,logobject):
                self.log = logobject
        def write(self,s):
                self.log.info(s)

class StdErrCatcher(object):
        def __init__(self,logobject):
                self.log = logobject
        def write(self,s):
                self.log.exception(s)

def setup_logging():
        # Code for logging from https://www.loggly.com/ultimate-guide/python-logging-basics/
        # with addition of custom classes StdErrCatcher and StdOutCatcher
        starttime = str(datetime.now())
        logdir = os.path.join(os.getcwd(),"MIPPY-logs")
        try:
                os.makedirs(logdir)
        except:
                pass
        
        logpath=os.path.join(logdir,starttime.replace(":",".").replace(" ","_")+".txt")
        
        with open(logpath,'wb') as logfile:
                logfile.write("MIPPY LOG: "+starttime+'\n')
        
        handler = logging.handlers.WatchedFileHandler(
                os.environ.get("LOGFILE",logpath)
                )
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        logout = logging.getLogger()
        logout.setLevel(os.environ.get("LOGLEVEL","INFO"))
        logout.addHandler(handler)
        logout.info("Is this working?")
        
        sys.stderr = StdErrCatcher(logout)
        sys.stdout = StdOutCatcher(logout)
        
        logout.info("How about now?")
        return