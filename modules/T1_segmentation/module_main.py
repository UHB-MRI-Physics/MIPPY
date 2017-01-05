from Tkinter import *
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
        print win.rows
        print win.cols
        print win.slcs
        print win.dyns
##        if 'PHILIPS' in images[0].Manufacturer.upper():
##                try:
##                        win.slcs=eval(images[-1][0x0028,0x0008].value)/eval(images[-1][0x2001,0x1081].value)
##                except:
##                        win.slcs=int(images[-1][0x2001,0x1018].value)
##                win.dyns=int(images[-1][0x2001,0x1081].value)
##        else:
##                win.slcs=images[-1].InstanceNumber/images[-1].AcquisitionNumber
##                win.dyns=images[-1].AcquisitionNumber

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
        except IndexError:
                resort_needed = False

        if resort_needed:
                sorted_images = []
                for d in range(win.dyns):
                        for s in range(win.slcs):
                                sorted_images.append(images[s*win.dyns+d])
                images=sorted_images

        # Create canvases
	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0,width=512,height=512,drawing_enabled=True)

	if not images[0].SeriesInstanceUID == images[-1].SeriesInstanceUID:
                win.multi=True
                win.imcanvas_GoF = MIPPYCanvas(win.imcanvases,bd=0,width=512,height=512,drawing_enabled=True)
                win.imcanvas_GoF.roi_mode='freehand'
                # Splitting into 2
                win.images_orig=[]
                win.images_GoF=[]
                for image in range(np.size(images)):
                        series = images[0].SeriesInstanceUID
                        if images[image].SeriesInstanceUID==series:
                                win.images_orig.append(images[image])
                        else:
                                win.images_GoF.append(images[image])
                # Create scroll bars
                csl_GoF=StringVar()
                csl_GoF.set(win.imcanvas_GoF.active)
                win.imcanvas_GoF.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
                win.csl_GoF = Label(win.imcanvases,textvariable=csl_GoF,width=3)
        else:
                win.multi=False
                
	win.imcanvas_seg = MIPPYCanvas(win.imcanvases,bd=0,width=512,height=512,drawing_enabled=True)

	win.imcanvas_orig.roi_mode='freehand'
	win.imcanvas_seg.roi_mode='freehand'

	# Create scroll bars
	csl_orig=StringVar()
        csl_orig.set(win.imcanvas_orig.active)
        csl_seg=StringVar()
        csl_seg.set(win.imcanvas_seg.active)
        cdyn_orig=StringVar()
        cdyn_orig.set("388")
        cdyn_seg=StringVar()
        cdyn_seg.set("388")
	win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        win.imcanvas_seg.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        #~ win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        #~ win.imcanvas_seg.img.scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        # Create info space for current dynamic/slice
        win.csl_orig = Label(win.imcanvases,textvariable=csl_orig,width=3)
        win.csl_seg = Label(win.imcanvases,textvariable=csl_seg,width=3)
        win.cdyn_orig = Label(win.imcanvases,textvariable=cdyn_orig,width=3)
        win.cdyn_seg = Label(win.imcanvases,textvariable=cdyn_seg,width=3)

        # Window layout
        win.imcanvas_orig.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nwes')
        win.imcanvas_orig.img_scrollbar.grid(row=0,column=2,sticky='ns')
        win.csl_orig.grid(row=1,column=2)
        if win.multi==True:
                win.imcanvas_GoF.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
                win.imcanvas_GoF.img_scrollbar.grid(row=0,column=5,sticky='ns')
                win.csl_GoF.grid(row=1,column=5)
                win.imcanvas_seg.grid(row=0,column=6,rowspan=2,columnspan=2,sticky='nwes')
                win.imcanvas_seg.img_scrollbar.grid(row=0,column=8,sticky='ns')
                win.csl_seg.grid(row=1,column=5)
        else:
                win.imcanvas_seg.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
                win.imcanvas_seg.img_scrollbar.grid(row=0,column=5,sticky='ns')
                win.csl_seg.grid(row=1,column=5)
        #~ win.scroll_dyn_orig.grid(row=2,column=0,sticky='we')
        #~ win.cdyn_orig.grid(row=2,column=1)
        #~ win.scroll_dyn_seg.grid(row=2,column=3,sticky='we')
        #~ win.cdyn_seg.grid(row=2,column=4)
        win.imcanvases.grid(row=0,column=0,sticky='nwes')

        # To resize the objects with the main window
        win.rowconfigure(0,weight=1)
        win.columnconfigure(0,weight=1)
        win.rowconfigure(1,weight=0)
        win.columnconfigure(1,weight=0)
        win.imcanvases.rowconfigure(0,weight=1)
        win.imcanvases.rowconfigure(1,weight=0)
        win.imcanvases.rowconfigure(2,weight=0)
        win.imcanvases.columnconfigure(0,weight=1)
        win.imcanvases.columnconfigure(1,weight=0)
        win.imcanvases.columnconfigure(2,weight=0)
        if win.multi==True:
                win.imcanvases.columnconfigure(3,weight=1)
                win.imcanvases.columnconfigure(4,weight=0)
                win.imcanvases.columnconfigure(5,weight=0)
                win.imcanvases.columnconfigure(6,weight=1)
                win.imcanvases.columnconfigure(7,weight=0)
                win.imcanvases.columnconfigure(8,weight=0)
        else:
                win.imcanvases.columnconfigure(3,weight=1)
                win.imcanvases.columnconfigure(4,weight=0)
                win.imcanvases.columnconfigure(5,weight=0)

        if win.multi==True:
                win.imcanvas_orig.load_images(win.images_orig)
                win.imcanvas_GoF.load_images(win.images_GoF)
        else:
                win.imcanvas_orig.load_images(images)
                

        # Create buttons
        win.buttons=Frame(win)

        win.l_T1min = Label(win.buttons, text="Min T1 [ms]: ")
        win.T1min_in=StringVar(win)
        win.T1min_in.set(0)
        win.b_T1min = Entry(win.buttons,textvariable=win.T1min_in,width=5)
        win.l_T1max = Label(win.buttons, text="Max T1 [ms]: ")
        win.T1max_in=StringVar(win)
        win.T1max_in.set(2000)
        win.b_T1max = Entry(win.buttons,textvariable=win.T1max_in,width=5)
        win.s_T1bar = Scale(win.buttons,from_=win.T1min_in.get(),to=win.T1max_in.get(),orient=HORIZONTAL)

        if win.multi==True:
                win.c_GoF_in=IntVar(win)
                win.c_GoF_in.set(1)
                win.c_GoF=Checkbutton(win.buttons,text="Include Goodness-of-Fit Maps",variable=win.c_GoF_in,state="enabled")
                if win.c_GoF_in.get()==1:
                        win.l_GoFmin = Label(win.buttons, text="Min GoF [%]: ")
                        win.GoFmin_in=StringVar(win)
                        win.GoFmin_in.set(0)
                        win.b_GoFmin = Entry(win.buttons,textvariable=win.GoFmin_in,width=4)
                        win.s_GoFbar = Scale(win.buttons,from_=win.GoFmin_in.get(),to=100)

        win.c_NonZero_in=IntVar(win)
        win.c_NonZero_in.set(1)
        win.c_NonZero=Checkbutton(win.buttons,text="Exclude zero values",variable=win.c_NonZero_in,state="enabled")

        win.b_ROI = Button(win.buttons, text="Analyse ROI", command=lambda:ROI_stats(win))

        win.b_Optim = Button(win.buttons, text="Optimise within ROI", command=lambda:search_min(win))
        
        # Window layout
        win.l_T1min.grid(row=0,column=0,sticky='nw')
        win.b_T1min.grid(row=0,column=1,sticky='nw')
        win.l_T1max.grid(row=1,column=0,sticky='nw')
        win.b_T1max.grid(row=1,column=1,sticky='nw')
        win.s_T1bar.grid(row=2,column=0,sticky='new')

        if win.multi==True:
                win.c_GoF.grid(row=3,column=0,sticky='nw',columnspan=4)
                if win.c_GoF_in.get()==1:
                        win.l_GoFmin.grid(row=4,column=0,sticky='nw')
                        win.b_GoFmin.grid(row=4,column=1,sticky='nw')
                        win.s_GoFbar.grid(row=5,column=0,sticky='new')

        win.c_NonZero.grid(row=6,column=0,sticky='sw')
        win.b_ROI.grid(row=7,column=0,sticky='sw')
        win.b_Optim.grid(row=7,column=1,sticky='se')
                            
        win.buttons.grid(row=0,column=1,sticky='news')

        # Resizing options
        win.buttons.rowconfigure(0,weight=0)
        win.buttons.rowconfigure(1,weight=0)
        win.buttons.rowconfigure(5,weight=1)
        win.buttons.columnconfigure(0,weight=0)
        win.buttons.columnconfigure(1,weight=0)

        # Message box
        win.message_box=Frame(win)

        win.b_message = Text(win.message_box,state='disabled',height=15,width=100)
        win.b_message_clear = Button(win.message_box, text="Clear", command=lambda:status_clear(win))

        # Window layout
        win.b_message.grid(row=0,column=0,columnspan=3,sticky='news')
        win.b_message_clear.grid(row=0,column=3,sticky='new')

        win.message_box.grid(row=1,column=0,sticky='nwes')

        # Resizing option
        win.message_box.rowconfigure(0,weight=0)
        win.rowconfigure(1,weight=0)

        # Run buttons
        win.run_buttons=Frame(win)

