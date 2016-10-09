from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import source.functions.image_processing as imp
import os
from PIL import Image,ImageTk

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
	"""
	This is the function that will run when you run the program. If you create a GUI
	window, use "master_window" as its master.  "dicomdir" is the dicom directory
	that has been loaded, and may or may not be where you want to save any
	result images.  "images" is a list containing your image datasets.  If you have
	set the "preload_dicom" message above to "return True", these will be dicom
	datasets.  If you set "return False", these will just be paths to the image files.
	"""

	win = Toplevel(master_window)

	win.im1 = MIPPYCanvas(win,width=300,height=300,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROIs',command=lambda:self.reset_roi())
	win.measurebutton = Button(win.toolbar,text='Measure Uniformity',command=lambda:self.measure_uni())
	win.outputbox = Text(win,state='disabled',height=10,width=80)
	
	win.roibutton.grid(row=0,column=0,sticky='ew')
	win.measurebutton.grid(row=1,column=0,sticky='ew')
	
	win.im1.grid(row=0,column=0,sticky='nw')
	win.toolbar.grid(row=0,column=1,sticky='new')
	win.outputbox.grid(row=1,column=0,columnspan=2,sticky='nsew')
	
	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=1)
	win.columnconfigure(0,weight=0)
	win.columnconfigure(1,weight=1)
	
	win.toolbar.columnconfigure(0,weight=1)
	
	return
	
def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def output(win,txt):
	win.outputbox.config(state=NORMAL)
	win.outputbox.insert(END,txt+'\n')
	win.outputbox.config(state=DISABLED)
	win.outputbox.see(END)
	win.update()
	return