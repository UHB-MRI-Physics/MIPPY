from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
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

def flatten_series():
	"""
	If you require all images across multiple series as a single 1D list with
	no separation between series, then return True. Otherwise, return False
	to receive a 2D list separated by series.
	"""
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
	win.im1 = MIPPYCanvas(win,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='vertical')
	win.im1.configure_scrollbar()
	win.go_button = Button(win,text="Go!",command=lambda:run_analysis(win))
	win.im1.load_images(images)

	win.im1.grid(row=0,column=0)
	win.im1.img_scrollbar.grid(row=0,column=1)
	win.go_button.grid(row=1,column=0)

	return

def run_analysis(win):
	print "ANALYSIS!"
	return

def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return