##        try:
##                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))
##        except Exception,win.Im4D:
##                status(win,"Multiple Series Detected...\n")
##                win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((np.size(images,0)/win.slcs,win.slcs,win.rows,win.cols))
                        
        win.b_run = Button(win.run_buttons, text="Recalculate Maps", command=lambda:segment(win))
        win.b_save = Button(win.run_buttons, text="Save Segmented T1 Maps", command=lambda:save(win,dicomdir,images))
        win.b_save_bin = Button(win.run_buttons, text="Save Binary ROI", command=lambda:save_bin(win,dicomdir,images))

        # Window layout
##        win.l_threshold.grid(row=0,column=0,sticky='ne')
##        win.b_threshold.grid(row=0,column=1,sticky='ne')
##        win.l_GoF.grid(row=0,column=2,sticky='ne')
##        win.b_GoF.grid(row=0,column=3,sticky='ne')
        win.b_run.grid(row=0,column=0,sticky='nw')
        win.b_save_bin.grid(row=1,column=0,sticky='nw')        
        win.b_save.grid(row=2,column=0,sticky='nw')

        win.run_buttons.grid(row=1,column=1,sticky="news")
        
	return

def segment(win):
        current_slice=int(win.imcanvas_seg.active)
        win.Im3Dseg=win.imcanvas_orig.get_3d_array()*(win.imcanvas_orig.get_3d_array()>=float(win.T1min_in.get()))*(win.imcanvas_orig.get_3d_array()<=float(win.T1max_in.get()))
        #quick_display(win.imcanvas_orig.get_3d_array(),win)
        if win.multi==True:
                win.Im3Dseg=win.Im3Dseg*(win.imcanvas_GoF.get_3d_array()>=float(win.GoFmin_in.get()))
        #quick_display(win.Im3Dseg,win)

        win.imcanvas_seg.load_images([b for b in (win.Im3Dseg)])
        win.imcanvas_seg.show_image(current_slice)
        return

