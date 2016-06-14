from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
from image_registration import image_registration as im_reg
import time

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
        win.slcs=images[-1].InstanceNumber/images[-1].AcquisitionNumber
        win.dyns=images[-1].AcquisitionNumber
        
	# Create canvases
	win.imcanvases=Frame(win)
	win.imcanvas_orig = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)
	win.imcanvas_align = MIPPYCanvas(win.imcanvases,bd=0 ,width=384,height=384,drawing_enabled=False)
	
	# Create scroll bars
	csl_orig=StringVar()
        csl_orig.set(win.imcanvas_orig.active)
        csl_align=StringVar()
        csl_align.set(win.imcanvas_align.active)
        cdyn_orig=StringVar()
        cdyn_orig.set("388")
        cdyn_align=StringVar()
        cdyn_align.set("4")
	win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        win.imcanvas_align.img_scrollbar = Scrollbar(win.imcanvases,orient='vertical')
        #~ win.imcanvas_orig.img_scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        #~ win.imcanvas_align.img.scrollbar = Scrollbar(win.imcanvases,orient='horizontal')
        # Create info space for current dynamic/slice
        win.csl_orig = Label(win.imcanvases,textvariable=csl_orig,width=3)
        win.csl_align = Label(win.imcanvases,textvariable=csl_align,width=3)
        win.cdyn_orig = Label(win.imcanvases,textvariable=cdyn_orig,width=3)
        win.cdyn_align = Label(win.imcanvases,textvariable=cdyn_align,width=3)
        
        # Window layout
        win.imcanvas_orig.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nwes')
        win.imcanvas_orig.img_scrollbar.grid(row=0,column=2,sticky='ns')
        win.csl_orig.grid(row=1,column=2)
        win.imcanvas_align.grid(row=0,column=3,rowspan=2,columnspan=2,sticky='nwes')
        win.imcanvas_align.img_scrollbar.grid(row=0,column=5,sticky='ns')
        win.csl_align.grid(row=1,column=5)
        #~ win.scroll_dyn_orig.grid(row=2,column=0,sticky='we')
        #~ win.cdyn_orig.grid(row=2,column=1)
        #~ win.scroll_dyn_align.grid(row=2,column=3,sticky='we')
        #~ win.cdyn_align.grid(row=2,column=4)
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

        win.l_reference = Label(win.buttons, text="Reference Image:")
        win.ref = StringVar(win)
        win.ref.set("Dynamic Number")
        win.b_reference = OptionMenu(win.buttons,win.ref,"Dynamic Number","Average Image")
        win.ref_in = StringVar(win)
        win.ref_in.set(1)
        win.l_ref_in = Label(win.buttons, text="Ref.#:", width=5)
        win.b_ref_in = Entry(win.buttons,textvariable=win.ref_in,width=4)
        # win.buttons.bind(win.ref.get()=="Average Image",win.b_ref_in.configure(state="disabled"))
        # win.buttons.pack()
        # win.b_ref_in.bind(win.ref.get()=="Dynamic Number",win.b_ref_in.configure(state="normal"))

        win.l_method=Label(win.buttons,text="Optimisation Method:")
        win.method = StringVar(win)
        win.method.set("L-BFGS-B")
        win.b_method = OptionMenu(win.buttons,win.method,
                                  "Nelder-Mead","Powell","CG","BFGS","Newton-CG","L-BFGS-B","TNC","COBYLA","SLSQP","dogleg","trust-ncg")

        win.l_tolerance=Label(win.buttons,text="Optimisation Tolerance:")
        win.tol_in=StringVar(win)
        win.tol_in.set(0.001)
        win.b_tol_in=Entry(win.buttons,textvariable=win.tol_in,width=6)

        win.l_maxiter=Label(win.buttons,text="Maximum Iteration:")
        win.maxiter_in=StringVar(win)
        win.maxiter_in.set(100)
        win.b_maxiter_in=Entry(win.buttons,textvariable=win.maxiter_in,width=6)

        win.l_edges=Label(win.buttons,text="% contribution:")
        win.c_edges_in=IntVar(win)
        win.c_edges=Checkbutton(win.buttons,text="Use Edges",variable=win.c_edges_in)
        win.edges_in=IntVar(win)
        win.edges_in.set(0)
        win.b_edges_in = Entry(win.buttons,textvariable=win.edges_in,width=3)
        
        win.c_2D_in=IntVar(win)
        win.c_2D_in.set(1)
        win.c_2D=Checkbutton(win.buttons,text="2D-realignment",variable=win.c_2D_in)

        
        # Window layout
        win.l_reference.grid(row=0,column=0,sticky='nw')
        win.b_reference.grid(row=1,column=0,sticky='nw')
        win.l_ref_in.grid(row=0,column=1,sticky='nw')
        win.b_ref_in.grid(row=1,column=1,sticky='nw')        
        win.l_method.grid(row=2,column=0,sticky='nw')
        win.b_method.grid(row=3,column=0, sticky='nw')
        win.l_tolerance.grid(row=4,column=0, sticky='nw')
        win.b_tol_in.grid(row=4,column=1,sticky='nw')
        win.l_maxiter.grid(row=5,column=0,sticky='nw')
        win.b_maxiter_in.grid(row=5,column=1,sticky='nw')
        win.c_edges.grid(row=6,column=0,sticky='nw')
        win.l_edges.grid(row=7,column=0,sticky='ne')
        win.b_edges_in.grid(row=7,column=1,sticky='nw')
        win.c_2D.grid(row=8,column=0,sticky='nw')
                            
        win.buttons.grid(row=0,column=1,sticky='new')

        # Resizing options
        win.buttons.rowconfigure(0,weight=0)
        win.buttons.rowconfigure(1,weight=0)
        win.buttons.columnconfigure(0,weight=0)
        win.buttons.columnconfigure(1,weight=0)

        # Message box
        win.message_box=Frame(win)

        win.b_message = Text(win.message_box,state='disabled',height=6)

        # Window layout
        win.b_message.grid(row=0,column=0,sticky='news')

        win.message_box.grid(row=1,column=0,sticky='wes')

        # Resizing option
        win.message_box.rowconfigure(0,weight=1)

        # Run buttons
        win.run_buttons=Frame(win)

        win.Im4D=np.array([a.px_float for a in win.imcanvas_orig.images]).reshape((win.dyns,win.slcs,win.rows,win.cols))
        win.b_run = Button(win.run_buttons, text="Realign", command=lambda:realign(win))
        win.b_save = Button(win.run_buttons, text="Save", command=lambda:save(win,dicomdir,images))

        # Window layout
        win.b_run.grid(row=0,column=0,sticky='new')
        win.b_save.grid(row=1,column=0,sticky='new')

        win.run_buttons.grid(row=1,column=1,sticky="new")
        
	return
	
