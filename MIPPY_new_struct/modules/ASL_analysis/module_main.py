from Tkinter import *
import tkMessageBox
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
import time
import datetime
import numpy as np
import numpy.matlib
from copy import deepcopy
from dicom.tag import Tag
from scipy.optimize import minimize
from scipy.optimize import fsolve
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import scipy
##from sympy.solvers import solveset
from sympy import Symbol

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
	print "Module loaded..."
	print "Received "+str(len(images))+" images."
	print os.getcwd()
	print dicomdir

	# Create all GUI elements
	win = Toplevel(master = master_window)
	win.title("MIPPY-ASL Analysis: "+"Series "+str(images[0][0].SeriesNumber).zfill(3)+"-"+str(images[0][0].SeriesDescription))
	
	# Image Set Matrix Size
	win.rows=[]
	win.cols=[]
	win.slcs=[]
	win.dyns=[]

	slicepositions = []
	print len(images)
	for n in range(len(images)):
		win.rows.append(images[n][-1].Rows)
		win.cols.append(images[n][-1].Columns)
		try:
			for im in images[n]:
				slicepositions.append(str(im.PlanePositionSequence))
		except:
			for im in images[n]:
				slicepositions.append(str(im.ImagePositionPatient))
		slicepositions = np.array(slicepositions)
		win.slcs.append(np.shape(np.unique(slicepositions))[0])
		win.dyns.append(len(images[n])/win.slcs[n])

		try:
			if (images[n][0].ImagePositionPatient==images[n][1].ImagePositionPatient):
				resort_needed = True
			else:
				resort_needed = False
		except AttributeError:
			if (images[n][0].PlanePositionSequence==images[n][1].PlanePositionSequence):
				resort_needed = True
			else:
				resort_needed = False

		if resort_needed:
			sorted_images = []
			for d in range(win.dyns[n]):
				for s in range(win.slcs[n]):
					sorted_images.append(images[s*win.dyns[n]+d])
			images[n]=sorted_images
		slicepositions = []

	# Create canvases
		
	win.canvas_holder=Frame(win)
	win.imframes=[]
	win.imcanvases=[]
	
	N=len(images)+1

	rlen=[0,1,2,3,2,3,3]

	win.imASL=None
	win.imT1=None
	win.imM0=None
	
	for n in range(N):
		win.imframes.append(Frame(win.canvas_holder))
		win.imcanvases.append(MIPPYCanvas(win.imframes[n],bd=0 ,width=384,height=384,drawing_enabled=True))

		# Drop-box buttons
		if n<len(images):
			win.imframes[n].imtype = StringVar()
			win.imframes[n].imtype.set("Image Type")
			win.imframes[n].b_imtype = OptionMenu(win.imframes[n],win.imframes[n].imtype,"Image Type","Image Type","ASL","T1 map", "M0 map")
			win.imframes[n].imtype.trace('w',lambda name, idx, mode:im_check(win))
		else:
			win.imframes[n].l_results=Label(win.imframes[n],text="Results")

		# Create scroll bars
		win.imcanvases[n].csl=StringVar()
		win.imcanvases[n].csl.set(win.imcanvases[n].active)
		win.imcanvases[n].img_scrollbar = Scrollbar(win.imframes[n],orient='vertical')
		win.imframes[n].csl = Label(win.imframes[n],textvariable=win.imcanvases[n].active_str,width=7)

		# Window layout
		if n<len(images):
			win.imframes[n].b_imtype.grid(row=0,column=1,sticky='new')
			win.imframes[n].b_imtype.configure(width=8)
		else:
			win.imframes[n].l_results.grid(row=0,column=1,sticky='new')

		win.imcanvases[n].roi_mode='freehand'

		win.imcanvases[n].grid(row=1,column=0,rowspan=2,columnspan=3,sticky='nwes')
		win.imcanvases[n].img_scrollbar.grid(row=1,column=3,sticky='nws')
		win.imframes[n].csl.grid(row=2,column=3,sticky='s')

		win.imframes[n].rowconfigure(0,weight=0)
		win.imframes[n].rowconfigure(1,weight=1)
		win.imframes[n].rowconfigure(2,weight=0)
		win.imframes[n].columnconfigure(0,weight=0)
		win.imframes[n].columnconfigure(1,weight=0)
		win.imframes[n].columnconfigure(2,weight=0)
		win.imframes[n].columnconfigure(3,weight=0)

		row_num=(n-n%rlen[N])/rlen[N]
		col_num=n%rlen[N]
		win.imframes[n].grid(row=row_num,column=col_num,sticky='news')

	win.canvas_holder.grid(row=0,column=0,sticky='news')

	win.images=images

	for n in range(len(images)):
		win.imcanvases[n].load_images(images[n])
		non_zero=win.imcanvases[n].get_3d_array()
		non_zero=non_zero[np.where(non_zero>0)]
		win.imcanvases[n].set_window_level(np.percentile(non_zero,95.)-np.percentile(non_zero,15.),np.percentile(non_zero,15.)+(np.percentile(non_zero,95.)-np.percentile(non_zero,15.))/2)
	
	# Create buttons
	win.buttons=Frame(win)
	
	win.l_method=Label(win.buttons,text="Subtraction Method:")
	win.method = StringVar(win)
	win.method.set("Simple")
	win.b_method = OptionMenu(win.buttons,win.method,"Simple","Simple","Interpolated")

	win.l_reject=Label(win.buttons,text="Pairs to removed from analysis")
	win.reject_in=StringVar(win)
	win.reject_in.set(0)
	win.b_reject_in=Entry(win.buttons,textvariable=win.reject_in,width=5)

	win.c_rev_in=IntVar(win)
	win.c_rev_in.set(0)
	win.c_rev=Checkbutton(win.buttons,text="Reverse Tag and Control",variable=win.c_rev_in)

	win.l_T1bl=Label(win.buttons,text="T1 of Arterial Blood [ms]:")
	win.T1bl_in=StringVar(win)
	win.T1bl_in.set(1500)
	win.b_T1bl_in=Entry(win.buttons,textvariable=win.T1bl_in,width=5)

	win.l_T1tis=Label(win.buttons,text="T1 of Tissue [ms]:")
	win.T1tis_in=StringVar(win)
	win.T1tis_in.set(840)
	win.b_T1tis_in=Entry(win.buttons,textvariable=win.T1tis_in,width=5)

	win.l_M0tis=Label(win.buttons,text="M0 of Tissue:")
	win.M0tis_in=StringVar(win)
	win.M0tis_in.set(600)
	win.b_M0tis_in=Entry(win.buttons,textvariable=win.M0tis_in,width=5)

	win.l_PLD=Label(win.buttons,text="Post-Labelling Delay [ms]:")
	win.PLD_in=IntVar(win)
	win.PLD_in.set(1300)
	win.b_PLD_in=Entry(win.buttons,textvariable=win.PLD_in,width=5)

	win.rb_TAvar = IntVar()
	win.rb_TAvar.set(1)
	win.rb_TAauto = Radiobutton(win.buttons, text="Set TA automatically\nfrom the DICOM header", variable=win.rb_TAvar, value=1, command=lambda:hide_TA(win))

	win.rb_TA = Radiobutton(win.buttons, text="Set TA manually [ms]:", variable=win.rb_TAvar, value=2, command=lambda:show_TA(win))
	win.TA_in=StringVar(win)
	win.TA_in.set(65)
	win.b_TA = Entry(win.buttons,textvariable='-',width=6,state="disabled")

	win.c_rev_in=IntVar(win)
	win.c_rev_in.set(0)
	win.c_rev=Checkbutton(win.buttons,text="Reversed Slice Acquisition",variable=win.c_rev_in)
	
	win.b_subtract = Button(win.buttons, text="Subtract", command=lambda:subtract(win))        
	hide_rej(win)
	win.b_average = Button(win.buttons, text="Average", command=lambda:average(win))

	win.l_win_centr = Label(win.buttons,text="Window Centre")
	win.win_centr_in = IntVar(win)
	win.win_centr_in.set(0)
	win.b_win_centr = Entry(win.buttons,textvariable=win.win_centr_in,width=5)
	win.l_win_width = Label(win.buttons,text="Window Width")
	win.win_width_in = IntVar(win)
	win.win_width_in.set(0)
	win.b_win_width = Entry(win.buttons,textvariable=win.win_width_in,width=5)
	
	win.c_NonZero_in=IntVar(win)
	win.c_NonZero_in.set(1)
	win.c_NonZero=Checkbutton(win.buttons,text="Exclude zero values",variable=win.c_NonZero_in,state="enabled")

	win.b_ROI = Button(win.buttons, text="Analyse ROI", command=lambda:ROI_stats(win))

	# Window layout       
	win.l_method.grid(row=0,column=0,sticky='nw')
	win.b_method.grid(row=1,column=0, sticky='nw',ipadx=15)
	win.l_reject.grid(row=2,column=0, sticky='nw')
	win.b_reject_in.grid(row=3,column=0,sticky='nw')
	win.c_rev.grid(row=4,column=0,sticky='nw')
	win.b_subtract.grid(row=5,column=0,sticky='nw')
	win.b_average.grid(row=6,column=0,sticky='nw')
	win.l_T1bl.grid(row=7,column=0,sticky='sw')
	win.b_T1bl_in.grid(row=7,column=1,sticky='sw')
	win.l_T1tis.grid(row=8,column=0,sticky='sw')
	win.b_T1tis_in.grid(row=8,column=1,sticky='sw')
	win.l_M0tis.grid(row=9,column=0,sticky='sw')
	win.b_M0tis_in.grid(row=9,column=1,sticky='sw')
	win.l_PLD.grid(row=10,column=0,sticky='sw')
	win.b_PLD_in.grid(row=10,column=1,sticky='sw')
	win.rb_TAauto.grid(row=11,column=0,sticky='sw',rowspan=2,columnspan=4)
	win.rb_TA.grid(row=13,column=0,sticky='nw',columnspan=2)
	win.b_TA.grid(row=13,column=1,sticky='nw')
	win.c_rev.grid(row=14,column=0,sticky='nw',columnspan=4)

	win.c_NonZero.grid(row=15,column=0,columnspan=2,sticky='sw')
	win.b_ROI.grid(row=16,column=0,sticky='sw')

	win.buttons.grid(row=0,column=1,sticky='news')
	
	# Resizing options
	win.buttons.rowconfigure(0,weight=0)
	win.buttons.rowconfigure(1,weight=0)
	win.buttons.rowconfigure(2,weight=0)
	win.buttons.rowconfigure(3,weight=0)
	win.buttons.rowconfigure(4,weight=0)
	win.buttons.rowconfigure(5,weight=0)
	win.buttons.rowconfigure(6,weight=0)
	win.buttons.rowconfigure(7,weight=0)
	win.buttons.rowconfigure(8,weight=0)
	win.buttons.rowconfigure(9,weight=0)
	win.buttons.rowconfigure(10,weight=0)
	win.buttons.rowconfigure(11,weight=0)
	win.buttons.rowconfigure(12,weight=0)
	win.buttons.rowconfigure(13,weight=0)
	win.buttons.rowconfigure(14,weight=1)
	win.buttons.rowconfigure(15,weight=0)
	win.buttons.rowconfigure(16,weight=0)

	win.buttons.columnconfigure(0,weight=0)
	win.buttons.columnconfigure(1,weight=0)

	# Message box
	win.message_box=Frame(win)
	
	win.b_message = Text(win.message_box,state='disabled',height=6,width=120)

	# Window layout
	win.b_message.grid(row=0,column=0,sticky='news')

	win.message_box.grid(row=1,column=0,sticky='news')

	# Resizing option
	win.message_box.rowconfigure(0,weight=1)

	# Run buttons
	win.run_buttons=Frame(win)

	win.b_perf = Button(win.run_buttons, text="Create Perfusion Map", command=lambda:perf(win))
	win.b_save = Button(win.run_buttons, text="Save", command=lambda:save(win,dicomdir,images))

	# Window layout
	win.b_perf.grid(row=0,column=0,sticky='nw')
	win.b_save.grid(row=1,column=0,sticky='nw')

	win.run_buttons.grid(row=1,column=1,sticky="news")
	
	return
	
