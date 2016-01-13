from Tkinter import *
from ttk import *
from source.functions.viewer_functions import *

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
	
	# Create all GUI elements
	window = Toplevel(master = master_window)
	window.imcanvas = Canvas(window,bd=0,width=512,height=512)
	window.roi_square_button = Button(window,text="Draw square ROI",command=lambda:draw_square_roi)
	window.roi_ellipse_button = Button(window,text="Draw elliptical ROI",command=lambda:draw_ellipse_roi)
	window.roi_polygon_button = Button(window,text="Draw polygon ROI", command=lambda:draw_polygon_roi)
	window.roi_line_button = Button(window,text="Draw line",command=lambda:draw_line_roi)
	window.scrollbutton = Button(window, text="SLICE + / -")
	window.statsbutton = Button(window,text="Get ROI statistics")
	window.statstext = StringVar()
	window.statswindow = Label(window,textvariable=window.statstext)
	window.zoominbutton = Button(window,text="ZOOM +",command=lambda:zoom_in)
	window.zoomoutbutton = Button(window,text="ZOOM -",command=lambda:zoom_out)
	
	# Pack GUI using "grid" layout
	window.imcanvas.grid(row=0,column=0,columnspan=1,rowspan=5,sticky='nsew')
	window.roi_square_button.grid(row=0,column=1,sticky='ew')
	window.roi_ellipse_button.grid(row=1,column=1,sticky='ew')
	window.roi_polygon_button.grid(row=2,column=1,sticky='ew')
	window.roi_line_button.grid(row=3,column=1,sticky='ew')
	window.scrollbutton.grid(row=7,column=0,sticky='nsew')
	window.statsbutton.grid(row=4,column=1,sticky='ew')
	window.statswindow.grid(row=5,column=1,columnspan=1,rowspan=3,sticky='nsew')
	window.zoominbutton.grid(row=5,column=0,sticky='nsew')
	window.zoomoutbutton.grid(row=6,column=0,sticky='nsew')
	
	window.active_images = []
	for image in images:
		viewer_object = MIPPY_8bitviewer(image)
		window.active_images.append(viewer_object)
	
	for image in window.active_images:
		image.resize(512,512)
	
	# Test - just draw slice 1!
	window.imcanvas.create_image(0,0,anchor='nw',image=window.active_images[0].photoimage)
	
	
	return
	
def close_window(active_frame):
	active_frame.destroy()
	return

def draw_square_roi(window):
	pass

def draw_ellipse_roi(window):
	pass
	
def draw_polygon_roi(window):
	pass

def draw_line_roi(window):
	pass

def zoom_in(window):
	pass

def zoom_out(window):
	pass