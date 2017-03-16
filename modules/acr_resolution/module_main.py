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

def overlap(radius,length):
	length = float(length)
	halflength = length/2
	radius=float(radius)
	if halflength>=radius:
		return np.pi*(radius**2)/(length**2)
	# Or if length<radius...
	full_circle_area = np.pi*(radius**2)
	# From definite integral of quarter circle between 0 and "length"...
	reduced_area = 0.25*(radius**2)*(2*np.arcsin(halflength/radius)+np.sin(2*np.arcsin(halflength/radius)))
	diff = full_circle_area/4 - reduced_area
	reduced_area = 4*(reduced_area-diff)
	if reduced_area>(length**2):
		return 1
	else:
		return reduced_area/(length**2)


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

	win.im1 = MIPPYCanvas(win,width=408,height=408,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROI',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Resolution',command=lambda:measure_res(win))
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
					
	# Create extra canvas for viewing just the resolution insert
	win.im2 = MIPPYCanvas(win,width=408,height=144,drawing_enabled=True)
	# im2 scrollbar is created but never displayed
	win.im2.img_scrollbar = Scrollbar(win)

	win.phantom_label.grid(row=0,column=0,sticky='w')
	win.phantom_choice.grid(row=1,column=0,sticky='ew')
	win.advanced_checkbox.grid(row=2,column=0,sticky='w')
	win.mode_label.grid(row=3,column=0,sticky='w')

	win.roibutton.grid(row=4,column=0,sticky='ew')
	win.measurebutton.grid(row=5,column=0,sticky='ew')

	win.im1.grid(row=0,column=0,sticky='nw')
	win.im1.img_scrollbar.grid(row=1,column=0,sticky='ew')
	win.toolbar.grid(row=0,column=1,rowspan=3,sticky='new')
	win.im2.grid(row=2,column=0,sticky='nw')
	win.outputbox.grid(row=3,column=0,columnspan=2,sticky='nsew')

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
	win.phantom=phantom
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

	#~ xdim = radius_x*0.75
	#~ ydim = radius_y*0.75

	#~ if xdim<ydim:
		#~ ydim=xdim
	#~ elif ydim<xdim:
		#~ xdim=ydim

	#~ win.xdim = xdim
	#~ win.ydim = ydim

	#~ roi_ellipse_coords = win.im1.canvas_coords(get_ellipse_coords(center,xdim,ydim))
#~ #	print roi_ellipse_coords
	#~ win.im1.new_roi(roi_ellipse_coords,tags=['e'])
	
	
	xdim=34
	ydim=12
	
	win.roi_shape = (ydim*2,xdim*2)

	win.im1.roi_rectangle(xc+6-xdim,yc+39-ydim,xdim*2,ydim*2,tags=['res'],system='image')

def measure_res(win):


	px = np.array(win.im1.get_roi_pixels()[0]).reshape(win.roi_shape)
	
	win.im2.load_images([px])
	
	px1 = px[:,0:win.roi_shape[1]/3]
	px2 = px[:,win.roi_shape[1]/3:2*win.roi_shape[1]/3]
	px3 = px[:,2*win.roi_shape[1]/3:]

	# Determine "black" and "white" values for MTF calculation
	image = win.im1.get_active_image()
	px_whole = image.px_float
	
	xc = win.xc
	yc = win.yc
	phantom=win.phantom
	
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
	
	roi_top_c = (xc,yc-radius_y-17)
	roi_rt_c = (xc+radius_x+17,yc)
	roi_bot_c = (xc,yc+radius_y+17)
	roi_lt_c = (xc-radius_y-17,yc)
	roi_long = 45
	roi_short = 8
	
	win.im1.roi_ellipse(roi_top_c,roi_long,roi_short,tags=['top'],system='image')
	win.im1.roi_ellipse(roi_rt_c,roi_short,roi_long,tags=['rt'],system='image')
	win.im1.roi_ellipse(roi_bot_c,roi_long,roi_short,tags=['bot'],system='image')
	win.im1.roi_ellipse(roi_lt_c,roi_short,roi_long,tags=['lt'],system='image')
	
	stats = win.im1.get_roi_statistics(rois=range(1,5))
	means = stats['mean']
	stds = stats['std']
	areas = stats['area_px']
	print "areas",areas
	
	H = win.im1.get_active_image().rows
	W = win.im1.get_active_image().columns
	
	roi_outside = False
	replaced = []
	
	for i in range(4):
		coords = np.column_stack(win.im1.image_coords(win.im1.roi_list[i].coords))
		#~ if ((coords[0]<0).all() or (coords[0]>=W).all() or (coords[1]<0).all() or (coords[1]>=H).all()):
		if (areas[i]<0.3*areas[i-2]):
			roi_outside = True
			if i==0:
				means[i]=means[i-2]
				stds[i]=stds[i-2]
				replaced.append('  - TOP replaced by BOTTOM')
			elif i==1:
				means[i]=means[i-2]
				stds[i]=stds[i-2]
				replaced.append('  - RIGHT replaced by LEFT')
			elif i==2:
				means[i]=means[i-2]
				stds[i]=stds[i-2]
				replaced.append('  - BOTTOM replaced by TOP')
			elif i==3:
				means[i]=means[i-2]
				stds[i]=stds[i-2]
				replaced.append('  - LEFT replaced by RIGHT')
				
	black = np.min([means[0]+means[2],means[1]+means[3]])/2
	
	threshold = black*2
	full_white = np.mean(px_whole[np.where(px_whole>threshold)])
	# Correct white value for "hole" area as a fraction of pixel area
	# Compute overlapping area to get expected white value for each hole set
	area_overlap_1 = overlap((0.5*1.1),np.mean([image.xscale,image.yscale]))
	area_overlap_2 = overlap((0.5*1.0),np.mean([image.xscale,image.yscale]))
	area_overlap_3 = overlap((0.5*0.9),np.mean([image.xscale,image.yscale]))
	print area_overlap_1,area_overlap_2,area_overlap_3
	white1 = full_white*area_overlap_1
	white2 = full_white*area_overlap_2
	white3 = full_white*area_overlap_3
	print white1,white2,white3
	
	
	

	#~ clear_output(win)
	#~ output(win,'Measured across central 75% of phantom\n')

	#~ output(win,"Integral uniformity (ACR) = "+str(np.round(int_uniformity*100,1))+" %\n")

	#~ output(win,"Fractional uniformity (Horizontal) = "+str(np.round(h_uni*100,1))+" %")
	#~ output(win,"Fractional uniformity (Vertical) = "+str(np.round(v_uni*100,1))+" %")

	#~ output(win,'\nThe following can be copied and pasted directly into MS Excel or similar')
	#~ output(win,'\nX (mm)\tHorizontal\tY (mm)\tVertical')
	#~ for row in range(len(profile_h)):
		#~ output(win,str(x[row]*xscale)+'\t'+str(profile_h[row])+'\t'+str(y[row]*yscale)+'\t'+str(profile_v[row]))
#~ #	win.im1.grid(row=0,column=0,sticky='nw')
	#~ win.outputbox.see('1.0')
#~ #	win.update()