def close_window(window):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def im_check(win):
	win.imASL=None
	win.imT1=None
	win.imM0=None
	for n in range(len(win.imframes)-1):
		if win.imframes[n].imtype.get()=="ASL":
			win.imASL=n
		elif win.imframes[n].imtype.get()=="T1 map":
			win.imT1=n
			hide_T1(win)
		elif win.imframes[n].imtype.get()=="M0 map":
			win.imM0=n
			hide_M0(win)
		if win.imT1==None:
			show_T1(win)
		if win.imM0==None:
			show_M0(win)

def status(win,*txt):
	print_str = ''
	for arg in txt:
		print_str = print_str+str(arg)
	win.b_message.config(state=NORMAL)
	win.b_message.insert(END,print_str+'\n')
	win.b_message.bind('<1>', lambda event: win.b_message.focus_set())
	win.b_message.config(state=DISABLED)
	win.b_message.see(END)
	win.update()

def status_clear(win):
	win.b_message.config(state=NORMAL)
	win.b_message.delete(1.0,END)
	win.b_message.config(state=DISABLED)
	win.update()

def ROI_stats(win):
	for n in range(len(win.imcanvases)):
		try:
			if win.c_NonZero_in.get()==0:
				win.pix_seg=np.array(win.imcanvases[n].get_roi_pixels())
			else:
				win.pix_seg=np.array(win.imcanvases[n].get_roi_pixels())
				win.pix_seg=win.pix_seg[np.where(win.pix_seg!=0)]

			if n==len(win.imcanvases)-1:
				status(win,'Results ROI stats: mean=',np.round(np.mean(win.pix_seg),1),' std=',np.round(np.std(win.pix_seg)+0.05,1),' min=',np.round(np.amin(win.pix_seg),1),' max=',np.round(np.amax(win.pix_seg),1),' area=',np.size(win.pix_seg),'px')
			else:
				status(win,win.imframes[n].imtype.get()+' ROI stats: mean=',np.round(np.mean(win.pix_seg),1),' std=',np.round(np.std(win.pix_seg)+0.05,1),' min=',np.round(np.amin(win.pix_seg),1),' max=',np.round(np.amax(win.pix_seg),1),' area=',np.size(win.pix_seg),'px')
		except:
			pass

