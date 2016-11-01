"""
ACR distortion assessment.
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
from scipy.signal import convolve

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
	
	"""
	This section creates you blank GUI and sets your window title and icon.
	"""
	win = Toplevel(master_window)
	win.title("ACR Distortion Assessment")
	if "nt" == os.name:
		win.wm_iconbitmap(bitmap = "source/images/brain_orange.ico")
	else:
		win.wm_iconbitmap('@'+os.path.join(root_path,'source','images','brain_bw.xbm'))
	gc.collect()
	"""
	"""	

	win.im1 = MIPPYCanvas(win,width=400,height=400,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROIs',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Uniformity',command=lambda:measure_distortion(win))
	win.outputbox = Text(win,state='disabled',height=10,width=80)

	win.phantom_options = [
		'ACR (TRA)',
		'MagNET Flood (TRA)']

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
	print "Center",center

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

	xdim = radius_x * 1.2	      # 10% more than anticipated diameter
	ydim = radius_y * 1.2       # 10% more than anticipated diameter

	if xdim>ydim:
		ydim=xdim
	elif ydim>xdim:
		xdim=ydim

	win.xdim = xdim
	win.ydim = ydim
	
	win.n_profiles = 8

	roi_ellipse_coords = get_ellipse_coords(center,xdim,ydim,win.n_profiles)
	print roi_ellipse_coords
#	win.im1.new_roi(roi_ellipse_coords,tags=['e'])

#	win.im1.roi_rectangle(xc-xdim,yc-5,xdim*2,10,tags=['h'],system='image')
#	win.im1.roi_rectangle(xc-5,yc-ydim,10,ydim*2,tags=['v'],system='image')
	for a in range(len(roi_ellipse_coords)/2):
		win.im1.new_roi([roi_ellipse_coords[a],roi_ellipse_coords[a+len(roi_ellipse_coords)/2]],system='image')

def measure_distortion(win):
	profiles = []
	px = []
	res = 0.1
	smoothing = 0.3
	for i in range(len(win.im1.roi_list)):
		this_prof, this_px = win.im1.get_profile(index=i,resolution=res,interpolate=True)
		profiles.append(convolve(np.array(this_prof),np.ones(smoothing/res),mode='same'))
		px.append(this_px)
	
	lows = []
	highs = []
	
	flat_px = win.im1.get_active_image().px_float.flatten()
	
	noise_threshold = 0.1*np.mean(flat_px)
	im_mean = np.mean(flat_px[np.where(flat_px>=noise_threshold)])
	im_max = np.max(flat_px)
	half_value = im_mean/2
	print noise_threshold,im_max,im_mean,half_value
	
	
	for profile in profiles:
		this_low = None
		this_high = None
		for i in range(len(profile)/2):
#			print i
			if (profile[i]>=half_value and
				profile[i-1]<half_value and
				profile[i+1]>=half_value and
				not this_low):
				this_low = px[0][i]
			if (profile[-i]>=half_value and
				profile[-i+1]<half_value and
				profile[-i-1]>=half_value and
				not this_high):
				this_high = px[0][-i]
			if this_low and this_high:
				break
		lows.append(this_low)
		highs.append(this_high)
	
	print lows
	print highs
	
	lengths = np.zeros(len(lows))
	for a in range(len(lows)):
		lengths[a] = (highs[a]-lows[a])*res
	
	xscale = win.im1.get_active_image().xscale
	yscale = win.im1.get_active_image().yscale
	linearity = (np.mean(lengths[1:])*np.mean([xscale,yscale]) - 190.)/190.
	distortion = np.std(lengths[1:])/np.mean(lengths[1:])
	print "Linearity", np.round(linearity*100,2), "%"
	print "Linearity (absolute)", np.round(linearity * 190.+190,2), "mm"
	print "Distortion", np.round(distortion*100,2), "%"





	clear_output(win)
#	output(win,'Measured across central 75% of phantom\n')
#
#	output(win,"Integral uniformity (ACR) = "+str(np.round(int_uniformity*100,1))+" %\n")
	output(win,"Linearity: "+str(np.round(linearity*100,2))+" %")
	output(win,"Linearity (Absolute): "+str(np.round(linearity * 190.+190,2))+" mm")
	output(win,"Distortion: "+str(np.round(distortion*100,2))+" %")
#
#	output(win,"Fractional uniformity (Horizontal) = "+str(np.round(h_uni*100,1))+" %")
#	output(win,"Fractional uniformity (Vertical) = "+str(np.round(v_uni*100,1))+" %")
#
#	output(win,'\nThe following can be copied and pasted directly into MS Excel or similar')
#	output(win,'\nX (mm)\tHorizontal\tY (mm)\tVertical')
#	for row in range(len(profile_h)):
#		output(win,str(x[row]*xscale)+'\t'+str(profile_h[row])+'\t'+str(y[row]*yscale)+'\t'+str(profile_v[row]))
##	win.im1.grid(row=0,column=0,sticky='nw')
#	win.outputbox.see('1.0')
#	win.update()