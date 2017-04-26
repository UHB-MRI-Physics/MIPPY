"""
ACR slice position assessment.
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

	win = Toplevel(master_window)
	gc.collect()

	win.im1 = MIPPYCanvas(win,width=400,height=400,drawing_enabled=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Create/Reset ROIs',command=lambda:reset_roi(win))
	win.measurebutton = Button(win.toolbar,text='Measure Slice Offset',command=lambda:measure_slicepos(win))
	win.outputbox = Text(win,state='disabled',height=10,width=80)
	win.imageflipper = ImageFlipper(win,win.im1)

	#~ win.phantom_options = [
		#~ 'ACR (TRA)']

	#~ win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	#~ win.phantom_v = StringVar(win)

#	print win.phantom_v.get()
#	win.phantom_v.set(win.phantom_options[1])
#	win.phantom_choice = apply(OptionMenu,(win.toolbar,win.phantom_v)+tuple(win.phantom_options))
	#~ win.phantom_choice = OptionMenu(win.toolbar,win.phantom_v,win.phantom_options[0],*win.phantom_options)
	#~ mpy.optionmenu_patch(win.phantom_choice,win.phantom_v)
		# default value
#	print win.phantom_v.get()
	#~ win.mode=StringVar()
	#~ win.mode.set('valid')
	#~ win.advanced_checkbox = Checkbutton(win.toolbar,text='Use advanced ROI positioning?',var=win.mode,
								#~ onvalue='same',offvalue='valid')
	#~ win.mode_label = Label(win.toolbar,text='N.B. Advanced positioning is much slower, but accounts for the phantom not being fully contained in the image.',
					#~ wraplength=200,justify=LEFT)

	#~ win.phantom_label.grid(row=0,column=0,sticky='w')
	#~ win.phantom_choice.grid(row=1,column=0,sticky='ew')
	#~ win.advanced_checkbox.grid(row=2,column=0,sticky='w')
	#~ win.mode_label.grid(row=3,column=0,sticky='w')

	win.roibutton.grid(row=4,column=0,sticky='ew')
	win.measurebutton.grid(row=5,column=0,sticky='ew')

	win.im1.grid(row=1,column=0,sticky='nw')
	win.imageflipper.grid(row=0,column=0,sticky='nsew')
	win.im1.img_scrollbar.grid(row=2,column=0,sticky='ew')
	win.toolbar.grid(row=1,column=1,rowspan=2,sticky='new')
	win.outputbox.grid(row=3,column=0,columnspan=2,sticky='nsew')

	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=0)
	win.rowconfigure(2,weight=0)
	win.rowconfigure(3,weight=1)
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
	
	image = win.im1.get_active_image()

	geometry = imp.find_phantom_geometry(image)
	center = (geometry[0],geometry[1])
	win.xc = xc = center[0]
	win.yc = yc = center[1]
	win.radius_x = radius_x = geometry[2]
	win.radius_y = radius_y = geometry[3]
	
	#~ center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							#~ subpixel=False,mode=win.mode.get())
	#~ xc = center[0]
	#~ yc = center[1]
	#~ win.xc = xc
	#~ win.yc = yc

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
		# Add other phantom dimensions here...

#	xdim = radius_x*0.75
#	ydim = radius_y*0.75
#
#	if xdim<ydim:
#		ydim=xdim
#	elif ydim<xdim:
#		xdim=ydim
#
#	win.xdim = xdim
#	win.ydim = ydim
#
#	roi_ellipse_coords = win.im1.canvas_coords(get_ellipse_coords(center,xdim,ydim))
##	print roi_ellipse_coords
#	win.im1.new_roi(roi_ellipse_coords,tags=['e'])
#
#	win.im1.roi_rectangle(xc-xdim,yc-5,xdim*2,10,tags=['h'],system='image')
#	win.im1.roi_rectangle(xc-5,yc-ydim,10,ydim*2,tags=['v'],system='image')

	xdim=2.
	ydim=25.
	
	win.im1.roi_rectangle(xc-6,yc-80,xdim,ydim,tags=['roi'],system='image')
	win.im1.roi_rectangle(xc+1,yc-80,xdim,ydim,tags=['roi'],system='image')

def measure_slicepos(win):
	res = 1./10.
	ends = 3
	profile_a, y_a = win.im1.get_profile(direction='vertical',index=0,resolution=res,interpolate=True)
	profile_b, y_b = win.im1.get_profile(direction='vertical',index=1,resolution=res,interpolate=True)
	profile_a = convolve(np.array(profile_a),np.array([1,1,1,1,1]),mode='same')
	profile_b = convolve(np.array(profile_b),np.array([1,1,1,1,1]),mode='same')
	
	print len(profile_a)
	print len(profile_b)
	
	high_a = np.mean(profile_a[-int(ends/res)-1:-1])
	high_b = np.mean(profile_b[-int(ends/res)-1:-1])
	low_a = np.mean(profile_a[0:int(ends/res)])
	low_b = np.mean(profile_b[0:int(ends/res)])
	threshold_a = low_a+0.5*(high_a-low_a)
	threshold_b = low_b+0.5*(high_b-low_b)
	
	print low_a,threshold_a,high_a
	print low_b,threshold_b,high_b
	
	point_a = None
	point_b = None
	
	for a in range(np.shape(profile_a)[0]):
#		print a
		if (profile_a[a] >= threshold_a and
			profile_a[a+1] >= threshold_a and
			profile_a[a-1] < threshold_a):
			point_a = y_a[a]
			break
	for b in range(np.shape(profile_b)[0]):
#		print b
		if (profile_b[b] >= threshold_b and
			profile_b[b+1] >= threshold_b and
			profile_b[b-1] < threshold_b):
			point_b = y_b[b]
			break
	
	diff = (point_b-point_a)*res
	yscale = win.im1.get_active_image().yscale
	slicepos_error = diff/2 * yscale
	





	clear_output(win)

	output(win,"Slice position error:\t\t{v:=.2f}\tmm".format(v=slicepos_error))

	output(win,'\nMS Excel Results Table')
	output(win,'\nY1 (mm)\tValue\tY2 (mm)\tValue')
	for row in range(0,len(profile_a),10):
		output(win,str(y_a[row]*res*yscale)+'\t'+str(profile_a[row])+'\t'+str(y_b[row]*res*yscale)+'\t'+str(profile_b[row]))
#	win.im1.grid(row=0,column=0,sticky='nw')
	win.outputbox.see('1.0')
#	win.update()
	txt = win.outputbox.get('1.0',END)
	from source.functions.file_functions import save_results
	num = win.im1.active
	save_results(txt,name='SLICE_POSITION_'+str(num).zfill(4))