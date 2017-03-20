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
import time

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

	win.im1 = MIPPYCanvas(win,width=200,height=200,drawing_enabled=True)
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
	win.phantom_choice = OptionMenu(win.toolbar,win.phantom_v,win.phantom_options[0],*win.phantom_options)
	mpy.optionmenu_patch(win.phantom_choice,win.phantom_v)
	
	win.n_holes_options = ['3 hole method','4 hole method']
	win.n_holes = StringVar(win)
	win.n_holes_label = Label(win.toolbar,text='\nAnalysis method:\n(3 holes preferred for 1.1mm and 0.9mm, 4\nholes preferred for 1.0mm)')
	win.n_holes_choice = OptionMenu(win.toolbar,win.n_holes,win.n_holes_options[1],*win.n_holes_options)
	mpy.optionmenu_patch(win.n_holes_choice,win.n_holes)
	
	
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
	win.im2.antialias=False

	win.phantom_label.grid(row=0,column=0,sticky='w')
	win.phantom_choice.grid(row=1,column=0,sticky='ew')
	win.advanced_checkbox.grid(row=2,column=0,sticky='w')
	win.mode_label.grid(row=3,column=0,sticky='w')

	win.roibutton.grid(row=4,column=0,sticky='ew')
	
	win.n_holes_label.grid(row=5,column=0,sticky='sw')
	win.n_holes_choice.grid(row=6,column=0,sticky='new')
	
	win.measurebutton.grid(row=7,column=0,sticky='ew')

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
	
	win.radius_x = radius_x
	win.radius_y = radius_y
	
	
	xdim=34
	ydim=12
	
	win.roi_shape = (ydim*2,xdim*2)

	win.im1.roi_rectangle(xc+8-xdim,yc+39-ydim,xdim*2,ydim*2,tags=['res'],system='image')

