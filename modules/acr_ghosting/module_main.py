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
	win.measurebutton = Button(win.toolbar,text='Measure Ghosting',command=lambda:measure_ghosting(win))
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

	win.imageflipper.grid(row=0,column=0,sticky='nsew')
	win.im1.grid(row=1,column=0,sticky='nw')
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
	win.im1.show_image(7)
	win.im1.set_window_level(20,10)

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
	#~ center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							#~ subpixel=False,mode=win.mode.get())
	
	#~ xc = center[0]
	#~ yc = center[1]
	#~ win.xc = xc
	#~ win.yc = yc
	
	image = win.im1.get_active_image()

	geometry = imp.find_phantom_geometry(image)
	center = (geometry[0],geometry[1])
	win.xc = xc = center[0]
	win.yc = yc = center[1]
	radius_x = geometry[2]
	radius_y = geometry[3]

	#~ # Calculate phantom radius in pixels
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
		#~ # Add other phantom dimensions here...

	roi_top_c = (xc,yc-radius_y-17)
	roi_top_w = 45
	roi_top_h = 8
	
	roi_rt_c = (xc+radius_x+17,yc)
	roi_rt_w = 8
	roi_rt_h = 45
	
	roi_bot_c = (xc,yc+radius_y+17)
	roi_bot_w = 45
	roi_bot_h = 8
	
	roi_lt_c = (xc-radius_y-17,yc)
	roi_lt_w = 8
	roi_lt_h = 45

	win.im1.roi_ellipse(roi_top_c,roi_top_w,roi_top_h,tags=['top'],system='image',color='red')
	win.im1.roi_ellipse(roi_rt_c,roi_rt_w,roi_rt_h,tags=['rt'],system='image',color='blue')
	win.im1.roi_ellipse(roi_bot_c,roi_bot_w,roi_bot_h,tags=['bot'],system='image',color='red')
	win.im1.roi_ellipse(roi_lt_c,roi_lt_w,roi_lt_h,tags=['lt'],system='image',color='blue')
	win.im1.roi_circle((xc,yc),65,tags=['center'],system='image',color='magenta')

def measure_ghosting(win):
	#~ means = []
	#~ stds = []
	#~ areas = []
	#~ for i in range(4):
		#~ stats = win.im1.get_roi_statistics(rois=[i])
		#~ means.append(stats['mean'][0])
		#~ stds.append(stats['std'][0])
		#~ areas.append(stats['area_px'][0])
	stats = win.im1.get_roi_statistics(rois=range(4))
	means = stats['mean']
	stds = stats['std']
	areas = stats['area_px']
	central = win.im1.get_roi_statistics(rois=[4])
	
	# ROIs created in order top,right,bottom,left
	
	# This is a fix for poor phantom positioning, when one or more of the regions is totally outside
	# the image.
	
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
	
	ghost = abs( ((means[0]+means[2])-(means[1]+means[3]))/(2*central['mean'][0]) )
	
	clear_output(win)

	output(win,"Percentage Ghost Intensity (ACR):\t\t\t\t{v:=.2f}\t%".format(v=ghost*100))
	
	output(win,'\nMS Excel Table:')
	output(win,'Region\tMean\tStdDev')
	output(win,'Top\t{m:=.2f}\t{s:=.2f}'.format(m=means[0],s=stds[0]))
	output(win,'Bottom\t{m:=.2f}\t{s:=.2f}'.format(m=means[2],s=stds[2]))
	output(win,'Left\t{m:=.2f}\t{s:=.2f}'.format(m=means[1],s=stds[1]))
	output(win,'Right\t{m:=.2f}\t{s:=.2f}'.format(m=means[3],s=stds[3]))
	output(win,'Central\t{m:=.2f}\t{s:=.2f}'.format(m=central['mean'][0],s=central['std'][0]))
	
	if roi_outside:
		output(win,'\nWARNING! ROIs more than 70% outside of the image\nhave been replaced by their opposite ROI\nfor the calculation:')
		for string in replaced:
			output(win,string)

	win.outputbox.see('1.0')
	
	txt = win.outputbox.get('1.0',END)
	from source.functions.file_functions import save_results
	save_results(txt,name='GHOSTING')