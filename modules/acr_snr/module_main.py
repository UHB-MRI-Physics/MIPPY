from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import source.functions.image_processing as imp
from source.functions.file_functions import *
import source.functions.dicom_functions as dcm
import source.functions.misc_functions as mpy
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

def flatten_series():
	return False


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
#	if images[0].SeriesInstanceUID==images[-1].SeriesInstanceUID:
#		tkMessageBox.showwarning("ERROR","Images from two separate series are required.\n\n"
#								+"Please check your selection and reload the module.")
#		return
	
	print len(images)
	print len(images[0])
	
	if not len(images)==2:
		tkMessageBox.showwarning("ERROR","Images from two separate series are required.\n\n"
								+"Please check your selection and reload the module.")
		return

	win = Toplevel(master_window)
	win.images = images

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
	#~ win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	#~ win.phantom_options = [
		#~ 'ACR (TRA)',
		#~ 'ACR (SAG)',
		#~ 'ACR (COR)',
		#~ 'MagNET Flood (TRA)',
		#~ 'MagNET Flood (SAG)',
		#~ 'MagNET Flood (COR)']

	#~ win.phantom_label = Label(win.toolbar,text='\nPhantom selection:')
	#~ win.phantom = StringVar(win)
	#~ win.phantom_choice = OptionMenu(win.toolbar,win.phantom,win.phantom_options[0],*win.phantom_options)
	#~ mpy.optionmenu_patch(win.phantom_choice,win.phantom)
#	win.phantom.set(win.phantom_options[1])		# default value
	#~ win.mode=StringVar()
	#~ win.mode.set('valid')
	#~ win.advanced_checkbox = Checkbutton(win.toolbar,text='Use advanced ROI positioning?',var=win.mode,
								#~ onvalue='same',offvalue='valid')
	#~ win.mode_label = Label(win.toolbar,text='N.B. Advanced positioning is much slower, but accounts for the phantom not being fully contained in the image.',
					#~ wraplength=200,justify=LEFT)
					
	win.infobox = Text(win,state='disabled',height=20,width=40)
	win.infobox.tag_config('highlight', foreground='red')
	win.infobox.tag_config('unhighlight', foreground='black')
	win.outputbox = Text(win,state='disabled',height=10,width=80)

	win.toolbar.grid(row=0,column=2,sticky='nsew')
	win.roi_button.grid(row=2,column=0,sticky='ew')
	win.subtract_button.grid(row=3,column=0,sticky='ew')
	win.calc_button.grid(row=4,column=0,sticky='ew')
	#~ win.phantom_label.grid(row=0,column=0,sticky='w')
	#~ win.phantom_choice.grid(row=1,column=0,sticky='ew')
	#~ win.advanced_checkbox.grid(row=5,column=0,sticky='w')
	#~ win.mode_label.grid(row=6,column=0,sticky='w')
	
	win.outputbox.grid(row=2,column=0,columnspan=4,sticky='nsew')
	win.infobox.grid(row=0,column=3,rowspan=2,sticky='nsew')

	win.rowconfigure(0,weight=1)
	win.rowconfigure(1,weight=0)
	win.rowconfigure(2,weight=0)
	win.columnconfigure(0,weight=1)
	win.columnconfigure(1,weight=1)
	win.columnconfigure(2,weight=0)
	win.columnconfigure(3,weight=0)
	win.toolbar.rowconfigure(0,weight=0)
	win.toolbar.rowconfigure(1,weight=0)
	win.toolbar.rowconfigure(2,weight=0)
	win.toolbar.rowconfigure(3,weight=0)
	win.toolbar.rowconfigure(4,weight=0)
	win.toolbar.rowconfigure(5,weight=0)
	win.toolbar.rowconfigure(6,weight=0)
	win.toolbar.columnconfigure(0,weight=0)


	win.im1.load_images(images[0])
	win.im2.load_images(images[1])
	
	win.im1.show_image(7)
	win.im2.show_image(7)


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

def info(win,txt,red=False):
	win.infobox.config(state=NORMAL)
	if red:
		win.infobox.insert(END,txt+'\n','highlight')
	else:
		win.infobox.insert(END,txt+'\n')
	win.infobox.config(state=DISABLED)
	win.infobox.see(END)
	win.update()
	return

def clear_info(win):
	win.infobox.config(state=NORMAL)
	win.infobox.delete('1.0', END)
	win.infobox.insert(END,'DICOM HEADER CONFLICTS:\n')
	win.infobox.config(state=DISABLED)
	win.update()

