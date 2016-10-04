from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
from T1_mapping import T1_mapping as T1map
import time
import datetime
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
        if 'PHILIPS' in images[0].Manufacturer.upper():
                print images[0]
                try:
                        win.slcs=eval(images[-1][0x0028,0x0008].value)/eval(images[-1][0x2001,0x1081].value)
                except:
                        win.slcs=int(images[-1][0x2001,0x1018].value)
                        print "number of slices = "+str(win.slcs)
                win.dyns=int(images[-1][0x2001,0x1081].value)
        else:
                win.slcs=images[-1].InstanceNumber/images[-1].AcquisitionNumber
                win.dyns=images[-1].AcquisitionNumber
        
        # Create canvases
	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)
	win.imcanvas_maps = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)

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

        win.rb_TIvar = IntVar()
        win.rb_TIvar.set(1)
        win.rb_TI = Radiobutton(win.buttons, text="Set Initial TI and Increment", variable=win.rb_TIvar, value=1, command=lambda:hide_TIs(win))
        win.l_TI = Label(win.buttons, text="Initial TI [ms]: ")
        win.TI_in=StringVar(win)
        win.TI_in.set(100)
        win.b_TI = Entry(win.buttons,textvariable=win.TI_in,width=4)
        win.l_TIinc = Label(win.buttons, text="TI Increment [ms]: ")
        win.TIinc_in=StringVar(win)
        win.TIinc_in.set(100)
        win.b_TIinc = Entry(win.buttons,textvariable=win.TIinc_in,width=4)
        
        win.rb_TIs = Radiobutton(win.buttons, text="Set Individual TIs (comma-separated) [ms]:", variable=win.rb_TIvar, value=2, command=lambda:hide_TI(win))
        win.TIs_in=StringVar(win)
        win.b_TIs = Entry(win.buttons,textvariable=win.TIs_in,width=30,state="disabled")
        
        win.rb_TAvar = IntVar()
        win.rb_TAvar.set(1)
        win.rb_TAauto = Radiobutton(win.buttons, text="Set TA automatically from the DICOM header", variable=win.rb_TAvar, value=1, command=lambda:hide_TA(win))

        win.rb_TA = Radiobutton(win.buttons, text="Set TA manually [ms]:", variable=win.rb_TAvar, value=2, command=lambda:show_TA(win))
        win.TA_in=StringVar(win)
        win.TA_in.set(65)
        win.b_TA = Entry(win.buttons,textvariable=win.TA_in,width=4,state="disabled")

        win.c_rev_in=IntVar(win)
        win.c_rev_in.set(0)
        win.c_rev=Checkbutton(win.buttons,text="Use Reversed Aquisition",variable=win.c_rev_in)
        
        # Window layout
        win.rb_TI.grid(row=0,column=0,sticky='nw',columnspan=4)
        win.l_TI.grid(row=1,column=0,sticky='nw')
        win.b_TI.grid(row=1,column=1,sticky='nw')
        win.l_TIinc.grid(row=1,column=2,sticky='nw')
        win.b_TIinc.grid(row=1,column=3,sticky='nw')
        win.rb_TIs.grid(row=2,column=0,sticky='nw',columnspan=4)
        win.b_TIs.grid(row=3,column=0,sticky='nw',columnspan=3)
        
        win.rb_TAauto.grid(row=4,column=0,sticky='sw',rowspan=2,columnspan=4)
        win.rb_TA.grid(row=6,column=0,sticky='nw',columnspan=2)
        win.b_TA.grid(row=6,column=2,sticky='nw')

        win.c_rev.grid(row=8,column=0,sticky='nw',columnspan=4)
                            
        win.buttons.grid(row=0,column=1,sticky='new')

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

##        test_time_s=time.time()
##        test=numpy.matlib.repmat(images[0],win.dyns*win.slcs,1).astype(Dataset)
##        test_time_e=time.time()-test_time_s
##        print type(test[0])
##        test[10].TemporalPositionIdentifier=1000
##        print test[:,10].TemporalPositionIdentifier
##        print test[:,0].TemporalPositionIdentifier
##
##        print("repmat in %s [s]\n" %(test_time_e))
##
##        test_time_s=time.time()
##        test=deepcopy(images[0])
##        test_time_e=time.time()-test_time_s
##
##        print("deepcopy in %s [s]\n" %(test_time_e))
        try:
                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))
        except Exception,win.Im4D:
                status(win,"Multiple Series Detected...\nRecommended Reversed Acquisition\n")
                win.c_rev_in.set(1)
                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((np.size(images,0)/win.slcs,win.slcs,win.rows,win.cols))
        win.b_run = Button(win.run_buttons, text="Create T1 maps", command=lambda:T1_map(win,images))
        win.b_save = Button(win.run_buttons, text="Save T1 maps", command=lambda:save(win,dicomdir,images))

        # Window layout
        win.b_run.grid(row=0,column=0,sticky='new')
        win.b_save.grid(row=1,column=0,sticky='new')

        win.run_buttons.grid(row=1,column=1,sticky="new")
        
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

