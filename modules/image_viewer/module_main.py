from Tkinter import *
from ttk import *
#~ import tkMessageBox

def preload_dicom():
	"""
	This method is essential for the module to run. MIPPY needs to know whether
	the module wants preloaded DICOM datasets or just paths to the files.  Most
	modules will probably want preloaded DICOM datasets so that you don't have
	to worry about different manufacturers, enhanced vs non-enhanced etc.
	However, I imagine some people will prefer to work with the raw data files
	and open the datasets themselves?
	"""
	# If you want DICOM datasets pre-loaded, return True.
	# If you want paths to the files only, return False.
	# Note the capital letters on True and False.  These are important.
	return True


def execute(master_window,dicomdir,images):
	#~ window = Toplevel(master=master_window)
	#~ window.button1=Button(window,text="Press me!",command=lambda:close_window(window))
	
	#~ window.label1=Label(window,text=dicomdir)
	#~ window.label2=Label(window,text=images)
	#~ window.button1.grid(row=2,column=0,sticky='nsew')
	#~ window.label1.grid(row=0,column=0,sticky='nsew')
	#~ window.label2.grid(row=1,column=0,sticky='nsew')
	print "Module loaded..."
	print "Received "+str(len(images))+" image datasets."
	return
	
def close_window(active_frame):
	active_frame.destroy()