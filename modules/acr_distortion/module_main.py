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

def order2_2d(xy,P0,P1,P2,R0,R1,R2,off1,off2):
	return P0+P1*(xy[0]-off1)+P2*((xy[0]-off1)**2) + R0+R1*(xy[1]-off2)+R2*((xy[1]-off2)**2)


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
		win.wm_iconbitmap('@'+os.path.join(master_window.root_dir,'source','images','brain_bw.xbm'))
	gc.collect()
	"""
	"""
	
	win.screenwidth = win.winfo_screenwidth()
	win.screenheight = win.winfo_screenheight()
	print win.screenwidth
	print win.screenheight
	
	if win.screenheight < 800 or win.screenwidth < 1200:
		imwidth=300
		imheight=300

	win.im1 = MIPPYCanvas(win,width=imwidth,height=imheight,drawing_enabled=True,antialias=True)
	win.im1.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.im1.configure_scrollbar()
	win.toolbar = Frame(win)
	win.roibutton = Button(win.toolbar,text='Find central grid point',command=lambda:reset_grid(win))
	win.measurebutton = Button(win.toolbar,text='Measure Distortion',command=lambda:measure_distortion(win))
	#~ win.profilebutton = Button(win.toolbar,text='Initialise Profiles',command=lambda:reset_profiles(win))
	#~ win.measureprofbutton = Button(win.toolbar,text='Measure Profile Distortion',command=lambda:measure_profile_distortion(win))
	win.controlbox = ImageFlipper(win,win.im1)
	
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
	#~ win.profilebutton.grid(row=6,column=0,sticky='ew')
	#~ win.measureprofbutton.grid(row=7,column=0,sticky='ew')
	
	win.controlbox.grid(row=0,column=0,sticky='nsew')
	win.im1.grid(row=1,column=0,sticky='nw')
	win.im1.img_scrollbar.grid(row=2,column=0,sticky='ew')
	win.toolbar.grid(row=0,column=1,rowspan=3,sticky='new')
	win.outputbox.grid(row=3,column=0,columnspan=2,sticky='nsew')

	win.rowconfigure(0,weight=0)
	win.rowconfigure(1,weight=0)
	win.rowconfigure(2,weight=0)
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

	win.im1.roi_circle((xc,yc),4,resolution=4,system='image',tags=['center'])

