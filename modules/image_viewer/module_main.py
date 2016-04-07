from Tkinter import *
from ttk import *
import tkMessageBox
from source.functions.viewer_functions import *
import os
from PIL import Image,ImageTk
import platform

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
	print "Module loaded..."
	print "Received "+str(len(images))+" image datasets."
	print os.getcwd()
	#~ icondir = os.path.join(os.getcwd(),'source','images')
	
	
	
	# Create all GUI elements
	window = Toplevel(master = master_window)
	# Create canvas
	if platform.system()=='Linux':
		canvas_size=320
	else:
		canvas_size=512
	window.imcanvas = MIPPYCanvas(window,bd=0,width=canvas_size,height=canvas_size,drawing_enabled=False)
	# Open icons for button
	window.roi_sq_im = ImageTk.PhotoImage(file='source/images/square_roi.png')
	window.roi_el_im = ImageTk.PhotoImage(file='source/images/ellipse_roi.png')
	window.roi_fr_im = ImageTk.PhotoImage(file='source/images/freehand_roi.png')
	window.roi_li_im = ImageTk.PhotoImage(file='source/images/line_roi.png')
	
	window.toolbar=Frame(window)
	
	window.roi_square_button = Button(window.toolbar,text="Draw square ROI",command=lambda:window.imcanvas.draw_rectangle_roi(),image=window.roi_sq_im)
	window.roi_ellipse_button = Button(window.toolbar,text="Draw elliptical ROI",command=lambda:window.imcanvas.draw_ellipse_roi(),image=window.roi_el_im)
	window.roi_polygon_button = Button(window.toolbar,text="Draw freehand ROI", command=lambda:window.imcanvas.draw_freehand_roi(),image=window.roi_fr_im)
	window.roi_line_button = Button(window.toolbar,text="Draw line",command=lambda:window.imcanvas.draw_line_roi(),image=window.roi_li_im)
	#~ window.scrollbutton = Button(window, text="SLICE + / -")
	window.imcanvas.img_scrollbar = Scrollbar(window,orient='horizontal')
	window.imcanvas.configure_scrollbar()
	window.statsbutton = Button(window,text="Get ROI statistics",command=lambda:get_roi_statistics(window))
	window.statstext = StringVar()
	window.statswindow = Label(window,textvariable=window.statstext)
	window.zoominbutton = Button(window,text="ZOOM +",command=lambda:zoom_in(window))
	window.zoomoutbutton = Button(window,text="ZOOM -",command=lambda:zoom_out(window))
	
	# Pack GUI using "grid" layout
	window.imcanvas.grid(row=0,column=0,columnspan=1,rowspan=5,sticky='nsew')
	window.roi_square_button.grid(row=0,column=0)
	window.roi_ellipse_button.grid(row=1,column=0)
	window.roi_polygon_button.grid(row=2,column=0)
	window.roi_line_button.grid(row=3,column=0)
	window.toolbar.grid(row=0,column=1)
	#~ window.scrollbutton.grid(row=7,column=0,sticky='nsew')
	window.imcanvas.img_scrollbar.grid(row=7,column=0,sticky='ew')
	window.statsbutton.grid(row=4,column=1,sticky='ew')
	window.statswindow.grid(row=5,column=1,columnspan=1,rowspan=3,sticky='nsew')
	window.zoominbutton.grid(row=5,column=0,sticky='nsew')
	window.zoomoutbutton.grid(row=6,column=0,sticky='nsew')
	
	window.imcanvas.load_images(images)
	
	return
	
def close_window(active_frame):
	active_frame.destroy()
	return

def get_roi_statistics(window):
	canvas = window.imcanvas
	px = canvas.get_roi_pixels()
	mean = np.mean(px)
	std = np.std(px)
	area = len(px)*canvas.get_active_image().xscale*canvas.get_active_image().yscale
	tkMessageBox.showinfo('ROI STATS','Mean: %s\nStandard Deviation %s\nArea: %s' %(np.round(mean,2),np.round(std,2),np.round(area,2)))

def zoom_in(window):
	pass

def zoom_out(window):
	pass
	
print "Apple"