def ROI_stats(win):
        try:
                if win.c_NonZero_in.get()==0:
                        win.pix_seg=np.array(win.imcanvas_seg.get_roi_pixels())
                else:
                        win.pix_seg=np.array(win.imcanvas_seg.get_roi_pixels())
                        win.pix_seg=win.pix_seg[np.where(win.pix_seg>0)]

                status(win,'Segmented ROI stats: mean=',np.round(np.mean(win.pix_seg),1),' std=',np.round(np.std(win.pix_seg)+0.05,1),
                               ' min=',np.round(np.amin(win.pix_seg),1),' max=',np.round(np.amax(win.pix_seg),1),' area=',np.size(win.pix_seg),'px')
        except:
                pass
        try:
                if win.c_NonZero_in.get()==0:
                        pix=np.array(win.imcanvas_GoF.get_roi_pixels())
                else:
                        pix=np.array(win.imcanvas_GoF.get_roi_pixels())
                        pix=pix[np.where(pix>0)]
                
                status(win,'GoF ROI stats: mean=',np.round(np.mean(pix),1),' std=',np.round(np.std(pix)+0.05,1),
                               ' min=',np.round(np.amin(pix),1),' max=',np.round(np.amax(pix),1),' area=',np.size(pix),'px')
        except:
                pass
        try:
                if win.c_NonZero_in.get()==0:
                        pix=win.imcanvas_orig.get_roi_pixels()
                else:
                        pix=np.asarray(win.imcanvas_orig.get_roi_pixels())
                        pix=pix[np.where(pix>0)]
    
                status(win,'T1 ROI stats: mean=',np.round(np.mean(pix),1),' std=',np.round(np.std(pix)+0.05,1),
                               ' min=',np.round(np.amin(pix),1),' max=',np.round(np.amax(pix),1),' area=',np.size(pix),'px')
        except:
                pass
        return
                                
