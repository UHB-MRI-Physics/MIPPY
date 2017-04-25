"""
ACR uniformity assessment.
Rob Flintham. Nov 2016

New version 20/4/2017
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

	win.im1 = MIPPYCanvas(win,width=340,height=340,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROI',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Resolution',command=lambda:measure_res(win))
	win.outputbox = Text(win,state='disabled',height=10,width=80)

	#~ win.phantom_options = [
		#~ 'ACR (TRA)',
		#~ 'MagNET Flood (TRA)',
		#~ 'MagNET Flood (SAG)',
		#~ 'MagNET Flood (COR)']

	#~ win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	#~ win.phantom_v = StringVar(win)
	#~ win.phantom_choice = OptionMenu(win.toolbar,win.phantom_v,win.phantom_options[0],*win.phantom_options)
	#~ mpy.optionmenu_patch(win.phantom_choice,win.phantom_v)
	
	#~ win.n_holes_options = ['3 hole method','4 hole method']
	#~ win.n_holes = StringVar(win)
	#~ win.n_holes_label = Label(win.toolbar,text='\nAnalysis method:\n(3 holes preferred for 1.1mm and 0.9mm, 4\nholes preferred for 1.0mm)')
	#~ win.n_holes_choice = OptionMenu(win.toolbar,win.n_holes,win.n_holes_options[1],*win.n_holes_options)
	#~ mpy.optionmenu_patch(win.n_holes_choice,win.n_holes)
	
	win.controlbox = ImageFlipper(win,win.im1)	
	
	#~ win.mode=StringVar()
	#~ win.mode.set('valid')
	#~ win.advanced_checkbox = Checkbutton(win.toolbar,text='Use advanced ROI positioning?',var=win.mode,
								#~ onvalue='same',offvalue='valid')
	#~ win.mode_label = Label(win.toolbar,text='N.B. Advanced positioning is much slower, but accounts for the phantom not being fully contained in the image.',
					#~ wraplength=200,justify=LEFT)
					
	# Create extra canvas for viewing just the resolution insert
	win.im2 = MIPPYCanvas(win,width=340,height=120,drawing_enabled=True)
	# im2 scrollbar is created but never displayed
	win.im2.img_scrollbar = Scrollbar(win)
	win.im2.antialias=False

	#~ win.phantom_label.grid(row=0,column=0,sticky='w')
	#~ win.phantom_choice.grid(row=1,column=0,sticky='ew')
	#~ win.advanced_checkbox.grid(row=2,column=0,sticky='w')
	#~ win.mode_label.grid(row=3,column=0,sticky='w')

	win.roibutton.grid(row=4,column=0,sticky='ew')
	
	#~ win.n_holes_label.grid(row=5,column=0,sticky='sw')
	#~ win.n_holes_choice.grid(row=6,column=0,sticky='new')
	
	win.measurebutton.grid(row=7,column=0,sticky='ew')

	win.im1.grid(row=1,column=0,sticky='nw')
	win.im1.img_scrollbar.grid(row=2,column=0,sticky='ew')
	win.toolbar.grid(row=1,column=1,rowspan=2,sticky='new')
	win.controlbox.grid(row=0,column=0,sticky='nsew')
	win.im2.grid(row=3,column=0,sticky='nw')
	win.outputbox.grid(row=4,column=0,columnspan=2,sticky='nsew')

	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=0)
	win.rowconfigure(2,weight=0)
	win.rowconfigure(3,weight=0)
	win.rowconfigure(4,weight=0)
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
	#~ phantom=win.phantom_v.get()
	#~ win.phantom=phantom
	#~ center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							#~ subpixel=False,mode=win.mode.get())
	#~ xc = center[0]
	#~ yc = center[1]
	#~ win.xc = xc
	#~ win.yc = yc

	#~ # Calculate phantom radius in pixels
	#~ image = win.im1.get_active_image()
	#~ if phantom=='ACR (TRA)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 95./image.yscale
	#~ elif phantom=='ACR (SAG)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 79./image.yscale
	#~ elif phantom=='ACR (COR)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 79./image.yscale
	#~ elif phantom=='MagNET Flood (TRA)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 95./image.yscale
	#~ elif phantom=='MagNET Flood (SAG)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 105./image.yscale
	#~ elif phantom=='MagNET Flood (COR)':
		#~ radius_x = 95./image.xscale
		#~ radius_y = 105./image.yscale
	
	#~ win.radius_x = radius_x
	#~ win.radius_y = radius_y
	
	image = win.im1.get_active_image()

	geometry = imp.find_phantom_geometry(image)
	center = (geometry[0],geometry[1])
	win.xc = xc = center[0]
	win.yc = yc = center[1]
	win.radius_x = radius_x = geometry[2]
	win.radius_y = radius_y = geometry[3]
	
	
	xdim=34
	ydim=12
	
	win.roi_shape = (ydim*2,xdim*2)

	win.im1.roi_rectangle(xc+8-xdim,yc+39-ydim,xdim*2,ydim*2,tags=['res'],system='image')

def measure_res(win):


	px = np.array(win.im1.get_roi_pixels(tags=['res'])[0]).reshape(win.roi_shape)
	px_H = np.shape(px)[0]
	px_W = np.shape(px)[1]
	
	win.im2.load_images([px])
	win.im2.update()
	
	px1 = px[:,0:win.roi_shape[1]/3]
	px2 = px[:,win.roi_shape[1]/3:2*win.roi_shape[1]/3]
	px3 = px[:,2*win.roi_shape[1]/3:]
	
	# Get threshold values to accept profiles
	# 31 holes, take 90% of top 31 values
	#~ px_threshold = [0,0,0]
	#~ px_threshold[0] = np.max(px1)*0.4
	#~ px_threshold[0] = 0.5*np.mean(np.sort(px1.flatten())[-1:-5:-1])
	#~ px_threshold[1] = np.max(px2)*0.4
	#~ px_threshold[1] = 0.5*np.mean(np.sort(px2.flatten())[-1:-5:-1])
	#~ px_threshold[2] = np.max(px3)*0.4
	#~ px_threshold[2] = 0.5*np.mean(np.sort(px3.flatten())[-1:-5:-1])

	# Determine "black" and "white" values for MTF calculation
	
	bbox = win.im1.roi_list[0].bbox
	win.im1.roi_rectangle(bbox[0],bbox[1]-70,75,15,tags=['white'],color='blue')
	win.im1.roi_rectangle(bbox[0]-18,bbox[1],15,15,tags=['black'],color='red')
	
	black = win.im1.get_roi_statistics(tags=['black'])['mean'][0]
	full_white = win.im1.get_roi_statistics(tags=['white'])['mean'][0]
	print "Black",black
	print "White",full_white
	
	
	# Correct white value for "hole" area as a fraction of pixel area
	# Compute overlapping area to get expected white value for each hole set
	image = win.im1.get_active_image()
	area_overlap = [None,None,None]
	area_overlap[0] = overlap((0.5*1.1),np.mean([image.xscale,image.yscale]))
	area_overlap[1] = overlap((0.5*1.0),np.mean([image.xscale,image.yscale]))
	area_overlap[2] = overlap((0.5*0.9),np.mean([image.xscale,image.yscale]))
	#~ print area_overlap_1,area_overlap_2,area_overlap_3
	adj_white = [None,None,None]
	adj_white[0] = full_white*area_overlap[0]
	adj_white[1] = full_white*area_overlap[1]
	adj_white[2] = full_white*area_overlap[2]
	#~ print black,white11,white10,white09
	
	#~ if win.n_holes.get()=='3 hole method':
		#~ roi_len = 5
	#~ elif win.n_holes.get()=='4 hole method':
		#~ roi_len = 7
	#~ else:
		#~ print "Number of holes not decided properly - poorly coded!"
	fft_len=8
	n_profiles = 4
	
	profiles = []
	fft_results = []
	
	z = win.im2.zoom_factor
	
	# Determine hole set to use - take closest hole size to image resolution
	xscale = win.im1.get_active_image().xscale
	yscale = win.im1.get_active_image().yscale
	
	if 0.85 <= xscale < 0.95:
		hor_set = 2
		hor_size=0.9
	elif 0.95 <= xscale < 1.05:
		hor_set = 1
		hor_size=1.0
	elif 1.05 <= xscale < 1.15:
		hor_set = 0
		hor_size=1.1
	if 0.85 <= yscale < 0.95:
		ver_set = 2
		ver_size=0.9
	elif 0.95 <= yscale < 1.05:
		ver_set = 1
		ver_size=1.0
	elif 1.05 <= yscale < 1.15:
		ver_set = 0
		ver_size=1.1
	
	# Find best n horizontal profiles
	roi_len = 7
	n_profiles = 4
	fft_len=32
	profiles_hor = []
	max_x_hor = []
	hole_sum_hor = []
	fft_tail_max_hor = 0
	fft_best_x_hor = 0
	fft_best_y_hor = 0
	fft_result_hor = 0
	fft_tail_max_ver = 0
	fft_best_x_ver = 0
	fft_best_y_ver = 0
	fft_result_ver = 0
	zoom = win.im2.zoom_factor
	for y in range(px_H):
		this_row_profile = np.zeros(roi_len)
		this_max_x = 0
		this_value = 0
		for x in range(hor_set*px_W/3,((hor_set+1)*px_W)/3-roi_len):
			win.im2.delete('temp')
			win.im2.create_rectangle(x*zoom,y*zoom,(x+roi_len)*zoom,(y+1)*zoom,outline='yellow',tags='temp')
			win.im2.update()
			profile = px[y,x:x+roi_len].flatten()
			test_value = np.mean(profile[::2])
			if test_value > this_value:
			#~ if np.sum(profile[::2]) > np.sum(this_row_profile[::2]):
				this_row_profile = profile
				this_max_x = x
				#~ this_value = np.sum(profile[::2])
				this_value = test_value
			transform = np.fft.fft(profile,fft_len)
			if abs(transform[fft_len/2])>fft_tail_max_hor:
				fft_tail_max_hor = abs(transform[fft_len/2])
				fft_best_x_hor = x
				fft_best_y_hor = y
				fft_result_hor = abs(transform[fft_len/2])/abs(transform[0])
		profiles_hor.append(this_row_profile)
		max_x_hor.append(this_max_x)
		hole_sum_hor.append(this_value)
	print hole_sum_hor
	y_values_hor = np.array(hole_sum_hor).argsort()[-n_profiles:][::-1]
	x_values_hor = np.array(max_x_hor)[y_values_hor]
	x_values_hor = x_values_hor[y_values_hor.argsort()]
	y_values_hor = np.sort(y_values_hor)
	print x_values_hor
	print y_values_hor
	win.im2.delete('temp')
	for i in range(n_profiles):
		win.im2.create_rectangle(x_values_hor[i]*zoom,y_values_hor[i]*zoom,(x_values_hor[i]+roi_len)*zoom,(y_values_hor[i]+1)*zoom,outline='cyan')
	
	best_contrast_hor = 0
	best_x_hor = None
	best_y_hor = None
	best_diff_hor=0
	#~ for i in range((n_profiles+1)/2):
	for i in range(n_profiles):
		profile = px[y_values_hor[i],x_values_hor[i]:x_values_hor[i]+roi_len]
		max = np.max(profile)
		min = np.min(profile)
		contrast = (max-min)/(max+min)
		#~ diff = np.sum(profile[::2])-np.sum(profile[1::2])
		#~ diff=max-min
		#~ if diff > best_diff_hor:
		if contrast > best_contrast_hor:
			best_contrast_hor = contrast
			best_x_hor = x_values_hor[i]
			best_y_hor = y_values_hor[i]
	
	# Find best n vertical profiles
	profiles_ver = []
	max_y_ver = []
	hole_sum_ver = []
	zoom = win.im2.zoom_factor
	for x in range(ver_set*px_W/3,((ver_set+1)*px_W)/3):
		this_col_profile = np.zeros(roi_len)
		this_max_y = 0
		this_value = 0
		for y in range(px_H-roi_len):
			win.im2.delete('temp')
			win.im2.create_rectangle(x*zoom,y*zoom,(x+1)*zoom,(y+roi_len)*zoom,outline='yellow',tags='temp')
			win.im2.update()
			profile = px[y:y+roi_len,x].flatten()
			test_value = np.mean(profile[::2])
			if test_value > this_value:
				this_col_profile = profile
				this_max_y = y
				#~ this_value = np.sum(profile[::2])
				this_value = test_value
			transform = np.fft.fft(profile,fft_len)
			if abs(transform[fft_len/2])>fft_tail_max_ver:
				fft_tail_max_ver = abs(transform[fft_len/2])
				fft_best_x_ver = x
				fft_best_y_ver = y
				fft_result_ver = abs(transform[fft_len/2])/abs(transform[0])
		profiles_ver.append(this_col_profile)
		max_y_ver.append(this_max_y)
		hole_sum_ver.append(this_value)
	print hole_sum_ver
	x_values_ver = np.array(hole_sum_ver).argsort()[-n_profiles:][::-1]
	y_values_ver = np.array(max_y_ver)[x_values_ver]
	y_values_ver = y_values_ver[x_values_ver.argsort()]
	x_values_ver = np.sort(x_values_ver)
	x_values_ver = x_values_ver+(ver_set*px_W/3)
	win.im2.delete('temp')
	for i in range(n_profiles):
		win.im2.create_rectangle(x_values_ver[i]*zoom,y_values_ver[i]*zoom,(x_values_ver[i]+1)*zoom,(y_values_ver[i]+roi_len)*zoom,outline='cyan')
	
	best_contrast_ver = 0
	best_diff_ver= 0
	best_x_ver = None
	best_y_ver = None
	#~ for i in range((n_profiles-1)/2,n_profiles):
	for i in range(n_profiles):
		profile = px[y_values_ver[i]:y_values_ver[i]+roi_len,x_values_ver[i]]
		max = np.max(profile)
		min = np.min(profile)
		contrast = (max-min)/(max+min)
		#~ diff = np.sum(profile[::2])-np.sum(profile[1::2])
		#~ diff=max-min
		#~ if diff > best_diff_ver:
		if contrast > best_contrast_ver:
			best_contrast_ver = contrast
			best_x_ver = x_values_ver[i]
			best_y_ver = y_values_ver[i]
	win.im2.create_rectangle(best_x_hor*zoom,best_y_hor*zoom,(best_x_hor+roi_len)*zoom,(best_y_hor+1)*zoom,outline='magenta')
	win.im2.create_rectangle(best_x_ver*zoom,best_y_ver*zoom,(best_x_ver+1)*zoom,(best_y_ver+roi_len)*zoom,outline='magenta')
	
	win.im2.create_rectangle(fft_best_x_hor*zoom,fft_best_y_hor*zoom,(fft_best_x_hor+roi_len)*zoom,(fft_best_y_hor+1)*zoom,outline='red')
	win.im2.create_rectangle(fft_best_x_ver*zoom,fft_best_y_ver*zoom,(fft_best_x_ver+1)*zoom,(fft_best_y_ver+roi_len)*zoom,outline='red')
	
	contrast_zero_hor = (adj_white[hor_set]-black)/(adj_white[hor_set]+black)
	contrast_zero_ver = (adj_white[ver_set]-black)/(adj_white[ver_set]+black)
	
	mtf_hor = best_contrast_hor/contrast_zero_hor * np.pi / 4.
	mtf_ver = best_contrast_ver/contrast_zero_ver * np.pi / 4.
	
	print mtf_hor,mtf_ver,np.mean([mtf_hor,mtf_ver])
	
	phase = win.im1.get_active_image().pe_direction
	
	clear_output(win)
	output(win,'Estimated MTF using max CTF (magenta profiles)')
	output(win,'Mean:\t{v:=.1f}\t%'.format(v=np.mean([mtf_hor,mtf_ver])*100))
	output(win,'\nDirection\tPixel Size (mm)\tHole size (mm)\tMTF (%)')
	if phase=='ROW':
		output(win,'Phase\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=xscale,h=hor_size,m=mtf_hor*100))
		output(win,'Frequency\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=yscale,h=ver_size,m=mtf_ver*100))
	elif phase=='COL':
		output(win,'Phase\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=yscale,h=ver_size,m=mtf_ver*100))
		output(win,'Frequency\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=xscale,h=hor_size,m=mtf_hor*100))
	
	output(win,'\nEstimated MTF using FFT of profiles (red profiles)')
	output(win,'Mean:\t{v:=.1f}\t%'.format(v=np.mean([fft_result_hor,fft_result_ver])*100))
	output(win,'\nDirection\tPixel Size (mm)\tHole size (mm)\tMTF (%)')
	if phase=='ROW':
		output(win,'Phase\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=xscale,h=hor_size,m=fft_result_hor*100))
		output(win,'Frequency\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=yscale,h=ver_size,m=fft_result_ver*100))
	elif phase=='COL':
		output(win,'Phase\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=yscale,h=ver_size,m=fft_result_ver*100))
		output(win,'Frequency\t{p:=.3f}\t{h:=.1f}\t{m:=.1f}'.format(p=xscale,h=hor_size,m=fft_result_hor*100))
	
	output(win,'\nPhase encode direction:\t'+phase)
	
	# Output 4 profiles from each direction
	best_ver_profiles = []
	best_hor_profiles = []
	for i in range(n_profiles):
		best_ver_profiles.append(px[y_values_ver[i]:y_values_ver[i]+roi_len,x_values_ver[i]])
		best_hor_profiles.append(px[y_values_hor[i],x_values_hor[i]:x_values_hor[i]+roi_len])
	output(win,'\nProfiles:')
	output(win,'Pixel\tHor 1\tHor 2\tHor 3\tHor 4\tVer 1\tVer 2\tVer 3\tVer 4')
	for i in range(roi_len):
		output(win,'{p:=.0f}\t{h1:=.2f}\t{h2:=.2f}\t{h3:=.2f}\t{h4:=.2f}\t{v1:=.2f}\t{v2:=.2f}\t{v3:=.2f}\t{v4:=.2f}'.format(
				p=i,
				h1=best_hor_profiles[0][i],
				h2=best_hor_profiles[1][i],
				h3=best_hor_profiles[2][i],
				h4=best_hor_profiles[3][i],
				v1=best_ver_profiles[0][i],
				v2=best_ver_profiles[1][i],
				v3=best_ver_profiles[2][i],
				v4=best_ver_profiles[3][i]))
				
	output(win,'\nBlack\tWhite (Hor)\tWhite(Ver)')
	output(win,'{b:=.2f}\t{wh:=.2f}\t{wv:=.2f}'.format(b=black,wh=adj_white[hor_set],wv=adj_white[ver_set]))
	output(win,'N.B. White values adjusted for hole size')
	
	win.outputbox.see('1.0')
	
	win.update()
	
	txt = win.outputbox.get('1.0',END)
	from source.functions.file_functions import save_results
	save_results(txt,name='RESOLUTION')