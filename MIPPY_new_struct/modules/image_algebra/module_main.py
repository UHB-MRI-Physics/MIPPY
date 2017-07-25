from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
import time
import datetime
import numpy as np
import numpy.matlib
from copy import deepcopy
from dicom.tag import Tag
from scipy.optimize import minimize

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
	print "Module loaded..."
	print "Received "+str(len(images))+" images."
	print os.getcwd()
	print dicomdir
	win = Toplevel(master = master_window)

	# Image Set Matrix Size
	win.rows=images[-1].Rows
	win.cols=images[-1].Columns

	slicepositions = []
	try:
		for im in images:
			slicepositions.append(str(im.PlanePositionSequence))
	except:
		for im in images:
			slicepositions.append(str(im.ImagePositionPatient))

	slicepositions = np.array(slicepositions)
	win.slcs = np.shape(np.unique(slicepositions))[0]
	win.dyns = len(images)/win.slcs
	print win.rows
	print win.cols
	print win.slcs
	print win.dyns

	try:
		if (images[0].ImagePositionPatient==images[1].ImagePositionPatient):
			resort_needed = True
		else:
			resort_needed = False
	except AttributeError:
		if (images[0].PlanePositionSequence==images[1].PlanePositionSequence):
			resort_needed = True
		else:
			resort_needed = False
	except IndexError:
		resort_needed = False

	if resort_needed:
		sorted_images = []
		for d in range(win.dyns):
			for s in range(win.slcs):
				sorted_images.append(images[s*win.dyns+d])
		images=sorted_images


	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=True)
	win.imcanvas_maps = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=True)

	win.imcanvas_orig.roi_mode='ellipse'
	win.imcanvas_maps.roi_mode='ellipse'

	# Create scroll bars
	csl_orig=StringVar()
	csl_orig.set(win.imcanvas_orig.active)
	csl_maps=StringVar()
	csl_maps.set(win.imcanvas_maps.active)
	cdyn_orig=StringVar()
	cdyn_orig.set("388")
	cdyn_maps=StringVar()
	cdyn_maps.set("4")
	win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
	win.imcanvas_maps.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
	win.csl_orig = Label(win.imcanvases,textvariable=win.imcanvas_orig.active_str,width=7)
	win.csl_maps = Label(win.imcanvases,textvariable=win.imcanvas_maps.active_str,width=7)
	win.cdyn_orig = Label(win.imcanvases,textvariable=cdyn_orig,width=3)
	win.cdyn_maps = Label(win.imcanvases,textvariable=cdyn_maps,width=3)

	# Window layout
	win.imcanvas_orig.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nwes')
	win.imcanvas_orig.img_scrollbar.grid(row=0,column=2,sticky='nsw')
	win.csl_orig.grid(row=1,column=2)
	win.imcanvas_maps.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
	win.imcanvas_maps.img_scrollbar.grid(row=0,column=5,sticky='nsw')
	win.csl_maps.grid(row=1,column=5)

	win.imcanvases.grid(row=0,column=0,sticky='nwes')

	# To resize the objects with the main window
	win.rowconfigure(0,weight=2)
	win.columnconfigure(0,weight=2)
	win.imcanvases.rowconfigure(0,weight=2)
	win.imcanvases.rowconfigure(1,weight=0)
	win.imcanvases.rowconfigure(2,weight=0)
	win.imcanvases.columnconfigure(0,weight=2)
	win.imcanvases.columnconfigure(1,weight=0)
	win.imcanvases.columnconfigure(2,weight=0)
	win.imcanvases.columnconfigure(3,weight=2)
	win.imcanvases.columnconfigure(4,weight=0)
	win.imcanvases.columnconfigure(5,weight=0)

	win.imcanvas_orig.load_images(images)

	# Create buttons
	win.buttons=Frame(win)

	win.b_info = Button(win.buttons, text="Command Info", command=lambda:info_popup(win))

	win.l_eq = Label(win.buttons, text="Type in Equation: ")
	win.eq_in = StringVar(win)
	win.eq_in.set('im[1] + im[2]')
	win.b_eq = Entry(win.buttons, textvariable=win.eq_in,width=20)

	win.b_eval_eq = Button(win.buttons, text="Evaluate Equation", command=lambda:eval_eq(win,images))

	win.b_info.grid(row=0,column=0,sticky='nw')
	win.l_eq.grid(row=1,column=0,sticky='nw')
	win.b_eq.grid(row=2,column=0,sticky='nw')
	win.b_eval_eq.grid(row=3,column=0,sticky='nw')

	win.buttons.grid(row=0,column=1,sticky='news')

	return

def update_imnumber(win):
	""" This function just reads the active image number and updates it on the screen. """
	win.update()
	return
	
def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def info_popup(win):
	info_win=Toplevel(master=win)
	info_win.infocanvases=Frame(win)
	info_win.infocanvas=MIPPYCanvas(info_win.infocanvases,bd=1)
	txt=("'im[#]' - use notation 'im' and a number represanting an image\n"+"'+', '-', '*', '/' - normal algebra\n"+"'**' - square\n"+"'sqrt' - square root\n"+"Image Range currently not working...")
	info_win.info=Label(info_win,text=txt)
	info_win.info.grid(row=0,column=0)
	return

def eval_eq(win,images):
	win.map=[]
	im=[]
	im.append([])
	for image in images:
		im.append(MIPPYImage(image).px_float)
	
	win.map=eval(win.eq_in.get())
	slcs=np.size(win.map)/(win.rows*win.cols)
	win.imcanvas_maps.load_images(np.reshape(win.map,(slcs,win.rows,win.cols)))
	return