def close_window(window):
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

def realign(win):
        status_clear(win)
        status(win,"Checking parameters... \n") 
        if win.ref.get()==True:
                try:
                        start_time=time.time()
                        win.Im4D_align,win.trans=im_reg(win.Im4D,ref_av=win.ref.get(),min_method=win.method.get(),
                                                        tolerance=float(win.tol_in.get()),
                                                        max_iter=int(win.maxiter_in.get()),
                                                        edge=win.edges_in.get(),
                                                        2D=win.c_2D_in.get())
                except TypeError:
                        start_time=time.time()
                        status(win,"Incorrect Optimisation Method for this data-set! \n")
                        status(win,"Trying to recover with the default method... \n")
                        win.Im4D_align,win.trans=im_reg(win.Im4D,ref_av=win.ref.get(),
                                                        tolerance=float(win.tol_in.get()),
                                                        max_iter=int(win.maxiter_in.get()),
                                                        edge=win.edges_in.get(),
                                                        2D=win.c_2D_in.get())                                
        else:
                try:
                        start_time=time.time()
                        win.Im4D_align,win.trans=im_reg(win.Im4D,ref=int(win.ref_in.get()),
                                                        min_method=win.method.get(),
                                                        tolerance=float(win.tol_in.get()),
                                                        max_iter=int(win.maxiter_in.get()),
                                                        edge=win.edges_in.get(),
                                                        2D=win.c_2D_in.get())
                except TypeError:
                        start_time=time.time()
                        status(win,"Incorrect Optimisation Method for this data-set! \n")
                        status(win,"Trying to recover with the default method... \n")
                        win.Im4D_align,win.trans=im_reg(win.Im4D,ref=int(win.ref_in.get()),
                                                        tolerance=float(win.tol_in.get()),
                                                        max_iter=int(win.maxiter_in.get()),
                                                        edge=win.edges_in.get(),
                                                        2D=win.c_2D_in.get())

        run_time = time.time()-start_time
        
        if run_time>=60:
                txt=("fitting time for all dynamics was %s minutes and %s seconds \n" %(int(run_time/60),int(run_time-int(run_time/60)*60)) )
        else:
                txt=("fitting time for all dynamics was %s seconds \n" %(int(run_time)) )
                
        status(win,txt)
        
#        win.Im4D_align,win.trans=im_reg(win.Im4D,min_method=win.method.get(),
#                                        tolerance=win.tol_in.get(),max_iter=win.maxiter_in.get())
        win.Im3D_align=np.reshape(win.Im4D_align,(win.dyns*win.slcs,win.rows,win.cols))
        win.imcanvas_align.load_images([b for b in win.Im3D_align])
        status(win,"DONE!!!\n")
        return

def save(win,dicomdir,images):
        status(win,"Saving files... \n")
##        win.Im3D_align=np.reshape(win.Im4D_align,(win.dyns*win.slcs,win.rows,win.cols))
        dicomdir_out=os.path.join(dicomdir,"realignment")
        if not os.path.exists(dicomdir_out):
                os.makedirs(dicomdir_out)
        for s in range(len(images)):
                images_out=images[s]
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
                        
                images_out.SeriesDescription=''.join([images_out.SeriesDescription,"r"])
                images_out.PixelData = np.clip(((win.Im3D_align[s,:,:].reshape(win.cols*win.rows)-ri)/rs),0,np.max(win.Im3D_align)).astype(np.uint16)
                images_out.SOPInstanceUID = ''.join([images_out.SOPInstanceUID,".1"])
                images_out.SeriesInstanceUID = ''.join([images_out.SeriesInstanceUID,".1"])

                file_out=os.path.join(dicomdir_out,"im_realigned"+str(s+1).zfill(3)+".dcm")
                images_out.save_as(file_out)
        np.savetxt(os.path.join(dicomdir_out,"trans_mat.txt"),win.trans)        
        print "Saved "+str(s+2)+" files in:", \
              dicomdir_out
        print win
        return
