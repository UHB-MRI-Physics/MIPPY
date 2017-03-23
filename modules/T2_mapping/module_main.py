from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
from T2_mapping import T2_mapping as T2map
import time
import numpy as np
import numpy.matlib
from copy import deepcopy
from dicom.dataset import Dataset

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
##        print images[-1]
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
	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=True)
	win.imcanvas_maps = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=True)

	win.imcanvas_orig.roi_mode='ellipse'
	win.imcanvas_maps.roi_mode='ellipse'

	# Create scroll bars
	csl_orig=StringVar()
        csl_orig.set(win.imcanvas_orig.active)
        csl_maps=StringVar()
        csl_maps.set(win.imcanvas_maps.active)
        cdyn_orig=StringVar()
        cdyn_orig.set("388")
        cdyn_maps=StringVar()
        cdyn_maps.set("4")
	win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        win.imcanvas_maps.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        #~ win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        #~ win.imcanvas_maps.img.scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        # Create info space for current dynamic/slice
        win.csl_orig = Label(win.imcanvases,textvariable=csl_orig,width=3)
        win.csl_maps = Label(win.imcanvases,textvariable=csl_maps,width=3)
        win.cdyn_orig = Label(win.imcanvases,textvariable=cdyn_orig,width=3)
        win.cdyn_maps = Label(win.imcanvases,textvariable=cdyn_maps,width=3)

        # Window layout
        win.imcanvas_orig.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nwes')
        win.imcanvas_orig.img_scrollbar.grid(row=0,column=2,sticky='ns')
        win.csl_orig.grid(row=1,column=2)
        win.imcanvas_maps.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
        win.imcanvas_maps.img_scrollbar.grid(row=0,column=5,sticky='ns')
        win.csl_maps.grid(row=1,column=5)
        #~ win.scroll_dyn_orig.grid(row=2,column=0,sticky='we')
        #~ win.cdyn_orig.grid(row=2,column=1)
        #~ win.scroll_dyn_maps.grid(row=2,column=3,sticky='we')
        #~ win.cdyn_maps.grid(row=2,column=4)
        win.imcanvases.grid(row=0,column=0,sticky='nwes')

        # To resize the objects with the main window
        win.rowconfigure(0,weight=2)
        win.columnconfigure(0,weight=2)
        win.imcanvases.rowconfigure(0,weight=2)
        win.imcanvases.rowconfigure(1,weight=0)
        win.imcanvases.rowconfigure(2,weight=0)
        win.imcanvases.columnconfigure(0,weight=2)
        win.imcanvases.columnconfigure(1,weight=0)
        win.imcanvases.columnconfigure(2,weight=0)
        win.imcanvases.columnconfigure(3,weight=2)
        win.imcanvases.columnconfigure(4,weight=0)
        win.imcanvases.columnconfigure(5,weight=0)

        win.imcanvas_orig.load_images(images)

        # Create buttons
        win.buttons=Frame(win)
        
        win.rb_TEvar = IntVar()
        win.rb_TEvar.set(1)
        win.rb_TEauto = Radiobutton(win.buttons, text="Set TEs automatically from the DICOM header", variable=win.rb_TEvar, value=1, command=lambda:hide_TE(win))

        win.rb_TE = Radiobutton(win.buttons, text="Set Individual TEs (comma-separated) [ms]:", variable=win.rb_TEvar, value=2, command=lambda:show_TE(win))
        win.TE_in=StringVar(win)
        win.b_TE = Entry(win.buttons,textvariable=win.TE_in,width=30,state="disabled")

        # Window layout
        
        win.rb_TEauto.grid(row=0,column=0,sticky='sw',rowspan=2,columnspan=4)
        win.rb_TE.grid(row=2,column=0,sticky='nw',columnspan=2)
        win.b_TE.grid(row=3,column=0,sticky='nw')
                            
        win.buttons.grid(row=0,column=1,sticky='news')

        # Resizing options
        win.buttons.rowconfigure(0,weight=0)
        win.buttons.rowconfigure(1,weight=0)
        win.buttons.columnconfigure(0,weight=0)
        win.buttons.columnconfigure(1,weight=0)

        # Message box
        win.message_box=Frame(win)

        win.b_message = Text(win.message_box,state='disabled',height=15)

        # Window layout
        win.b_message.grid(row=0,column=0,sticky='news')

        win.message_box.grid(row=1,column=0,sticky='wes')

        # Resizing option
        win.message_box.rowconfigure(0,weight=1)
        win.rowconfigure(1,weight=1)

        # Run buttons
        win.run_buttons=Frame(win)

        try:
                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))
        except Exception,win.Im4D:
                status(win,"Multiple Series Detected...\n")
                win.c_rev_in.set(1)
                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((np.size(images,0)/win.slcs,win.slcs,win.rows,win.cols))
        win.b_run = Button(win.run_buttons, text="Create T2 maps", command=lambda:T2_map(win,images))
        win.b_save = Button(win.run_buttons, text="Save T2 maps", command=lambda:save(win,dicomdir,images))

        # Window layout
        win.b_run.grid(row=0,column=0,sticky='new')
        win.b_save.grid(row=1,column=0,sticky='new')

        win.run_buttons.grid(row=1,column=1,sticky="news")
        
	return
	