def hide_T1(win):
	win.b_T1tis_in.config(textvariable='-',state='disabled')
	return

def show_T1(win):
	try:
		win.b_T1tis_in.config(textvariable=win.T1tis_in,state='normal')
	except AttributeError:
		return

def hide_M0(win):
	win.b_M0tis_in.config(textvariable='-',state='disabled')
	return

def show_M0(win):
	try:
		win.b_M0tis_in.config(textvariable=win.M0tis_in,state='normal')
	except AttributeError:
		return

def hide_TA(win):
	"""Greys out Initial TA window"""
	if win.rb_TAvar.get()==1:
		win.b_TA.configure(textvariable='-',state="disabled")
		win.rb_TA.focus()
	return

def show_TA(win):
	"""Activates the TA windows"""
	if win.rb_TAvar.get()==2:
		win.b_TA.configure(textvariable=win.TA_in,state="normal")
		win.b_TA.focus()

def hide_rej(win):
	"""Greys out Pairs to remove from analysis"""
	if ~hasattr(win,"images_processed"):
		win.l_reject.configure(state="disabled")
		win.b_reject_in.configure(state="disabled")
	return

def show_rej(win):
	"""Activates Pairs to remove from analysis"""
	if hasattr(win,"images_processed"):
		win.l_reject.configure(state="normal")
		win.b_reject_in.configure(state="normal")
		win.b_reject_in.focus()

