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
from scipy.signal import convolve,convolve2d
from scipy.ndimage.measurements import center_of_mass
from scipy.optimize import curve_fit

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
	By default, MIPPY will pass the image datasets as a 2D list, divided by series.
	If you want only a single, flat list from all your series, return True.
	"""
	return True

def polynomial(x,A=0,B=0,C=0,Coff=0,D=0,Doff=0,E=0,Eoff=0,F=0,Foff=0):
	return A + B*(x) + C*((x+Coff)**2) + D*((x+Doff)**3) + E*((x+Eoff)**4) + F*((x+Foff)**5)


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
	win.roibutton = Button(win.toolbar,text='Initialise Grid',command=lambda:reset_grid(win))
	win.measurebutton = Button(win.toolbar,text='Measure Grid Distortion',command=lambda:measure_grid_distortion(win))
	win.profilebutton = Button(win.toolbar,text='Initialise Profiles',command=lambda:reset_profiles(win))
	win.measureprofbutton = Button(win.toolbar,text='Measure Profile Distortion',command=lambda:measure_profile_distortion(win))
	
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
	win.profilebutton.grid(row=6,column=0,sticky='ew')
	win.measureprofbutton.grid(row=7,column=0,sticky='ew')

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
	win.im1.show_image(5)

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

def reset_grid(win):
	win.im1.delete_rois()
	phantom=win.phantom_v.get()
	center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							subpixel=False,mode=win.mode.get())
	xc = center[0]
	yc = center[1]
	win.xc = xc
	win.yc = yc
	print "Center",center
	
	exp_gridsize = 15
	
	win.expected_positions = []
	grid_size_x = exp_gridsize/win.im1.get_active_image().xscale
	grid_size_y = exp_gridsize/win.im1.get_active_image().yscale
	
	for j in range(9):
		for i in range(9):
			if not ((i==0 and j==0) or (i==0 and j==8) or (i==8 and j==0) or (i==8 and j==8)):
				x_exp = (i-4)*grid_size_x+xc
				y_exp = (j-4)*grid_size_y+yc
				win.expected_positions.append((x_exp,y_exp))
	print "Finished calculating positions"
	
	for roi_pos in win.expected_positions:
		win.im1.roi_circle(roi_pos,2,resolution=3,system='image')

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
	

def measure_grid_distortion(win):
	actual_positions = list(win.expected_positions) # Use list() to create a new list rather than reference the existing one
	
	search = 5
	threshold = 0.05
	diff = threshold
	max_iter = 50
	n = 0
	
	kernel = np.array(((1,1,1),(1,1,1),(1,1,1))).astype(np.float64)/9
	px = convolve2d(np.array(win.im1.get_active_image().px_float),kernel,mode='same',boundary='fill',fillvalue=0)
	
	while diff>=threshold and n<max_iter:
		n = n+1
		current_positions = list(actual_positions)
		actual_positions = []
		
		for p in current_positions:
			CoM = center_of_mass(1/(px[p[1]-search:p[1]+search+1,p[0]-search:p[0]+search+1]+1))
			actual_positions.append((p[0]+CoM[1]-search,p[1]+CoM[0]-search))
		pos_old = np.array(current_positions)
		pos_new = np.array(actual_positions)
		diff = np.sum(abs(pos_new-pos_old))/len(actual_positions)
	print 'Iterations = '+str(n)
	
	for p in actual_positions:
		win.im1.roi_circle(p,2,resolution=3,system='image',color='magenta')
	
	# Convert initial and final positions to arrays
	actual_positions = np.array(actual_positions)
	initial_positions = np.array(win.expected_positions)
	
	# Find x and y differences in grid positions
	xdiff = actual_positions[:,0]-initial_positions[:,0]
	ydiff = actual_positions[:,1]-initial_positions[:,1]
	
	xco0=0
	xco1=0
	xco2=0
	xoff2=0
	yco0=0
	yco1=0
	yco2=0
	yoff2=0
	
	xspc = win.im1.get_active_image().xscale
	yspc = win.im1.get_active_image().yscale
	
	xdist_opt,xdist_cov = curve_fit(polynomial,initial_positions[:,0]-win.xc,xdiff,p0=[xco0,xco1,xco2,xoff2])
	ydist_opt,ydist_cov = curve_fit(polynomial,initial_positions[:,1]-win.yc,ydiff,p0=[yco0,yco1,yco2,yoff2])
	
	# Convert image coordinates to mm distances
	xdist_opt = xdist_opt*xspc
	ydist_opt = xdist_opt*yspc
	
	# First and second order (linear and non-linear) distortion in X and Y
	xdist_1st = xdist_opt[1]
	xdist_2nd = xdist_opt[2]
	ydist_1st = ydist_opt[1]
	ydist_2nd = ydist_opt[2]
	
	print 'X distortion (linear): {v:=.3f} mm/mm'.format(v=xdist_1st)
	print 'X distortion (non-linear): {v:=.3f} mm/mm2'.format(v=xdist_2nd)
	print 'Y distortion (linear): {v:=.3f} mm/mm'.format(v=ydist_1st)
	print 'Y distortion (non-linear): {v:=.3f} mm/mm2'.format(v=ydist_2nd)
	
	# Get linear distances from grid
	xdistances = []
	ydistances = []
	
	for i in range(7):
		x_x1 = actual_positions[i*9+7,0]
		x_x2 = actual_positions[i*9+15,0]
		x_y1 = actual_positions[i*9+7,1]
		x_y2 = actual_positions[i*9+15,1]
		x_r = np.sqrt((x_x2-x_x1)**2+(x_y2-x_y1)**2)
		
		y_x1 = actual_positions[i,0]
		y_x2 = actual_positions[i-7,0]
		y_y1 = actual_positions[i,1]
		y_y2 = actual_positions[i-7,1]
		y_r = np.sqrt((y_x2-y_x1)**2+(y_y2-y_y1)**2)
		
		#~ self.tabs.dist.im1.create_line(x_x1,x_y1,x_x2,x_y2,fill='green',tags='line')
		#~ self.tabs.dist.im1.create_line(y_x1,y_y1,y_x2,y_y2,fill='red',tags='line')
		
		xdistances.append(x_r)
		ydistances.append(y_r)
	
	xdistances = np.array(xdistances)
	ydistances = np.array(ydistances)
	
	lin_x = np.mean(xdistances)
	lin_y = np.mean(ydistances)
	cov_x = np.std(xdistances)/lin_x
	cov_y = np.std(ydistances)/lin_y
	
	print 'Linearity (X): {v:=.2f} mm'.format(v=lin_x*xspc)
	print 'Linearity (Y): {v:=.2f} mm'.format(v=lin_y*yspc)
	print 'CoV Distortion (X): {v:=.2f} %'.format(v=cov_x*100)
	print 'CoV Distortion (Y): {v:=.2f} %'.format(v=cov_y*100)
	
	clear_output(win)
	output(win,'Linearity (X): {v:=.2f} mm'.format(v=lin_x*xspc))
	output(win,'Linearity (Y): {v:=.2f} mm'.format(v=lin_y*yspc))
	output(win,'CoV Distortion (X): {v:=.2f} %'.format(v=cov_x*100))
	output(win,'CoV Distortion (Y): {v:=.2f} %'.format(v=cov_y*100))
	
	output(win,'\nX distances:')
	for value in xdistances:
		output(win,'{v:=.2f}'.format(v=value))
		
	output(win,'\nY distances:')
	for value in ydistances:
		output(win,'{v:=.2f}'.format(v=value))
	win.outputbox.see('1.0')





	#~ clear_output(win)
#~ #	output(win,'Measured across central 75% of phantom\n')
#~ #
#~ #	output(win,"Integral uniformity (ACR) = "+str(np.round(int_uniformity*100,1))+" %\n")
	#~ output(win,"Linearity: "+str(np.round(linearity*100,2))+" %")
	#~ output(win,"Linearity (Absolute): "+str(np.round(linearity * 190.+190,2))+" mm")
	#~ output(win,"Distortion: "+str(np.round(distortion*100,2))+" %")
#~ #
#~ #	output(win,"Fractional uniformity (Horizontal) = "+str(np.round(h_uni*100,1))+" %")
#~ #	output(win,"Fractional uniformity (Vertical) = "+str(np.round(v_uni*100,1))+" %")
#~ #
#~ #	output(win,'\nThe following can be copied and pasted directly into MS Excel or similar')
#~ #	output(win,'\nX (mm)\tHorizontal\tY (mm)\tVertical')
#~ #	for row in range(len(profile_h)):
#~ #		output(win,str(x[row]*xscale)+'\t'+str(profile_h[row])+'\t'+str(y[row]*yscale)+'\t'+str(profile_v[row]))
#~ ##	win.im1.grid(row=0,column=0,sticky='nw')
#~ #	win.outputbox.see('1.0')
#~ #	win.update()


def reset_profiles(win):
	win.im1.delete_rois()
	phantom=win.phantom_v.get()
	center = imp.find_phantom_center(win.im1.get_active_image(),phantom,
							subpixel=False,mode=win.mode.get())
	xc = center[0]
	yc = center[1]
	win.xc = xc
	win.yc = yc
	print "Center",center
	
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
	
	
def measure_profile_distortion(win):
	profiles = []
	px = []
	res = 0.1
	smoothing = 0.3
	for i in range(len(win.im1.roi_list)):
		# Temporary fix for now, skip circular ROIs
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
	
	
	# THIS NEEDS FIXING. Calculate coordinates of each end and scale properly, in case of non-square pixels
	xscale = win.im1.get_active_image().xscale
	yscale = win.im1.get_active_image().yscale
	print 'PROFILE LENGTHS:'
	print lengths[1:]*np.mean([xscale,yscale])
	print ''
	linearity = (np.mean(lengths[1:])*np.mean([xscale,yscale]) - 190.)/190.
	distortion = np.std(lengths[1:])/np.mean(lengths[1:])
	print "Linearity", np.round(linearity*100,2), "%"
	print "Linearity (absolute)", np.round(linearity * 190.+190,2), "mm"
	print "Distortion", np.round(distortion*100,2), "%"
	
	clear_output(win)
	output(win,'Linearity: {v:=.2f} %'.format(v=linearity*100))
	output(win,'Linearity (absolute): {v:=.2f} %'.format(v=np.mean(lengths[1:])*np.mean([xscale,yscale])))
	output(win,'Distortion (CoV): {v:=.2f} %'.format(v=distortion))
	
	output(win,'\nProfile Lengths')
	for value in lengths[1:]:
		output(win,'{v:=.2f}'.format(v=value*np.mean([xscale,yscale])))
	win.outputbox.see('1.0')