def search_min(win):
        win.pix_seg0=np.size(win.pix_seg)
        T1min_t=int(win.T1min_in.get())
        T1max_t=int(win.T1max_in.get())
        T1range=np.array([T1min_t,T1max_t])
        results = minimize(extract_pix,T1range,args=(win),method='Nelder-Mead')
        #win.T1min_in.set(T1min_t)
        #win.T1max_in.set(T1max_t)
        status(win,'Optimisation results = ',results)
        return

def extract_pix(T1range,win):
        win.T1min_in.set(str(int(T1range[0])))
        win.T1max_in.set(str(int(T1range[1])))
##        current_slice=int(win.imcanvas_seg.active)
        segment(win)
##        win.imcanvas_seg.show_image(current_slice)
        ROI_stats(win)
        eval_fun = np.std(win.pix_seg)**1/(100*float(np.size(win.pix_seg+1)/float(win.pix_seg0+1))**1)
        #status(win,eval_fun)
        if np.size(win.pix_seg)<0.5*win.pix_seg0:
            eval_fun = 10000
        return eval_fun


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

def save(win,dicomdir,images):
        status(win,"Saving maps in DICOM format...")
        rows=win.rows
        cols=win.cols
        slcs=win.slcs
        dyns=win.dyns
        for s in range(slcs):
                txt=("Saving slice %s " %(s+1))
                status(win,txt)
                #   saving DICOMs
                # T1 map
                images_T1seg=images[len(images)-slcs+s-1]
                images_T1seg.AcquisitionNumber=dyns+1
                images_T1seg.InstanceNumber=dyns*slcs+s+1
                T1map_seg=np.clip(win.Im3Dseg[s][:][:],0,2**16).astype(np.uint16)
                images_T1seg.PixelData = np.reshape(T1map_seg,(cols*rows))
                try:
                        images_T1seg.AcquisitionTime = str(float(images_T1seg.AcquisitionTime) + 0.1)
                except AttributeError:
                        pass
                try:
                        images_T1seg.SmallestImagePixelValue = min(images_T1seg.PixelData)
                        images_T1seg[0x0028,0x0106].VR='US'
                        images_T1seg.LargestImagePixelValue = max(images_T1seg.PixelData)
                        images_T1seg[0x0028,0x0107].VR='US'
                except:
                        pass
                images_T1seg.SOPInstanceUID = ''.join([images_T1seg.SOPInstanceUID,".1"])
                images_T1seg.RescaleSlope = 1
                images_T1seg.RescaleIntercept = 0
                images_T1seg.WindowCentre = 1000
                images_T1seg.WindowWidth = 1000

                try:
                        images_T1seg[0x2005,0x100E].value = 1
                except:
                        pass
                images_T1seg.SeriesDescription = images[0].SeriesDescription+"_seg"
                images_T1seg.SeriesInstanceUID = images[0].SeriesInstanceUID+".1"
                
                file_out=os.path.join(dicomdir,"_Series_"+str(images_T1seg.SeriesNumber).zfill(3)+"_maps","T1map_seg_"+str(s+1).zfill(3)+".dcm")
                print file_out
                try:
                        os.makedirs(os.path.split(file_out)[0])
                except:
                        pass

                images_T1seg.save_as(file_out)
        
        status(win,"DONE!!!")
        