def hide_TIs(win):
        """Greys out Initial TIs window"""
        if win.rb_TIvar.get()==1:
                win.b_TI.configure(state="normal")
                win.b_TIinc.configure(state="normal")
                win.b_TIs.configure(state="disabled")
                win.b_TI.focus()
        return

def hide_TI(win):
        """Greys out Initial TI and ITinc windows"""
        if win.rb_TIvar.get()==2:
                win.b_TI.configure(state="disabled")
                win.b_TIinc.configure(state="disabled")
                win.b_TIs.configure(state="normal")
                win.b_TIs.focus()
        return

def hide_TA(win):
        """Greys out Initial TA window"""
        if win.rb_TAvar.get()==1:
                win.b_TA.configure(state="disabled")
                win.rb_TA.focus()
        return

def show_TA(win):
        """Activates the TA windows"""
        if win.rb_TAvar.get()==2:
                win.b_TA.configure(state="normal")
                win.b_TA.focus()
        return
def T1_map(win,images):
        """Creating maps - T1_mapping.py script"""
        status_clear(win)
        win.TIs=sort_TIs(win,images)
        
        if win.TIs==None:
                return
        status(win,"Fitting T1 maps...\n")
        start_time=time.time()
        win.maps=np.zeros((5,win.slcs,win.rows,win.cols))
        win.maps=T1map(win.Im4D,win.TIs,images,rev=False)
        
        run_time = time.time()-start_time

        if run_time>=60:
                txt=("Fitting completed in %s minutes and %s seconds. \n" %(int(run_time/60),int(run_time-int(run_time/60)*60)) )
        else:
                txt=("Fitting completed in %s seconds. \n" %(int(np.ceil(run_time))) )
        status(win,txt)        
        test=win.maps[0]
#        quick_display(win,test)
        win.imcanvas_maps.load_images([b for b in (np.reshape(win.maps,(5*win.slcs,win.rows,win.cols)) )])
                
        return
def time_convert(win,t):
        h=str(t)[0:2]
        m=str(t)[2:4]
        s=str(t)[4:6]
        hms=int()