def str2num(string):
	return sum(((list(range(*[int(j) + k for k,j in enumerate(i.split('-'))]))
	if '-' in i else [int(i)]) for i in string.split(',')), [])

def error1_popup(win):
	txt=("ASL series must be selected to perform this action!")
	tkMessageBox.showerror('ERROR',txt)
	return

def error2_popup(win):
	txt=("Please subtract the ASL data first!")
	tkMessageBox.showerror('ERROR',txt)
	return

def error3_popup(win):
	txt=("The dimensions of T1 and M0 maps must match the ASL data!")
	tkMessageBox.showerror('ERROR',txt)
	return

def subtract(win):
	if win.imASL==None:
		error1_popup(win)
		return
	status(win,"Subtracting... ")
	win.Im4D=np.array([a.px_float for a in win.imcanvases[win.imASL].images]).reshape((win.dyns[win.imASL],win.slcs[win.imASL],win.rows[win.imASL],win.cols[win.imASL]))
	if win.method.get()=="Simple":
		if win.c_rev_in.get()==0:
			Im4Ds=win.Im4D[0::2,:,:,:]
			Im4Dns=win.Im4D[1::2,:,:,:]
		else:
			Im4Ds=win.Im4D[1::2,:,:,:]
			Im4Dns=win.Im4D[0::2,:,:,:]
		win.toggle='s_'
	elif win.method.get()=="Interpolated":
		if win.c_rev_in.get()==0:
			Im4Ds=win.Im4D[0::2,:,:,:]
			Im4Dns=win.Im4D[1::2,:,:,:]
		else:
			Im4Ds=win.Im4D[1::2,:,:,:]
			Im4Dns=win.Im4D[0::2,:,:,:]
			
		Im4Ds_=np.zeros((np.shape(Im4Ds)[0]+1,win.slcs[win.imASL],win.rows[win.imASL],win.cols[win.imASL]))
		Im4Ds_[0:-1:1,:,:,:]=Im4Ds
		Im4Ds_[-1,:,:,:]=Im4Ds[-1,:,:,:]
		Im4Ds_=scipy.ndimage.interpolation.zoom(Im4Ds_,
									[2*(float(np.shape(Im4Ds_)[0]-0.5)/float(np.shape(Im4Ds_)[0])),1,1,1],
									order=1,mode="nearest",prefilter=False)
		Im4Ds=Im4Ds_[0:-1,:,:,:]

		Im4Dns_=np.zeros((np.shape(Im4Dns)[0]+1,win.slcs[win.imASL],win.rows[win.imASL],win.cols[win.imASL]))
		Im4Dns_[0,:,:,:]=Im4Dns[0,:,:,:]
		Im4Dns_[1:,:,:,:]=Im4Dns
		Im4Dns_=scipy.ndimage.interpolation.zoom(Im4Dns_,
									[2*(float(np.shape(Im4Dns_)[0]-0.5)/float(np.shape(Im4Dns_)[0])),1,1,1],
									order=1,mode="nearest",prefilter=False)
		Im4Dns=Im4Dns_[1:,:,:,:]
		win.toggle='si_'
	win.images_processed=np.subtract(Im4Ds,Im4Dns)
	if win.reject_in.get()!='0':
		rejected=str2num(win.reject_in.get())
		status(win,"rejected array: %s" %rejected)
		rejected=np.subtract(rejected,1)
		win.images_processed=[element for n, element in enumerate(win.images_processed) if n not in rejected]
	status(win,"DONE!!!")
	status(win,"Number of Subtracted Pairs: %s" %np.size(win.images_processed,0))
	win.imcanvases[-1].load_images(np.reshape(win.images_processed,(np.shape(win.images_processed)[0]*np.shape(win.images_processed)[1],np.shape(win.images_processed)[2],np.shape(win.images_processed)[3])))
	show_rej(win)
	reset_windowing(win.imcanvases[-1])
	return

