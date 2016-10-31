"""
ACR uniformity assessment.
Rob Flintham. Nov 2016
"""


from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import source.functions.image_processing as imp
import source.functions.misc_functions as mpy
import os
from PIL import Image,ImageTk
import gc
from scipy.signal import convolve2d

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
	gc.collect()

	win.im1 = MIPPYCanvas(win,width=400,height=400,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROIs',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Uniformity',command=lambda:measure_uni(win))
	win.outputbox = Text(win,state='disabled',height=10,width=80)

	win.phantom_options = [
		'ACR (TRA)',
		'MagNET Flood (TRA)',
		'MagNET Flood (SAG)',
		'MagNET Flood (COR)']

	win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	win.phantom_v = StringVar(win)

#	print win.phantom_v.get()
#	win.phantom_v.set(win.phantom_options[1])
#	win.phantom_choice = apply(OptionMenu,(win.toolbar,win.phantom_v)+tuple(win.phantom_options))
	win.phantom_choice = OptionMenu(win.toolbar,win.phantom_v,win.phantom_options[0],*win.phantom_options)
	mpy.optionmenu_patch(win.phantom_choice,win.phantom_v)
		# default value
#	print win.phantom_v.get()
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
	win.im1.img_scrollbar.grid(row=1,column=0,sticky='ew')
	win.toolbar.grid(row=0,column=1,rowspan=2,sticky='new')
	win.outputbox.grid(row=2,column=0,columnspan=2,sticky='nsew')

	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=0)
	win.rowconfigure(2,weight=1)
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

def clear_output(win):
	win.outputbox.config(state=NORMAL)
	win.outputbox.delete('1.0', END)
	win.outputbox.config(state=DISABLED)
	win.update()

def reset_roi(win):
	win.im1.delete_rois()
	phantom=win.phantom_v.get()
	center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							subpixel=False,mode=win.mode.get())
	xc = center[0]
	yc = center[1]
	win.xc = xc
	win.yc = yc

#	if (win.phantom_v.get()=='ACR (TRA)'
#		or win.phantom_v.get()=='ACR (SAG)'
#		or win.phantom_v.get()=='ACR (COR)'):
#		win.phantom = imp.make_ACR()
#	elif (win.phantom_v.get()=='MagNET Flood (TRA)'
#		or win.phantom_v.get()=='MagNET Flood (SAG)'
#		or win.phantom_v.get()=='MagNET Flood (COR)'):
#		win.phantom = imp.make_MagNET_flood()

#	if '(TRA)' in win.phantom_v.get():
#		roi_r = 0.85*win.phantom._r
#		roi_r_px_x = roi_r * win.im1.get_active_image().xscale
#		roi_r_px_y = roi_r * win.im1.get_active_image().yscale

	# Calculate phantom radius in pixels
	image = win.im1.get_active_image()
	if phantom=='ACR (TRA)':
		radius_x = 95./image.xscale
		radius_y = 95./image.yscale
	elif phantom=='ACR (SAG)':
		radius_x = 95./image.xscale
		radius_y = 79./image.yscale
	elif phantom=='ACR (COR)':
		radius_x = 95./image.xscale
		radius_y = 79./image.yscale
	elif phantom=='MagNET Flood (TRA)':
		radius_x = 95./image.xscale
		radius_y = 95./image.yscale
	elif phantom=='MagNET Flood (SAG)':
		radius_x = 95./image.xscale
		radius_y = 105./image.yscale
	elif phantom=='MagNET Flood (COR)':
		radius_x = 95./image.xscale
		radius_y = 105./image.yscale
		# Add other phantom dimensions here...

	xdim = radius_x*0.75
	ydim = radius_y*0.75

	if xdim<ydim:
		ydim=xdim
	elif ydim<xdim:
		xdim=ydim

	win.xdim = xdim
	win.ydim = ydim

	roi_ellipse_coords = win.im1.canvas_coords(get_ellipse_coords(center,xdim,ydim))
#	print roi_ellipse_coords
	win.im1.new_roi(roi_ellipse_coords,tags=['e'])

	win.im1.roi_rectangle(xc-xdim,yc-5,xdim*2,10,tags=['h'],system='image')
	win.im1.roi_rectangle(xc-5,yc-ydim,10,ydim*2,tags=['v'],system='image')

