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
	win.configure_scrollbar()
	win.im1.grid(row=0,column=0,sticky='nsew')
	win.im1.img_scrollbar.grid(row=1,column=0,sticky='ew')

	win.toolbar = Frame(win)
	win.roi_button = Button(win.toolbar,text='Create/reset ROIs', command=lambda:roi_reset(win),width=30)
	win.profile_button = Button(win.toolbar,text='View Profiles',command=lambda:show_profiles(win),width=30)
	win.histogram_button = Button(win.toolbar,text='View Histogram',command=lambda:show_histogram(win),width=30)
	win.measure_button = Button(win.toolbar, text='Measure Uniformity', command=lambda:measure_uniformity(win),width=30)
	win.method_label = Label(win.toolbar,text='\nPhantom selection:')
	win.method = StringVar(win)
	win.method.set('ACR (TRA)')		# default value	
	win.method_choice = OptionMenu(win.toolbar,win.method,'ACR','MagNET')
	return
	
def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return