def measure_res(win):


	px = np.array(win.im1.get_roi_pixels()[0]).reshape(win.roi_shape)
	px_H = np.shape(px)[0]
	px_W = np.shape(px)[1]
	
	win.im2.load_images([px])
	win.im2.update()
	
	px1 = px[:,0:win.roi_shape[1]/3]
	px2 = px[:,win.roi_shape[1]/3:2*win.roi_shape[1]/3]
	px3 = px[:,2*win.roi_shape[1]/3:]

	# Determine "black" and "white" values for MTF calculation
	image = win.im1.get_active_image()
	px_whole = image.px_float
	
	xc = win.xc
	yc = win.yc
	radius_x = win.radius_x
	radius_y = win.radius_y
	
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
	white11 = full_white*area_overlap_1
	white10 = full_white*area_overlap_2
	white09 = full_white*area_overlap_3
	print black,white11,white10,white09
	
	if win.n_holes.get()=='3 hole method':
		roi_len = 5
	elif win.n_holes.get()=='4 hole method':
		roi_len = 7
	else:
		print "Number of holes not decided properly - poorly coded!"
	fft_len=32
	
	profiles = []
	fft_results = []
	
	z = win.im2.zoom_factor
	
	# For each set of holes,
	for i in range(3):
		max_tail_hor = 0
		max_x_hor = 0
		max_y_hor = 0
		max_tail_ver = 0
		max_x_ver = 0
		max_y_ver = 0
		result_hor = 0
		result_ver = 0
		profile_temp_hor = []
		profile_temp_ver = []
		#cycle through hor profiles
		for y in range(px_H):
			for x in range(i*px_W/3,((i+1)*px_W)/3-roi_len):
				win.im2.delete('temp')
				profile = px[y,x:x+roi_len].flatten()
				win.im2.create_rectangle((x*z,y*z,(x+roi_len)*z,(y+1)*z),outline='yellow',tags='temp')
				win.im2.update()
				transform = np.fft.fft(profile,fft_len)
				
				if abs(transform[fft_len/2])>max_tail_hor and (0.5<profile[0]/profile[-1]<1.5 or 0.5<profile[-1]/profile[0]<1.5):
					max_tail_hor = abs(transform[fft_len/2])
					max_x_hor = x
					max_y_hor = y
					result_hor = abs(transform[fft_len/2])/abs(transform[0])
					profile_temp_hor = np.array(profile)
		win.im2.delete('temp')
		
		#cycle through ver profiles
		for y in range(px_H-roi_len):
			for x in range(i*px_W/3,((i+1)*px_W)/3):
				win.im2.delete('temp')
				profile = px[y:y+roi_len,x].flatten()
				win.im2.create_rectangle((x*z,y*z,(x+1)*z,(y+roi_len)*z),outline='yellow',tags='temp')
				win.im2.update()
				transform = np.fft.fft(profile,fft_len)
				
				if abs(transform[fft_len/2])>max_tail_ver and (0.5<profile[0]/profile[-1]<1.5 or 0.5<profile[-1]/profile[0]<1.5):
					max_tail_ver = abs(transform[fft_len/2])
					max_x_ver = x
					max_y_ver = y
					result_ver = abs(transform[fft_len/2])/abs(transform[0])
					profile_temp_ver = np.array(profile)
		win.im2.delete('temp')
		win.im2.create_rectangle((max_x_hor*z,max_y_hor*z,(max_x_hor+roi_len)*z,(max_y_hor+1)*z),outline='magenta',tags='final')
		win.im2.create_rectangle((max_x_ver*z,max_y_ver*z,(max_x_ver+1)*z,(max_y_ver+roi_len)*z),outline='magenta',tags='final')
		
		profiles.append(profile_temp_hor)
		profiles.append(profile_temp_ver)
		fft_results.append(result_hor)
		fft_results.append(result_ver)
		
	fft_array = np.array(fft_results)
	
	# MTF results from FFT
	mtf11_fft = np.mean(fft_array[0:2])*(np.pi/4)
	mtf10_fft = np.mean(fft_array[2:4])*(np.pi/4)
	mtf09_fft = np.mean(fft_array[4:6])*(np.pi/4)
	
	# MTF results from profiles and CTF
	contrast_11_h = abs((np.max(profiles[0])-np.min(profiles[0]))/(np.max(profiles[0])+np.min(profiles[0])))
	contrast_11_v = abs((np.max(profiles[1])-np.min(profiles[1]))/(np.max(profiles[1])+np.min(profiles[1])))
	contrast_10_h = abs((np.max(profiles[2])-np.min(profiles[2]))/(np.max(profiles[2])+np.min(profiles[2])))
	contrast_10_v = abs((np.max(profiles[3])-np.min(profiles[3]))/(np.max(profiles[3])+np.min(profiles[3])))
	contrast_09_h = abs((np.max(profiles[4])-np.min(profiles[4]))/(np.max(profiles[4])+np.min(profiles[4])))
	contrast_09_v = abs((np.max(profiles[5])-np.min(profiles[5]))/(np.max(profiles[5])+np.min(profiles[5])))
	
	contrast_11_ideal = (white11-black)/(white11+black)
	contrast_10_ideal = (white10-black)/(white10+black)
	contrast_09_ideal = (white09-black)/(white09+black)
	
	ctf_11_h = contrast_11_h/contrast_11_ideal
	ctf_11_v = contrast_11_v/contrast_11_ideal
	ctf_10_h = contrast_10_h/contrast_10_ideal
	ctf_10_v = contrast_10_v/contrast_10_ideal
	ctf_09_h = contrast_09_h/contrast_09_ideal
	ctf_09_v = contrast_09_v/contrast_09_ideal
	
	mtf11_ctf = np.mean([ctf_11_h,ctf_11_v])*np.pi/4
	mtf10_ctf = np.mean([ctf_10_h,ctf_10_v])*np.pi/4
	mtf09_ctf = np.mean([ctf_09_h,ctf_09_v])*np.pi/4
	
	print "FFT based results"
	print mtf11_fft,mtf10_fft,mtf09_fft
	print "CTF based results"
	print mtf11_ctf,mtf10_ctf,mtf09_ctf
	

	clear_output(win)
	output(win,'MTF measured using FFT of hole profiles')
	output(win,'1.1mm holes: {v:=.1f} %'.format(v=mtf11_fft*100))
	output(win,'1.0mm holes: {v:=.1f} %'.format(v=mtf10_fft*100))
	output(win,'0.9mm holes: {v:=.1f} %'.format(v=mtf09_fft*100))
	
	output(win,'\nMTF measured using CTF from max/min of hole profiles')
	output(win,'1.1mm holes: {v:=.1f} %'.format(v=mtf11_ctf*100))
	output(win,'1.0mm holes: {v:=.1f} %'.format(v=mtf10_ctf*100))
	output(win,'0.9mm holes: {v:=.1f} %'.format(v=mtf09_ctf*100))
	
	output(win,'\nWhite and black values corrected for hole size')
	output(win,'Black: {v:=.2f}'.format(v=black))
	output(win,'White (raw): {v:=.2f}'.format(v=full_white))
	output(win,'White (1.1mm): {v:=.2f}'.format(v=white11))
	output(win,'White (1.0mm): {v:=.2f}'.format(v=white10))
	output(win,'White (0.9mm): {v:=.2f}'.format(v=white09))
	
	output(win,'\nProfiles for MS Excel')
	output(win,'1.1 hor\t1.1 ver\t1.0 hor\t1.0 ver\t0.9 hor\t0.9 ver')
	for i in range(roi_len):
		output(win,'{a:=.2f}\t{b:=.2f}\t{c:=.2f}\t{d:=.2f}\t{e:=.2f}\t{f:=.2f}'.format(
			a=profiles[0][i],b=profiles[1][i],c=profiles[2][i],d=profiles[3][i],e=profiles[4][i],f=profiles[5][i]))
			
	win.outputbox.see('1.0')
	win.update()