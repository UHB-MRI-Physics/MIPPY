from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk       
import time
import scipy
import scipy.ndimage
import copy as cp


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
	print "Module loaded..."
	print "Received "+str(len(images))+" images."
	print os.getcwd()
	print dicomdir

	# Create all GUI elements
	win = Toplevel(master = master_window)
	
	# Image Set Matrix Size
        win.rows=images[-1].Rows
        win.cols=images[-1].Columns
            
        slicepositions = []
        try:
                for im in images:
                        slicepositions.append(str(im.PlanePositionSequence))
        except:
                for im in images:
                    slicepositions.append(str(im.ImagePositionPatient))
        slicepositions = np.array(slicepositions)
        win.slcs = np.shape(np.unique(slicepositions))[0]
        win.dyns = len(images)/win.slcs

        try:
                if (images[0].ImagePositionPatient==images[1].ImagePositionPatient):
                    resort_needed = True
                else:
                    resort_needed = False
        except AttributeError:
                if (images[0].PlanePositionSequence==images[1].PlanePositionSequence):
                    resort_needed = True
                else:
                    resort_needed = False
            
        if resort_needed:
                sorted_images = []
                for d in range(win.dyns):
                        for s in range(win.slcs):
                                sorted_images.append(images[s*win.dyns+d])
                images=sorted_images
        
	# Create canvases
	n_canvases = []
	for n in images
                n_canvases.append(str(n.SeriesInstanceUID))
        n_canvases = set(n_canvases)
	print n_canvases
	
	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)
	win.imcanvas_out = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)
	
	# Create scroll bars
	csl_orig=StringVar()
	csl_orig.set(win.imcanvas_orig.active)
	csl_out=StringVar()
	csl_out.set(win.imcanvas_out.active)
	cdyn_orig=StringVar()
	cdyn_orig.set("388")
	cdyn_out=StringVar()
	cdyn_out.set("4")
	win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
	win.imcanvas_out.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
	#~ win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
	#~ win.imcanvas_out.img.scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
	# Create info space for current dynamic/slice
	win.csl_orig = Label(win.imcanvases,textvariable=csl_orig,width=3)
	win.csl_out = Label(win.imcanvases,textvariable=csl_out,width=3)
	win.cdyn_orig = Label(win.imcanvases,textvariable=cdyn_orig,width=3)
	win.cdyn_out = Label(win.imcanvases,textvariable=cdyn_out,width=3)
	
	# Window layout
	win.imcanvas_orig.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nwes')
	win.imcanvas_orig.img_scrollbar.grid(row=0,column=2,sticky='ns')
	win.csl_orig.grid(row=1,column=2)
	win.imcanvas_out.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
	win.imcanvas_out.img_scrollbar.grid(row=0,column=5,sticky='ns')
	win.csl_out.grid(row=1,column=5)
	#~ win.scroll_dyn_orig.grid(row=2,column=0,sticky='we')
	#~ win.cdyn_orig.grid(row=2,column=1)
	#~ win.scroll_dyn_out.grid(row=2,column=3,sticky='we')
	#~ win.cdyn_out.grid(row=2,column=4)
	win.imcanvases.grid(row=0,column=0,sticky='nwes')
	
	# To resize the objects with the main window
	win.rowconfigure(0,weight=1)
	win.columnconfigure(0,weight=1)
	win.imcanvases.rowconfigure(0,weight=1)
	win.imcanvases.rowconfigure(1,weight=0)
	win.imcanvases.rowconfigure(2,weight=0)
	win.imcanvases.columnconfigure(0,weight=1)
	win.imcanvases.columnconfigure(1,weight=0)
	win.imcanvases.columnconfigure(2,weight=0)
	win.imcanvases.columnconfigure(3,weight=1)
	win.imcanvases.columnconfigure(4,weight=0)
	win.imcanvases.columnconfigure(5,weight=0)
	
	win.imcanvas_orig.load_images(images)
	
	# Create buttons
	win.buttons=Frame(win)
	
	win.l_method=Label(win.buttons,text="Subtraction Method:")
	win.method = StringVar(win)
	win.method.set("Simple")
	win.b_method = OptionMenu(win.buttons,win.method,"Simple",
                                  "Simple","Interpolated")

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
	
	win.b_subtract = Button(win.buttons, text="Subtract", command=lambda:subtract(win))        
	hide_rej(win)
	win.b_average = Button(win.buttons, text="Average", command=lambda:average(win))

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

	win.buttons.grid(row=0,column=1,sticky='news')
	
	# Resizing options
	win.buttons.rowconfigure(0,weight=0)
	win.buttons.rowconfigure(1,weight=0)
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
	print len(win.imcanvas_orig.images)
	win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))

        win.b_perf = Button(win.buttons, text="Create Perfusion Maps", command=lambda:perf(win))
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

def subtract(win):
	status(win,"Subtracting... ")
	win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))
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
			
		Im4Ds_=np.zeros((np.shape(Im4Ds)[0]+1,win.slcs,win.rows,win.cols))
		Im4Ds_[0:-1:1,:,:,:]=Im4Ds
		Im4Ds_[-1,:,:,:]=Im4Ds[-1,:,:,:]
		Im4Ds_=scipy.ndimage.interpolation.zoom(Im4Ds_,
									[2*(float(np.shape(Im4Ds_)[0]-0.5)/float(np.shape(Im4Ds_)[0])),1,1,1],
									order=1,mode="nearest",prefilter=False)
		Im4Ds=Im4Ds_[0:-1,:,:,:]

		Im4Dns_=np.zeros((np.shape(Im4Dns)[0]+1,win.slcs,win.rows,win.cols))
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
	win.imcanvas_out.load_images(np.reshape(win.images_processed,(np.size(win.images_processed,0)*win.slcs,win.rows,win.cols)))
	show_rej(win)
	return

def average(win):
	if hasattr(win,"images_processed"):
		status(win,"Averaging Subtracted Images... ")
		win.images_processed=np.mean(win.images_processed,0)
	else:
		status(win,"Averaging Original Images... ")
		win.images_processed=np.mean(win.Im4D,0)
	win.imcanvas_out.load_images(win.images_processed)
	if win.toggle.find('av_')<0:
		win.toggle+='av_'
	status(win,'DONE!!!')
	return
        
def save(win,dicomdir,images):
	if hasattr(win,"images_processed"):
		status(win,"Saving files...")
		##        win.Im3D_align=np.reshape(win.Im4D_align,(win.dyns*win.slcs,win.rows,win.cols))
		dicomdir_out=os.path.join(dicomdir,"_ASL")
		if not os.path.exists(dicomdir_out):
			os.makedirs(dicomdir_out)
		if len(np.shape(win.images_processed))==4:
			Im3D=np.reshape(win.images_processed,(np.shape(win.images_processed)[0]*np.shape(win.images_processed)[1],win.rows,win.cols))
		else:
			Im3D=win.images_processed
		if len(np.shape(win.images_processed))>=3:
			for s in range(np.shape(Im3D)[0]):
				images_out=cp.deepcopy(images[s])
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
			images_out=cp.deepcopy(images[s])
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