def measure_uni(win):
	profile_h, x = win.im1.get_profile(direction='horizontal',index=1)
	profile_v, y = win.im1.get_profile(direction='vertical',index=2)
	profile_h = np.array(profile_h)
	profile_v = np.array(profile_v)
	print profile_h
	print profile_v
	xc = win.xc
	yc = win.yc
	xdim = win.xdim
	ydim = win.ydim

	cross_x1 = win.im1.roi_list[2].coords[0][0]/win.im1.zoom_factor
	cross_y1 = win.im1.roi_list[1].coords[0][1]/win.im1.zoom_factor
	cross_x2 = win.im1.roi_list[2].coords[1][0]/win.im1.zoom_factor
	cross_y2 = win.im1.roi_list[1].coords[2][1]/win.im1.zoom_factor

	# FRACTIONAL UNIFORMITY
#	center_value = np.mean(win.im1.get_active_image().px_float[yc-5:yc+5,xc-5:xc+5])
	center_value = np.mean(win.im1.get_active_image().px_float[cross_y1:cross_y2,cross_x1:cross_x2])
	print center_value

	x_len = np.round(2.*xdim,0)
	y_len = np.round(2.*ydim,0)

	h_clipped = np.clip(profile_h,0.9*center_value,1.1*center_value)
	v_clipped = np.clip(profile_v,0.9*center_value,1.1*center_value)
	print "where",np.where(0.9*center_value<profile_h)
#	h_valid = float(len(np.where(np.where(0.9*center_value<profile_h)<1.1*center_value)))
#	v_valid = float(len(np.where(np.where(0.9*center_value<profile_v)<1.1*center_value)))
	h_valid = float(len(profile_h)-len(np.where(profile_h<0.9*center_value)[0])-len(np.where(profile_h>1.1*center_value)[0]))
	v_valid = float(len(profile_v)-len(np.where(profile_v<0.9*center_value)[0])-len(np.where(profile_v>1.1*center_value)[0]))
	print h_valid
	print v_valid

	h_uni = h_valid/x_len
	v_uni = v_valid/y_len

	xscale = win.im1.get_active_image().xscale
	yscale = win.im1.get_active_image().yscale

	# INTEGRAL UNIFORMITY
	convolve_radius = np.floor(np.sqrt(100/np.pi))	# Gives 100px circular area
	mask = np.zeros((int(convolve_radius),int(convolve_radius)))
	for j in range(np.shape(mask)[0]):
		for i in range(np.shape(mask)[1]):
			if i**2+j**2 < convolve_radius**2:
				mask[j][i] = 1

	px = np.copy(win.im1.get_active_image().px_float)
	px_smooth = convolve2d(px,mask,mode='same',boundary='fill',fillvalue=0)

	win.hiddencanvas = MIPPYCanvas(win,height=win.im1.height,width=win.im1.width)
	win.hiddencanvas.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.hiddencanvas.configure_scrollbar()
	win.hiddencanvas.load_images([px_smooth])
#	win.hiddencanvas.grid(row=0,column=0,sticky='nw')
#	win.update()
	win.hiddencanvas.roi_list = [win.im1.roi_list[0]]
	stats = win.hiddencanvas.get_roi_statistics()
	int_uniformity = 1. - (stats['max'][0]-stats['min'][0])/(stats['max'][0]+stats['min'][0])





	clear_output(win)
	output(win,'Measured across central 75% of phantom\n')

	output(win,"Integral uniformity (ACR) = "+str(np.round(int_uniformity*100,1))+" %\n")

	output(win,"Fractional uniformity (Horizontal) = "+str(np.round(h_uni*100,1))+" %")
	output(win,"Fractional uniformity (Vertical) = "+str(np.round(v_uni*100,1))+" %")

	output(win,'\nThe following can be copied and pasted directly into MS Excel or similar')
	output(win,'\nX (mm)\tHorizontal\tY (mm)\tVertical')
	for row in range(len(profile_h)):
		output(win,str(x[row]*xscale)+'\t'+str(profile_h[row])+'\t'+str(y[row]*yscale)+'\t'+str(profile_v[row]))
#	win.im1.grid(row=0,column=0,sticky='nw')
	win.outputbox.see('1.0')
#	win.update()