def average(win):
	if win.imASL==None:
		error2_popup(win)
		return
	if hasattr(win,"images_processed"):
		status(win,"Averaging Subtracted Images... ")
		win.images_processed=np.mean(win.images_processed,0)
	else:
		status(win,"Averaging Original Images... ")
		win.images_processed=np.mean(win.Im4D,0)
	win.imcanvases[-1].load_images(win.images_processed)
	if win.toggle.find('av_')<0:
		win.toggle+='av_'
	status(win,'DONE!!!')
	sort_TIs(win)
	reset_windowing(win.imcanvases[-1])
	return

def sort_TIs(win):
	"""Sorting TIs for each individual image"""
	status(win,"Sorting TIs for each individual image...")
	# First - get the TA
	TA=np.zeros(win.slcs[win.imASL]-1)
	if win.rb_TAvar.get()==1:
		for a in range(win.slcs[win.imASL]-1):
			tst_a = str(win.images[win.imASL][a].AcquisitionTime)
			tst_b = str(win.images[win.imASL][a+1].AcquisitionTime)
			dst = str(win.images[win.imASL][a].StudyDate)

			time_a = datetime.datetime(int(dst[0:4]),int(dst[4:6]),int(dst[6:8]),int(tst_a[0:2]),int(tst_a[2:4]),int(tst_a[4:6]),int(tst_a[7:]))
			time_b = datetime.datetime(int(dst[0:4]),int(dst[4:6]),int(dst[6:8]),int(tst_b[0:2]),int(tst_b[2:4]),int(tst_b[4:6]),int(tst_b[7:]))

			TA[a] = (time_b-time_a).total_seconds()*1000

		#status(win,TA)
		TAav=np.round(float(np.mean(TA,0)),2)
		win.TA_in.set(abs(float(TAav)))
		txt=("Estimated TA is %s [ms]" %(win.TA_in.get()))
		status(win,txt)
		if TAav<0:
			win.c_rev_in.set(1)

	# second - all TI values
	TIs=np.zeros(win.slcs[win.imASL])
	for s in range(win.slcs[win.imASL]):
		if win.c_rev_in.get()==0:
			TIs[s]=win.PLD_in.get()+s*float(win.TA_in.get())
		elif win.c_rev_in.get()==1:
			TIs[s]=win.PLD_in.get()+(win.slcs-s-1)*float(win.TA_in.get())

	status(win,"These are the follwing times for each slice:")
	status(win,TIs)
	win.TIs=TIs
	return