def close_window(win):
	"""Closes the window passed as an argument"""
	active_frame.destroy()
	return

def status(win,txt):
        win.b_message.config(state=NORMAL)
        win.b_message.insert(END,txt)
        win.b_message.config(state=DISABLED)
        win.b_message.see(END)
        win.update()

def status_clear(win):
        win.b_message.config(state=NORMAL)
        win.b_message.delete(1.0,END)
        win.b_message.config(state=DISABLED)
        win.update()

def hide_TE(win):
        """Greys out TE window"""
        if win.rb_TEvar.get()==1:
                win.b_TE.configure(state="disabled")
                win.rb_TE.focus()
        return

def show_TE(win):
        """Activates the TE windows"""
        if win.rb_TEvar.get()==2:
                win.b_TE.configure(state="normal")
                win.b_TE.focus()
        return
def T2_map(win,images):
        """Creating maps - T2_mapping.py script"""
        status_clear(win)
        win.TEs=sort_TEs(win,images)
        
        if win.TEs==None:
                return
        status(win,"Fitting T2 maps...\n")
        start_time=time.time()
        win.maps=np.zeros((5,win.slcs,win.rows,win.cols))
        win.maps=T2map(win.Im4D,win.TEs,images,threshold=0,GoF=50)
        
        run_time = time.time()-start_time

        if run_time>=60:
                txt=("Fitting completed in %s minutes and %s seconds. \n" %(int(run_time/60),int(run_time-int(run_time/60)*60)) )
        else:
                txt=("Fitting completed in %s seconds. \n" %(int(np.ceil(run_time))) )
        status(win,txt)        

        win.imcanvas_maps.load_images([b for b in (np.reshape(win.maps,(5*win.slcs,win.rows,win.cols)) )])
                
        return

def sort_TEs(win,images):
        """Sorting TEs for each individual image"""
        status(win,"Sorting TEs for each image... \n")
        TEs=np.zeros(win.dyns*win.slcs)
        if win.rb_TEvar.get()==1:
                for d in range(win.dyns):
                        for s in range(win.slcs):
                                TEs[int(win.slcs)*d+s]=float(images[int(win.slcs)*d+s].EchoTime)
        elif win.rb_TEvar.get()==2:
                TE=np.genfromtxt([win.TEs_in.get()],delimiter=",")
                if np.size(TE,0)!=win.dyns:
                        status(win,"Provided number of TEs does not match number of dynamics...\n")
                        return None
                        
                for d in range(win.dyns):
                        for s in range(win.slcs):
                                TEs[int(win.slcs)*d+s]=s*win.TE_in.get()

        status(win,"These are the follwing echo times for each image:\n")
        status(win,TEs)
        status(win,"\n")
        return TEs

def save(win,dicomdir,images):
        status(win,"Saving maps in DICOM format... \n")
        rows=win.rows
        cols=win.cols
        slcs=win.slcs
        dyns=win.dyns
        for s in range(slcs):
                txt=("Saving slice %s \n" %(s+1))
                status(win,txt)
                #   saving DICOMs
                # T1 map
                images_T2=images[len(images)-slcs+s-1]
                images_T2.AcquisitionNumber=dyns+1
                images_T2.InstanceNumber=dyns*slcs+s+1
                T2_map=win.maps[0][s][:][:]
                images_T2.PixelData = np.reshape(T2_map,(cols*rows)).astype(np.uint16)
                images_T2.AcquisitionTime = str(float(images_T2.AcquisitionTime) + 0.1)
                images_T2.SmallestImagePixelValue = min(images_T2.PixelData)
                images_T2.LargestImagePixelValue = max(images_T2.PixelData)
                images_T2.SOPInstanceUID = ''.join([images_T2.SOPInstanceUID,".1"])
                images_T2.RescaleSlope = 1
                images_T2.RescaleIntercept = np.min(T2_map)
        ##        images_T1.SeriesDescription = "T1 result"
                
                file_out=os.path.join(dicomdir,"_Series_"+str(images_T2.SeriesNumber).zfill(3)+"_maps","T2_map_"+str(s+1).zfill(3)+".dcm")
                try:
                        os.makedirs(os.path.split(file_out)[0])
                except:
                        pass

                images_T2.save_as(file_out)
                    
                # T1_R^2
                images_T2_R2=images[len(images)-slcs+s-1]
                images_T2_R2.AcquisitionNumber=dyns+2
                images_T2_R2.InstanceNumber=(dyns+1)*slcs+s+1
                T2_R2=win.maps[1][s][:][:]
                images_T2_R2.PixelData = np.uint16(T2_R2.reshape(cols*rows)) # Adjust the multiplication and then the RescaleSlope field
                images_T2_R2.AcquisitionTime = str(float(images_T2_R2.AcquisitionTime) + 0.2)
                images_T2_R2.SmallestImagePixelValue = min(images_T2_R2.PixelData)
                images_T2_R2.LargestImagePixelValue = max(images_T2_R2.PixelData)
                images_T2_R2.SOPInstanceUID = ''.join([images_T2_R2.SOPInstanceUID,".2"])
                images_T2_R2.RescaleSlope = 1                                   # This should give you 100*R1, i.e. 99.55% => 99.55