def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def roi_reset(win):
	print "ROI reset"
	win.im1.delete_rois()
	#~ center = imp.find_phantom_center(win.im1.get_active_image(),phantom=win.phantom.get(),
							#~ subpixel=False,mode=win.mode.get())
	#~ xc = center[0]
	#~ yc = center[1]
	#~ print xc, yc
	
	#~ image = win.im1.get_active_image()
	#~ phantom=win.phantom.get()
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
		
	image = win.im1.get_active_image()

	geometry = imp.find_phantom_geometry(image,subpixel=False)
	center = (geometry[0],geometry[1])
	win.xc = xc = center[0]
	win.yc = yc = center[1]
	win.radius_x = radius_x = geometry[2]
	win.radius_y = radius_y = geometry[3]

	dim = 10
	
	cr_x = radius_x * np.sqrt(0.7)
	cr_y = radius_y * np.sqrt(0.7)
	
	
	
	h_x = cr_x - np.sqrt((cr_x**2) - ((dim*2)**2)/4) +dim
	h_y = cr_y - np.sqrt((cr_y**2) - ((dim*2)**2)/4) +dim
	
	xspc = cr_x-h_x-dim
	yspc = cr_y-h_y-dim
	
	# Comment this out to use phantom-adjusted spacing
	#~ xspc = 40
	#~ yspc = 40

	# Add five ROI's
	win.im1.roi_rectangle(xc-dim,yc-yspc-dim,dim*2,dim*2,tags=['top'],system='image')
	win.im1.roi_rectangle(xc+xspc-dim,yc-dim,dim*2,dim*2,tags=['right'],system='image')
	win.im1.roi_rectangle(xc-dim,yc+yspc-dim,dim*2,dim*2,tags=['bottom'],system='image')
	win.im1.roi_rectangle(xc-xspc-dim,yc-dim,dim*2,dim*2,tags=['left'],system='image')
	win.im1.roi_rectangle(xc-dim,yc-dim,dim*2,dim*2,tags=['center'],system='image')
	win.order = ['Top','Right','Bottom','Left','Center']
	z = win.im1.zoom_factor
	win.im1.create_oval(((xc-cr_x)*z,(yc-cr_y)*z,(xc+cr_x)*z,(yc+cr_y)*z),tags='round',outline='blue')
	return



def snr_calc(win):
	print "SNR calc"
	#~ rois = win.im1.find_withtag('roi')
	if len(win.im1.roi_list)==0:
		tkMessageBox.showerror("ERROR", "No ROI selected. Please create one or more"
							+" regions to analyse.")
		return
	imnum1 = win.im1.active
	imnum2 = win.im2.active
	
	# Check image headers to ensure images are matched.
	
	clear_info(win)
	diffs = dcm.compare_dicom(win.images[0][imnum1-1],win.images[1][imnum2-1])
	if len(diffs)==0:
		info(win,'\nNone detected')
	else:
		for row in diffs:
			#~ print row
			info(win,'\n'+row[0]+':')
			info(win,'1: '+row[1],red=True)
			info(win,'2: '+row[2],red=True)
	win.infobox.see('1.0')
	
	
	
	
	sub_image = [win.im1.get_active_image().px_float-win.im2.get_active_image().px_float]
	win.im2.load_images(sub_image)
	win.im2.roi_list = win.im1.roi_list
	signal = win.im1.get_roi_statistics()
	noise = win.im2.get_roi_statistics()
	snr_list = []
	for i in range(len(signal['mean'])):
		snr_list.append(signal['mean'][i]/noise['std'][i]*np.sqrt(2))
	#~ print snr_list
	#~ print np.mean(snr_list)
	
	#~ print len(signal['mean'])
	#~ print signal
	
	image1 = win.im1.get_active_image()
	
	clear_output(win)
	output(win,'SNR:\t{v:=.2f}'.format(v=np.mean(snr_list)))
	output(win,'Pixel Bandwidth (Hz/px):\t{v:=.2f}'.format(v=image1.pixel_bandwidth))
	output(win,'Image Bandwidth (Hz):\t{v:=.2f}'.format(v=image1.image_bandwidth))
	output(win,'Prescribed voxel size (X,Y,Z mm):\t{x:=.2f}\t{y:=.2f}\t{s:=.2f}'.format(
			x=win.im1.get_active_image().xscale,
			y=win.im1.get_active_image().yscale,
			s=win.images[0][imnum1-1].SliceThickness))
	
	output(win,'\nMS Excel Results Table')
	output(win,'Region\tArea\tMean\tStd Dev\tMin\tMax')
	for i in range(len(signal['mean'])):
		output(win,'SIG'+str(i+1)+' ('+win.order[i]+')\t{area:=.2f}\t{mean:=.2f}\t{std:=.2f}\t{min:=.2f}\t{max:=.2f}'.format(
			area=signal['area_px'][i],mean=signal['mean'][i],std=signal['std'][i],min=signal['min'][i],max=signal['max'][i]))
	for i in range(len(noise['mean'])):
		output(win,'NOI'+str(i+1)+' ('+win.order[i]+')\t{area:=.2f}\t{mean:=.2f}\t{std:=.2f}\t{min:=.2f}\t{max:=.2f}'.format(
			area=noise['area_px'][i],mean=noise['mean'][i],std=noise['std'][i],min=noise['min'][i],max=noise['max'][i]))
	win.outputbox.see('1.0')
	
	txt = win.outputbox.get('1.0',END)
	from source.functions.file_functions import save_results
	save_results(txt,name='SNR')
	
	

	#~ results = {
		#~ 'Signal': signal['mean'],
		#~ 'Noise': noise['std'],
		#~ 'Sig 1': signal['mean'][0],
		#~ 'Sig 2': signal['mean'][1],
		#~ 'Sig 3': signal['mean'][2],
		#~ 'Sig 4': signal['mean'][3],
		#~ 'Sig 5': signal['mean'][4],
		#~ 'Noi 1': noise['std'][0],
		#~ 'Noi 2': noise['std'][1],
		#~ 'Noi 3': noise['std'][2],
		#~ 'Noi 4': noise['std'][3],
		#~ 'Noi 5': noise['std'][4],
		#~ 'SNR (mean)': np.mean(snr_list),
		#~ 'Stdev (SNR)': np.std(snr_list)
		#~ }
	#~ print results

	#~ save_results(results)
#	display_results(results,win)

	win.im2.load_images(win.images[1])
	win.im2.show_image(imnum2)

	return

def view_subtraction(win):
	print "View subtraction"
	px1 = win.im1.get_active_image().px_float
	px2 = win.im2.get_active_image().px_float
	sub = px1-px2
	quick_display(sub,win)
	return