def perf(win):
	win.Im3Dperf=np.zeros((np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]))
	test=np.zeros((np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]))
	if win.imASL==None:
		error2_popup(win)
	win.Im3D=np.array([a.px_float for a in win.imcanvases[-1].images]).reshape((np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]))
	if win.imT1==None:
		win.T1=np.tile(np.float64(win.T1tis_in.get()),[np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]])
	else:
		try:
			win.T1=np.array([a.px_float for a in win.imcanvases[win.imT1].images]).reshape((np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]))
		except IndexError or ValueError:
			error3_popup(win)
			return

	if win.imM0==None:
		win.M0=np.float64(win.M0tis_in.get())
		win.M0=np.tile(win.M0tis_in.get(),[np.shape(win.images_processed)[0],
		np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]])
	else:
		try:
			win.M0=np.array([a.px_float for a in win.imcanvases[win.imM0].images]).reshape((np.shape(win.images_processed)[0],np.shape(win.images_processed)[1],np.shape(win.images_processed)[2]))
		except IndexError or ValueError:
			error3_popup(win)
			return
	f=Symbol('f')
	for s in range(win.slcs[win.imASL]):
		status(win,"Calculating maps: slice ",s+1)
		for y in range (win.rows[win.imASL]):
			for x in range (win.cols[win.imASL]):
				try:
					win.Im3Dperf[s,y,x] = fsolve(perf_fun,0,(win.M0[s,y,x], win.TIs[s],win.T1[s,y,x],np.float64(win.T1bl_in.get()),win.Im3D[s,y,x]))[0]
				except IndexError:
					win.Im3Dperf[s,y,x] = 0.
				
				if win.Im3Dperf[s,y,x]==np.inf:
					win.Im3Dperf[s,y,x]=0.
	win.imcanvases[-1].load_images(win.Im3Dperf)
	reset_windowing(win.imcanvases[-1])

