from tkinter import *
from tkinter.ttk import *
import tkinter.messagebox
from mippy.viewing import *
import os
from PIL import Image,ImageTk
import platform
from pkg_resources import resource_filename

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


def execute(master_window,instance_info,images):
        print("Module loaded...")
        print("Received "+str(len(images))+" image datasets.")
        print(os.getcwd())
        #~ icondir = os.path.join(os.getcwd(),'source','images')


        # This is to fix backwards compatibility for anywhere the old dicomdir object
        # was used
        dicomdir = instance_info['image_directory']
    
        window = Toplevel(master_window)
        window.instance_info = instance_info
        window.title("{} {}: {}".format(window.instance_info['module_name'],window.instance_info['mippy_version'],window.instance_info['module_instance']))
        # Create canvas
        if platform.system()=='Linux':
                canvas_size=320
        else:
                canvas_size=512
        window.imcanvas = MIPPYCanvas(window,bd=0,width=canvas_size,height=canvas_size,drawing_enabled=True)
        # Open icons for button
        sq_im = resource_filename('mippy','resources/square_roi.png')
        el_im = resource_filename('mippy','resources/ellipse_roi.png')
        fr_im = resource_filename('mippy','resources/freehand_roi.png')
        li_im = resource_filename('mippy','resources/line_roi.png')
        window.roi_sq_im = ImageTk.PhotoImage(file=sq_im)
        window.roi_el_im = ImageTk.PhotoImage(file=el_im)
        window.roi_fr_im = ImageTk.PhotoImage(file=fr_im)
        window.roi_li_im = ImageTk.PhotoImage(file=li_im)

        window.toolbar=Frame(window)

        window.roi_square_button = Button(window.toolbar,text="Draw square ROI",command=lambda:window.imcanvas.draw_rectangle_roi(),image=window.roi_sq_im)
        window.roi_ellipse_button = Button(window.toolbar,text="Draw elliptical ROI",command=lambda:window.imcanvas.draw_ellipse_roi(),image=window.roi_el_im)
        window.roi_polygon_button = Button(window.toolbar,text="Draw freehand ROI", command=lambda:window.imcanvas.draw_freehand_roi(),image=window.roi_fr_im)
        window.roi_line_button = Button(window.toolbar,text="Draw line",command=lambda:window.imcanvas.draw_line_roi(),image=window.roi_li_im)
        window.roi_square_button.config(pad=2)
        window.roi_ellipse_button.config(pad=2)
        window.roi_polygon_button.config(pad=2)
        window.roi_line_button.config(pad=2)
        #~ window.scrollbutton = Button(window, text="SLICE + / -")
        window.imcanvas.img_scrollbar = Scrollbar(window,orient='horizontal')
        window.imcanvas.configure_scrollbar()
        window.statsbutton = Button(window,text="Get ROI statistics",command=lambda:get_stats(window))
        window.profilebutton = Button(window,text="Get Horizontal Profile",command=lambda:get_profile(window))
        window.vertprofilebutton = Button(window,text="Get Vertical Profile",command=lambda:get_vert_profile(window))
        window.statstext = StringVar()
        window.statswindow = Label(window,textvariable=window.statstext)
        window.zoominbutton = Button(window,text="ZOOM +",command=lambda:zoom_in(window))
        window.zoomoutbutton = Button(window,text="ZOOM -",command=lambda:zoom_out(window))

        # Pack GUI using "grid" layout

        window.roi_square_button.grid(row=0,column=0)
        window.roi_ellipse_button.grid(row=1,column=0)
        window.roi_polygon_button.grid(row=2,column=0)
        window.roi_line_button.grid(row=3,column=0)
        window.imcanvas.grid(row=0,column=0,columnspan=1,rowspan=6,sticky='nsew')
        window.toolbar.grid(row=0,column=1,sticky='nsew')
        #~ window.scrollbutton.grid(row=7,column=0,sticky='nsew')
        window.imcanvas.img_scrollbar.grid(row=6,column=0,sticky='ew')
        window.statsbutton.grid(row=3,column=1,sticky='ew')
        window.profilebutton.grid(row=4,column=1,sticky='ew')
        window.vertprofilebutton.grid(row=5,column=1,sticky='ew')
        window.statswindow.grid(row=6,column=1,columnspan=1,rowspan=3,sticky='nsew')
        window.zoominbutton.grid(row=7,column=0,sticky='nsew')
        window.zoomoutbutton.grid(row=8,column=0,sticky='nsew')

        window.imcanvas.load_images(images)
        
        window.rowconfigure(0,weight=1)
        window.columnconfigure(0,weight=1)

        return

def close_window(active_frame):
        active_frame.destroy()
        return

def get_stats(window):
#        canvas = window.imcanvas
#        px = canvas.get_roi_pixels()
#        mean = np.mean(px)
#        std = np.std(px)
#        area = len(px)*canvas.get_active_image().xscale*canvas.get_active_image().yscale
#        tkMessageBox.showinfo('ROI STATS','Mean: %s\nStandard Deviation %s\nArea: %s' %(np.round(mean,2),np.round(std,2),np.round(area,2)))
        results = window.imcanvas.get_roi_statistics()
        tkinter.messagebox.showinfo('ROI STATS',results)

#        display_results(results,window)

def get_profile(window):
#        if not window.imcanvas.roi_list[0].roi_type=='line':
#                print "Only a line ROI can be used to generate profiles"
#                return
        profile,scale = window.imcanvas.get_profile()
        print(profile)
        return
def get_vert_profile(window):
        profile,scale = window.imcanvas.get_profile(direction='vertical')
        print(profile)
        return

def zoom_in(window):
        pass

def zoom_out(window):
        pass