def sort_TIs(win,images):
        """Sorting TIs for each individual image"""
        status(win,"Sorting TIs for each individual image... \n")
        TA=np.zeros(win.slcs-1)
        TIs=np.zeros(win.dyns*win.slcs)
        if win.rb_TAvar.get()==1:
                for a in range(win.slcs-1):
                        tst_a = str(images[a].AcquisitionTime)
                        tst_b = str(images[a+1].AcquisitionTime)
                        dst = str(images[a].StudyDate)
 
                        time_a = datetime.datetime(int(dst[0:4]),int(dst[4:6]),int(dst[6:8]),int(tst_a[0:2]),int(tst_a[2:4]),int(tst_a[4:6]),int(tst_a[7:]))
                        time_b = datetime.datetime(int(dst[0:4]),int(dst[4:6]),int(dst[6:8]),int(tst_b[0:2]),int(tst_b[2:4]),int(tst_b[4:6]),int(tst_b[7:]))
 
                        TA[a] = (time_b-time_a).total_seconds()*1000
                     
                TAav=int(np.mean(TA,0))
                win.TA_in.set(abs(int(TAav)))
                txt=("Estimated TA is %s [ms]\n" %(win.TA_in.get()))
                status(win,txt)
        if win.TA_in.get()>0:
                if win.rb_TIvar.get()==1:
                        for d in range(win.dyns):
                                for s in range(win.slcs):
                                        TIs[int(win.slcs)*d+s]=int(win.TI_in.get())+d*int(win.TIinc_in.get())+s*int(win.TA_in.get())
                elif win.rb_TIvar.get()==2:
                        TI=np.genfromtxt([win.TIs_in.get()],delimiter=",")
                        if np.size(TI,0)!=win.dyns:
                                status(win,"Provided number of TIs does not match number of dynamics...\n"
                                       +"number of dynamics = "+str(win.dyns))
                                return None
                        
                        for d in range(win.dyns):
                                for s in range(win.slcs):
                                        TIs[int(win.slcs)*d+s]=TI[d]+s*int(win.TA_in)
        elif win.TA_in.get()<0:
                if win.rb_TIvar.get()==1:
                        for d in range(win.dyns):
                                for s in range(win.slcs):
                                        TIs[int(win.slcs)*d+s]=int(win.TI_in.get())+d*int(win.TIinc_in.get())+(win.slcs-s-1)*int(win.TA_in.get())
                elif win.rb_TIvar.get()==2:
                        TI=np.genfromtxt([win.TIs_in.get()],delimiter=",")
                        if np.size(TI,0)!=win.dyns:
                                status(win,"Provided number of TIs does not match number of dynamics...\n")
                                return None
                        
                        for d in range(win.dyns):
                                for s in range(win.slcs):
                                        TIs[int(win.slcs)*d+s]=TI[d]+(win.slcs-s-1)*win.TA_in

        status(win,"These are the follwing times for each image:\n")
        status(win,TIs)
        status(win,"\n")
        return TIs

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
                images_T1=images[len(images)-slcs+s-1]
                images_T1.AcquisitionNumber=dyns+1
                images_T1.InstanceNumber=dyns*slcs+s+1
                T1_map=win.maps[0][s][:][:]
                images_T1.PixelData = np.reshape(T1_map,(cols*rows)).astype(np.uint16)
                images_T1.AcquisitionTime = str(float(images_T1.AcquisitionTime) + 0.1)
                images_T1.SmallestImagePixelValue = min(images_T1.PixelData)
                images_T1.LargestImagePixelValue = max(images_T1.PixelData)
                images_T1.SOPInstanceUID = ''.join([images_T1.SOPInstanceUID,".1"])
                images_T1.RescaleSlope = 1
                images_T1.RescaleIntercept = np.min(T1_map)
        ##        images_T1.SeriesDescription = "T1 result"
                
                file_out=os.path.join(dicomdir,"_Series_"+str(images_T1.SeriesNumber).zfill(3)+"_maps","T1_map_"+str(s+1).zfill(3)+".dcm")
                try:
                        os.makedirs(os.path.split(file_out)[0])
                except:
                        pass

                images_T1.save_as(file_out)
                    
                # T1_R^2
                images_T1_R2=images[len(images)-slcs+s-1]
                images_T1_R2.AcquisitionNumber=dyns+2
                images_T1_R2.InstanceNumber=(dyns+1)*slcs+s+1
                T1_R2=win.maps[1][s][:][:]
                images_T1_R2.PixelData = np.uint16(T1_R2.reshape(cols*rows)) # Adjust the multiplication and then the RescaleSlope field
                images_T1_R2.AcquisitionTime = str(float(images_T1_R2.AcquisitionTime) + 0.2)
                images_T1_R2.SmallestImagePixelValue = min(images_T1_R2.PixelData)
                images_T1_R2.LargestImagePixelValue = max(images_T1_R2.PixelData)
                images_T1_R2.SOPInstanceUID = ''.join([images_T1_R2.SOPInstanceUID,".2"])
                images_T1_R2.RescaleSlope = 1                                   # This should give you 100*R1, i.e. 99.55% => 99.55
##                images_T1_R2.RescaleIntercept = np.min(T1_R2)
                images_T1_R2.RescaleIntercept = 0
        ##        images_T1_R2.SeriesDescription = "Fit R2 value"

                file_out=os.path.join(dicomdir,"_Series_"+str(images_T1_R2.SeriesNumber).zfill(3)+"_maps","T1_GoF_map_"+str(s+1).zfill(3)+".dcm")
                images_T1_R2.save_as(file_out)
                    
                # T1_Variance
                images_T1_Var=images[len(images)-slcs+s-1]
                images_T1_Var.AcquisitionNumber=dyns+3
                images_T1_Var.InstanceNumber=(dyns+2)*slcs+s+1
                T1_var=win.maps[2][s][:][:]
                images_T1_Var.PixelData = np.uint16(10.*T1_var.reshape(cols*rows))
                images_T1_Var.AcquisitionTime = str(float(images_T1_Var.AcquisitionTime) + 0.3)
                images_T1_Var.SmallestImagePixelValue = min(images_T1_Var.PixelData)
                images_T1_Var.LargestImagePixelValue = max(images_T1_Var.PixelData)
                images_T1_Var.SOPInstanceUID = ''.join([images_T1_Var.SOPInstanceUID,".3"])
                images_T1_Var.RescaleSlope = 1./10
                images_T1_Var.RescaleIntercept = np.min(10*T1_var)
        ##        images_T1_Var.SeriesDescription = "T1 variance"

                file_out=os.path.join(dicomdir,"_Series_"+str(images_T1_Var.SeriesNumber).zfill(3)+"_maps","T1_Var_map_"+str(s+1).zfill(3)+".dcm")
                images_T1_Var.save_as(file_out)
                        
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