def reset_windowing(canvas):
	non_zero=canvas.get_3d_array()
	non_zero=canvas.get_3d_array()
	non_zero=non_zero[np.where(non_zero>0)]
	canvas.set_window_level(np.percentile(non_zero,95.)-np.percentile(non_zero,15.),np.percentile(non_zero,15.)+(np.percentile(non_zero,95.)-np.percentile(non_zero,15.))/2)

def perf_fun(f,M0,TI,T1,T1bl,Im3D):
	return 0.02*f/3600*M0*(np.exp(TI*(1./T1+f/100./60000))-np.exp(TI/np.float64(T1bl)))/(1./T1bl-1./T1-f/100./60000)-Im3D

def save(win,dicomdir,images):
	if hasattr(win,"images_processed"):
		status(win,"Saving files...")
		##        win.Im3D_align=np.reshape(win.Im4D_align,(win.dyns*win.slcs,win.rows,win.cols))
		dicomdir_out=os.path.join(dicomdir,"_ASLmaps")
		if not os.path.exists(dicomdir_out):
			os.makedirs(dicomdir_out)
		if len(np.shape(win.images_processed))==4:
			Im3D=np.reshape(win.images_processed,(np.shape(win.images_processed)[0]*np.shape(win.images_processed)[1],win.rows,win.cols))
		else:
			Im3D=win.images_processed
		if len(np.shape(win.images_processed))>=3:
			for s in range(np.shape(Im3D)[0]):
				images_out=deepcopy(images[win.imASL][s])
				try:
					rs = images_out[0x28,0x1053].value
				except:
					rs = 1
				try:
					ri = images_out[0x28,0x1052].value
				except:
					ri = 0
				try:
					ss = images_out[0x2005,0x100E].value
				except:
					ss = 1
				images_out.SeriesDescription=''.join([images_out.SeriesDescription,win.toggle])
				images_out.SOPInstanceUID = ''.join([images_out.SOPInstanceUID,".0.",str(len(win.toggle))])
				images_out.SeriesInstanceUID = ''.join([images_out.SeriesInstanceUID,".0.",str(len(win.toggle))])
				images_out.PixelData = np.clip(((Im3D[s,:,:].reshape(win.cols*win.rows)-ri)/rs),0,np.max(Im3D)).astype(np.uint16)

				file_out=os.path.join(dicomdir_out,"im_"+win.toggle+str(s+1).zfill(3)+".dcm")
				images_out.save_as(file_out)
		else:
			s=0
			images_out=deepcopy(images[win.imASL][s])
			try:
				rs = images_out[0x28,0x1053].value
			except:
				rs = 1
			try:
				ri = images_out[0x28,0x1052].value
			except:
				ri = 0
			try:
				ss = images_out[0x2005,0x100E].value
			except:
				ss = 1
			images_out.SeriesDescription=''.join([images_out.SeriesDescription,win.toggle])
			images_out.SOPInstanceUID = ''.join([images_out.SOPInstanceUID,".0.",str(len(win.toggle))])
			images_out.SeriesInstanceUID = ''.join([images_out.SeriesInstanceUID,".0.",str(len(win.toggle))])
			images_out.PixelData = np.clip(((Im3D.reshape(win.cols*win.rows)-ri)/rs),0,np.max(Im3D)).astype(np.uint16)
			
			file_out=os.path.join(dicomdir_out,"im_"+win.toggle+str(s+1).zfill(3)+".dcm")
			images_out.save_as(file_out)
		if s==0:
			status(win,'Saved ', s+1, 'file in: ',dicomdir_out)
		else:
			status(win,'Saved ', s+1, 'files in: ',dicomdir_out)
	else:
		status(win,"There are no processed files to be saved... ")
	return