def measure_distortion(win):
	# Get new center position from ROI
	output(win,'Calculating expected grid point locations...')
	coords = win.im1.roi_list[0].coords
	center = win.im1.image_coords([( coords[0][0] , (coords[len(coords)/2][1]-coords[0][1])/2+coords[0][1])])[0]
	win.xc = center[0]
	win.yc = center[1]
	xc = win.xc
	yc = win.yc
	
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
	print "Finished calculating initial positions"
	
	output(win,'Detecting actual grid point locations...')
	actual_positions = list(win.expected_positions) # Use list() to create a new list rather than reference the existing one
	
	search = 4
	threshold = 0.08
	diff = threshold
	max_iter = 200
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
		diff = np.sum(abs(pos_new-pos_old))/(len(actual_positions)*2)
		print 'diff',diff
	print 'Iterations = '+str(n)
	print 'Diff = '+str(diff)
	
	win.im1.roi_list.remove(win.im1.roi_list[0])
	win.im1.delete('center')
	
	output(win,'Drawing grid points')
	for p in actual_positions:
		#~ win.im1.roi_circle(p,2,resolution=3,system='image',color='magenta')
		win.im1.new_roi([(p[0]-3,p[1]-3),(p[0]+3,p[1]+3)],system='image',color='cyan')
		win.im1.new_roi([(p[0]-3,p[1]+3),(p[0]+3,p[1]-3)],system='image',color='cyan')
		win.update()
	output(win,'Calculating grid distortion...')
	# Convert initial and final positions to arrays
	actual_positions = np.array(actual_positions)
	initial_positions = np.array(win.expected_positions)
	
	# Find x and y differences in grid positions
	xdiff = actual_positions[:,0]-initial_positions[:,0]
	ydiff = actual_positions[:,1]-initial_positions[:,1]
	
	gridpoints = len(actual_positions)
	
	win.xc = actual_positions[(gridpoints-1)/2,0]
	win.yc = actual_positions[(gridpoints-1)/2,1]
	
	xco0=0
	xco1=0
	xco2=0
	xoff=win.xc
	yco0=0
	yco1=0
	yco2=0
	yoff=win.yc
	
	xspc = win.im1.get_active_image().xscale
	yspc = win.im1.get_active_image().yscale
	
	xdistances = []
	ydistances = []
	
	for i in range(7):
		x_x1 = actual_positions[i*9+7,0]
		x_x2 = actual_positions[i*9+15,0]
		x_y1 = actual_positions[i*9+7,1]
		x_y2 = actual_positions[i*9+15,1]
		x_r = np.sqrt((x_x2-x_x1)**2+(x_y2-x_y1)**2)
		win.im1.new_roi([(x_x1,x_y1),(x_x2,x_y2)],tags=['gridlines'],color='magenta',system='image')
		
		y_x1 = actual_positions[i,0]
		y_x2 = actual_positions[i-7,0]
		y_y1 = actual_positions[i,1]
		y_y2 = actual_positions[i-7,1]
		y_r = np.sqrt((y_x2-y_x1)**2+(y_y2-y_y1)**2)
		win.im1.new_roi([(y_x1,y_y1),(y_x2,y_y2)],tags=['gridlines'],color='magenta',system='image')
		
		#~ self.tabs.dist.im1.create_line(x_x1,x_y1,x_x2,x_y2,fill='green',tags='line')
		#~ self.tabs.dist.im1.create_line(y_x1,y_y1,y_x2,y_y2,fill='red',tags='line')
		
		xdistances.append(x_r)
		ydistances.append(y_r)
	
	xdistances = np.array(xdistances)*xspc
	ydistances = np.array(ydistances)*yspc
	
	lin_x_grid = np.mean(xdistances)
	lin_y_grid = np.mean(ydistances)
	cov_x_grid = np.std(xdistances)/lin_x_grid
	cov_y_grid = np.std(ydistances)/lin_y_grid
	
	
	

	output(win,"Generating radial profile positions...")
	#~ win.im1.delete_rois()
	phantom=win.phantom_v.get()
	xc = win.xc
	yc = win.yc
	center = (xc,yc)
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
	
	# Measure radial distortions
	profiles = []
	px = []
	res = 0.1
	smoothing = 1
	output(win,"Collecting and smoothing profiles...")
	for i in range(len(win.im1.roi_list)-8,len(win.im1.roi_list)):
		# Temporary fix for now, skip circular ROIs
		this_prof, this_px = win.im1.get_profile(index=i,resolution=res,interpolate=True)
		profiles.append(convolve(np.array(this_prof),np.ones(smoothing/res),mode='same'))
		px.append(this_px)
		print "profile",len(this_px)

	lows = []
	highs = []

	flat_px = win.im1.get_active_image().px_float.flatten()

	noise_threshold = 0.1*np.mean(flat_px)
	im_mean = np.mean(flat_px[np.where(flat_px>=noise_threshold)])
	im_max = np.max(flat_px)
	half_value = im_mean/2
	print noise_threshold,im_max,im_mean,half_value

	output(win,'Measuring phantom dimensions...')
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
	lengths = lengths * np.mean([xscale,yscale])
	
	lin_radial = np.mean(lengths[1:])
	cov_radial = np.std(lengths[1:])/lin_radial
	
	#~ print 'Linearity (X): {v:=.2f} mm'.format(v=lin_x)
	#~ print 'Linearity (Y): {v:=.2f} mm'.format(v=lin_y)
	#~ print 'CoV Distortion (X): {v:=.2f} %'.format(v=cov_x*100)
	#~ print 'CoV Distortion (Y): {v:=.2f} %'.format(v=cov_y*100)
	
	clear_output(win)
	output(win,'Grid Linearity (Mean X): {v:=.2f} mm'.format(v=lin_x_grid))
	output(win,'Grid Linearity (Mean Y): {v:=.2f} mm'.format(v=lin_y_grid))
	output(win,'Grid Distortion (CoV X): {v:=.2f} %'.format(v=cov_x_grid*100))
	output(win,'Grid Distortion (CoV Y): {v:=.2f} %'.format(v=cov_y_grid*100))
	output(win,'\nRadial Linearity (Mean diameter): {v:=.2f} mm'.format(v=lin_radial))
	output(win,'Radial Distortion (CoV diameter): {v:=.2f} %'.format(v=cov_radial*100))

	output(win,'\nMS Excel Results Table 1:')
	output(win,'Grid X distances (mm)\tGrid Y distances (mm)')
	for i in range(len(xdistances)):
		output(win,'{x:=.2f}\t{y:=.2f}'.format(x=xdistances[i],y=ydistances[i]))
	
	output(win,'\nMS Excel Results Table 2:')
	output(win,'Diameter (mm)')
	output(win,'{v:=.2f}\t--IGNORED--'.format(v=lengths[0]))
	for value in lengths[1:]:
		output(win,'{v:=.2f}'.format(v=value))

	win.outputbox.see('1.0')
	
	txt = win.outputbox.get('1.0',END)
	from source.functions.file_functions import save_results
	save_results(txt,name='DISTORTION')