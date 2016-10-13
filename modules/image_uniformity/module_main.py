from Tkinter import *
#from ttk import *
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
	win.roibutton = Button(win.toolbar,text='Create/Reset ROIs',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Uniformity',command=lambda:measure_uni(win))
	win.outputbox = Text(win,state='disabled',height=10,width=80)

	win.phantom_options = [
		'',
		'ACR (TRA)',
		'MagNET Flood (TRA)',
		'MagNET Flood (SAG)',
		'MagNET Flood (COR)']

	win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	win.phantom_v = StringVar(win)

	print win.phantom_v.get()
	win.phantom_v.set(win.phantom_options[1])
	win.phantom_choice = apply(OptionMenu,(win.toolbar,win.phantom_v)+tuple(win.phantom_options))
		# default value
	print win.phantom_v.get()
	win.mode=StringVar()
	win.mode.set('valid')
	win.advanced_checkbox = Checkbutton(win.toolbar,text='Use advanced ROI positioning?',var=win.mode,
								onvalue='same',offvalue='valid')
	win.mode_label = Label(win.toolbar,text='N.B. Advanced positioning is much slower, but accounts for the phantom not being fully contained in the image.',
					wraplength=200,justify=LEFT)

	win.phantom_label.grid(row=0,column=0,sticky='w')
	win.phantom_choice.grid(row=1,column=0,sticky='ew')
	win.advanced_checkbox.grid(row=2,column=0,sticky='w')
	win.mode_label.grid(row=3,column=0,sticky='w')

	win.roibutton.grid(row=4,column=0,sticky='ew')
	win.measurebutton.grid(row=5,column=0,sticky='ew')

	win.im1.grid(row=0,column=0,sticky='nw')
	win.toolbar.grid(row=0,column=1,sticky='new')
	win.outputbox.grid(row=1,column=0,columnspan=2,sticky='nsew')

	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=1)
	win.columnconfigure(0,weight=0)
	win.columnconfigure(1,weight=1)

	win.toolbar.columnconfigure(0,weight=1)

	win.im1.load_images(images)

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

def reset_roi(win):
	print win.phantom_v.get()
	center = imp.find_phantom_center(win.im1.get_active_image(),phantom=win.phantom.get(),
							subpixel=False,mode=win.mode.get())
	xc = center[0]
	yc = center[1]

	if (win.phantom_v.get()=='ACR (TRA)'
		or win.phantom_v.get()=='ACR (SAG)'
		or win.phantom_v.get()=='ACR (COR)'):
		win.phantom = imp.make_ACR()
	elif (win.phantom_v.get()=='MagNET Flood (TRA)'
		or win.phantom_v.get()=='MagNET Flood (SAG)'
		or win.phantom_v.get()=='MagNET Flood (COR)'):
		win.phantom = imp.make_MagNET_flood()

	if '(TRA)' in win.phantom_v.get():
		roi_r = 0.85*win.phantom._r
		roi_r_px_x = roi_r * win.im1.get_active_image().xscale
		roi_r_px_y = roi_r * win.im1.get_active_image().yscale

	return