##                images_T2_R2.RescaleIntercept = np.min(T2_R2)
                images_T2_R2.RescaleIntercept = 0
        ##        images_T2_R2.SeriesDescription = "Fit R2 value"

                file_out=os.path.join(dicomdir,"_Series_"+str(images_T2_R2.SeriesNumber).zfill(3)+"_maps","T2_GoF_map_"+str(s+1).zfill(3)+".dcm")
                images_T2_R2.save_as(file_out)
                    
                # T1_Variance
                images_T2_Var=images[len(images)-slcs+s-1]
                images_T2_Var.AcquisitionNumber=dyns+3
                images_T2_Var.InstanceNumber=(dyns+2)*slcs+s+1
                T2_var=win.maps[2][s][:][:]
                images_T2_Var.PixelData = np.uint16(10.*T2_var.reshape(cols*rows))
                images_T2_Var.AcquisitionTime = str(float(images_T2_Var.AcquisitionTime) + 0.3)
                images_T2_Var.SmallestImagePixelValue = min(images_T2_Var.PixelData)
                images_T2_Var.LargestImagePixelValue = max(images_T2_Var.PixelData)
                images_T2_Var.SOPInstanceUID = ''.join([images_T2_Var.SOPInstanceUID,".3"])
                images_T2_Var.RescaleSlope = 1./10
                images_T2_Var.RescaleIntercept = np.min(10*T2_var)
        ##        images_T2_Var.SeriesDescription = "T2 variance"

                file_out=os.path.join(dicomdir,"_Series_"+str(images_T2_Var.SeriesNumber).zfill(3)+"_maps","T2_Var_map_"+str(s+1).zfill(3)+".dcm")
                images_T2_Var.save_as(file_out)
                        
                # M0 map
                images_M0=images[len(images)-slcs+s-1]
                images_M0.AcquisitionNumber=dyns+4
                images_M0.InstanceNumber=(dyns+3)*slcs+s+1
                M0_map=win.maps[3][s][:][:]
                images_M0.PixelData = np.uint16(M0_map.reshape(cols*rows))
                images_M0.AcquisitionTime = str(float(images_M0.AcquisitionTime) + 0.4)
                images_M0.SmallestImagePixelValue = min(images_M0.PixelData)
                images_M0.LargestImagePixelValue = max(images_M0.PixelData)
                images_M0.SOPInstanceUID = ''.join([images_M0.SOPInstanceUID,".4"])
                images_M0.RescaleSlope = 1
##                images_M0.RescaleIntercept = np.min(M0_map)
                images_M0.RescaleIntercept = 0
        ##        images_M0.SeriesDescription = "M0 map"

                file_out=os.path.join(dicomdir,"_Series_"+str(images_M0.SeriesNumber).zfill(3)+"_maps","M0_map_"+str(s+1).zfill(3)+".dcm")
                images_M0.save_as(file_out)
                    
                # M0-Variance
                images_M0_Var=images[len(images)-slcs+s-1]
                images_M0_Var.AcquisitionNumber=dyns+5
                images_M0_Var.InstanceNumber=(dyns+4)*slcs+s+1
                M0_var=win.maps[4][s][:][:]
                images_M0_Var.PixelData = np.uint16(10.*M0_var.reshape(cols*rows))
                images_M0_Var.AcquisitionTime = str(float(images_M0_Var.AcquisitionTime) + 0.5)
                images_M0_Var.SmallestImagePixelValue = min(images_M0_Var.PixelData)
                images_M0_Var.LargestImagePixelValue = max(images_M0_Var.PixelData)
                images_M0_Var.SOPInstanceUID = ''.join([images_M0_Var.SOPInstanceUID,".5"])
                images_M0_Var.RescaleSlope = 1./10
##                images_M0_Var.RescaleIntercept = np.min(10.*M0_var)
                images_M0_Var.RescaleIntercept = 0
        ##        images_M0_Var.SeriesDescription = "M0 variance"
                
                file_out=os.path.join(dicomdir,"_Series_"+str(images_M0_Var.SeriesNumber).zfill(3)+"_maps","M0_Var_map_"+str(s+1).zfill(3)+".dcm")
                images_M0_Var.save_as(file_out)
        
        status(win,"DONE!!! \n")
