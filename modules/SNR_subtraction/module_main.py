from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import source.functions.image_processing as imp
import tkMessageBox
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
	# Check you have images from two different series
	if images[0].SeriesInstanceUID==images[-1].SeriesInstanceUID:
		tkMessageBox.showwarning("ERROR","Images from two separate series are required.\n\n"
								+"Please check your selection and reload the module.")
		return
	
	win = Toplevel(master_window)
	
	win.im1 = MIPPYCanvas(win,width=300,height=300,drawing_enabled=True)
	win.im2 = MIPPYCanvas(win,width=300,height=300,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im2.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.im2.configure_scrollbar()
	win.im1.grid(row=0,column=0,sticky='nsew')
	win.im2.grid(row=0,column=1,sticky='nsew')
	win.im1.img_scrollbar.grid(row=1,column=0,sticky='ew')
	win.im2.img_scrollbar.grid(row=1,column=1,sticky='ew')
	
	win.toolbar = Frame(win)
	win.roi_button = Button(win.toolbar,text="Create/reset ROIs",command=lambda:roi_reset(win),width=30)
	win.subtract_button = Button(win.toolbar,text="View subtraction image",command=lambda:view_subtraction(win))
	win.calc_button = Button(win.toolbar,text="Calculate SNR",command=lambda:snr_calc(win))
	win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	win.phantom = StringVar(win)
	win.phantom.set('ACR (TRA)')		# default value	
	win.phantom_choice = OptionMenu(win.toolbar,win.phantom,
							'ACR (TRA)','ACR (SAG)','ACR (COR)','MagNET Flood (TRA)',
							'MagNET Flood (SAG)', 'MagNET Flood (COR)')
	win.mode=StringVar()
	win.mode.set('valid')
	win.advanced_checkbox = Checkbutton(win.toolbar,text='Use advanced ROI positioning?',var=win.mode,
								onvalue='same',offvalue='valid')
	win.mode_label = Label(win.toolbar,text='N.B. Advanced positioning is much slower, but accounts for the phantom not being fully contained in the image.',
					wraplength=200,justify=LEFT)
	
	win.toolbar.grid(row=0,column=2,sticky='nsew')
	win.roi_button.grid(row=0,column=0,sticky='ew')
	win.subtract_button.grid(row=1,column=0,sticky='ew')
	win.calc_button.grid(row=2,column=0,sticky='ew')
	win.phantom_label.grid(row=3,column=0,sticky='w')
	win.phantom_choice.grid(row=4,column=0,sticky='ew')
	win.advanced_checkbox.grid(row=5,column=0,sticky='w')
	win.mode_label.grid(row=6,column=0,sticky='w')
	
	win.rowconfigure(0,weight=1)
	win.rowconfigure(1,weight=0)
	win.columnconfigure(0,weight=1)
	win.columnconfigure(1,weight=1)
	win.columnconfigure(2,weight=0)
	win.toolbar.rowconfigure(0,weight=0)
	win.toolbar.rowconfigure(1,weight=0)
	win.toolbar.rowconfigure(2,weight=0)
	win.toolbar.rowconfigure(3,weight=0)
	win.toolbar.rowconfigure(4,weight=0)
	win.toolbar.rowconfigure(5,weight=0)
	win.toolbar.rowconfigure(6,weight=0)
	win.toolbar.columnconfigure(0,weight=0)
	
	win.images_split = [[]]
	for image in images:
		matched=False
		series = image.SeriesInstanceUID
		for imlist in win.images_split:
			if len(imlist)==0:
				imlist.append(image)
				matched=True
				break
			if imlist[0].SeriesInstanceUID==series:
				imlist.append(image)
				matched=True
				break
		if not matched:
			win.images_split.append([image])
	win.im1.load_images(win.images_split[0])
	win.im2.load_images(win.images_split[1])
				
	
	return
	
def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def roi_reset(win):
	print "ROI reset"
	win.im1.delete_rois()
	center = imp.find_phantom_center(win.im1.get_active_image(),phantom=win.phantom.get(),
							subpixel=False,mode=win.mode.get())
	xc = center[0]
	yc = center[1]
	print xc, yc
	dim = 10
	# Add five ROI's
	win.im1.roi_rectangle(xc-dim,yc-5*dim,dim*2,dim*2,tags=['top'],system='image')
	win.im1.roi_rectangle(xc+dim*3,yc-dim,dim*2,dim*2,tags=['right'],system='image')
	win.im1.roi_rectangle(xc-dim,yc+dim*3,dim*2,dim*2,tags=['bottom'],system='image')
	win.im1.roi_rectangle(xc-5*dim,yc-dim,dim*2,dim*2,tags=['left'],system='image')
	win.im1.roi_rectangle(xc-dim,yc-dim,dim*2,dim*2,tags=['center'],system='image')
	return
	
def snr_calc(win):
	print "SNR calc"
	rois = win.im1.find_withtag('roi')
	if len(rois)==0:
		tkMessageBox.showerror("ERROR", "No ROI selected. Please create one or more"
							+" regions to analyse.")
		return
	px1 = win.im1.get_active_image().px_float
	sub_images = []
	im_number = win.im2.active
	for i in range(len(win.im2.images)):
		sub_images.append(win.im2.images[i].px_float-win.im1.images[i].px_float)
	win.im2.load_images(sub_images)
	win.im2.show_image(im_number)
	win.im2.roi_list = win.im1.roi_list
	snr_list = []
	for i in range(len(win.im1.roi_list)):
		sig = win.im1.get_roi_pixels([i])
		noi = win.im2.get_roi_pixels([i])
		snr_list.append(np.mean(sig)/np.std(noi,ddof=1)*np.sqrt(2))
	snr = np.mean(snr_list)
	tkMessageBox.showinfo("RESULT","SNR = "+str(np.round(snr,2)))
	win.im2.load_images(win.images_split[1])
	win.im2.show_image(im_number)
	return

def view_subtraction(win):
	print "View subtraction"
	px1 = win.im1.get_active_image().px_float
	px2 = win.im2.get_active_image().px_float
	sub = px1-px2
	quick_display(win,sub)
	return