def save_bin(win,dicomdir,images):
        status(win,"Saving binary ROI in DICOM format...")
        rows=win.rows
        cols=win.cols
        slcs=win.slcs
        dyns=win.dyns
        win.pix_bin=win.imcanvas_seg.get_roi_mask().astype(np.float64)*win.imcanvas_seg.get_active_image().px_float
        try:
                win.pix_bin[np.where(win.pix_bin>0)]=1
                win.pix_bin=win.pix_bin.astype(np.uint8)               
        except:
                status(win,"No segmented ROI selected for this slice!")
                return

        
##        for s in range(slcs):
        s=int(win.imcanvas_seg.active)
        txt=("Saving slice %s " %(s))
        status(win,txt)
        #   saving DICOMs
        # Binary ROI
        images_ROIbin=images[len(images)-slcs+s-1]
        images_ROIbin.AcquisitionNumber=dyns+10
        images_ROIbin.InstanceNumber=dyns*slcs+s+10
        win.pix_bin=np.clip(win.pix_bin[:][:],0,1).astype(np.uint16)
        images_ROIbin.PixelData = np.reshape(win.pix_bin,(cols*rows))
        try:
                images_ROIbin.AcquisitionTime = str(float(images_ROIbin.AcquisitionTime) + 0.2)
        except AttributeError:
                pass
        try:
                images_ROIbin.SmallestImagePixelValue = min(images_ROIbin.PixelData)
                images_ROIbin[0x0028,0x0106].VR='US'
                images_ROIbin.LargestImagePixelValue = max(images_ROIbin.PixelData)
                images_ROIbin[0x0028,0x0107].VR='US'
        except:
                pass
        images_ROIbin.SOPInstanceUID = ''.join([images_ROIbin.SOPInstanceUID,".1.1"])
        images_ROIbin.RescaleSlope = 1
        images_ROIbin.RescaleIntercept = 0
        images_ROIbin.WindowCentre = 0.5
        images_ROIbin.WindowWidth = 0.5

        try:
                images_ROIbin[0x2005,0x100E].value = 1
        except:
                pass
        images_ROIbin.SeriesDescription = images[0].SeriesDescription+"_ROIbin"
        images_ROIbin.SeriesInstanceUID = images[0].SeriesInstanceUID+".1.1"
        
        file_out=os.path.join(dicomdir,"_Series_"+str(images_ROIbin.SeriesNumber).zfill(3)+"_maps","ROIbin_"+str(s).zfill(3)+".dcm")
        print file_out
        try:
                os.makedirs(os.path.split(file_out)[0])
        except:
                pass

        images_ROIbin.save_as(file_out)
        
        status(win,"DONE!!!")
