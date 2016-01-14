import dicom
import numpy as np
from Tkinter import *
from ttk import *
from PIL import Image,ImageTk

########################################
########################################
"""
GENERIC FUNCTIONS NOT ATTACHED TO CLASSES
"""
def quick_display(im_array):
	root = Tk()
	app = EasyViewer(master=root,im_array=im_array)
	app.mainloop()
	return

def generate_px_float(pixels,rs,ri,ss):
	return (pixels*rs+ri)/(rs*ss)
	
def get_global_min_and_max(image_list):
	"""
	Will only work with MIPPY_8bitviewer type objects
	"""
	min = np.amin(image_list[0].px_float)
	max = np.amax(image_list[0].px_float)
	for image in image_list:
		if np.amin(image.px_float) < min:
			min = np.amin(image.px_float)
		if np.amax(image.px_float) > max:
			max = np.amax(image.px_float)
	return min,max
	
def bits_to_ndarray(bits, shape):
	abytes = np.frombuffer(bits, dtype=np.uint8)
	abits = np.zeros(8*len(abytes), np.uint8)

	for n in range(8):
		abits[n::8] = (abytes & (2 ** n)) !=0

	return abits.reshape(shape)
	
	


########################################
########################################

class ROI():
	def __init__(self,coords):
		"""
		Expecting a string of 2- or 3-tuples to define bounding coordinates.
		Type of ROI will be inferred from number of points.
		"""
		self.coords = coords
		if len(coords)==1:
			self.roi_type = "point"
		elif len(coords)==2:
			self.roi_type = "line"
		elif len(coords)>len(coords[0]):
			self.roi_type = "polygon"
		elif len(coords)==len(coords[0]):
			self.roi_type = "plane"
		else:
			self.roi_type = "Unknown type"


class DicomCanvas(Canvas):
	def __init__(self,master,width=256,height=256,bd=0):
		super(Canvas,self).__init__(self,master,width=width,height=height,bd=bd)
		self.zoom_factor = 1
		self.roi_list = []
		self.roi_mode = 'square'
		self.bind('<Button-1>',self.left_click)
		self.bind('<B1-Motion>',self.left_drag)
		self.bind('<ButtonRelease-1>',self.left_release)
		self.bind('<Double-Button-1>',self.left_double)
		self.bind('<Button-3>',self.right_click)
		self.bind('<B3-Motion>',self.right_drag)
		self.bind('<ButtonRelease-3>',self.right_release)
		self.bind('<Double-Button-3>',self.right_double)
		self.drawing_roi = False
	
	def left_click(self,event):
		self.xmouse = event.x
		self.ymouse = event.y
		if len(self.roi_list)==0:
			self.drawing_roi = True
	
	def left_drag(self,event):
		xmove = event.x-self.xmouse
		ymove = event.y-self.ymouse
		if self.drawing_roi:
			try:
				self.delete('roi1')
			except:
				pass
			if roi_mode=='square':
				self.create_rectangle((self.xmouse,self.ymouse,event.x,event.y),fill='',outline='yellow',tags='roi1')
			elif roi_mode=='ellipse':
				self.create_oval((self.xmouse,self.ymouse,event.x,event,y),fill='',outline='yellow',tags='roi1')
		else:
			# Move ROI's if ROI's already exist???
			pass
	
	def left_release(self,event):
		if self.drawing_roi:
			self.add_roi((self.xmouse,self.ymouse,event.x,event.y))
			self.drawing_roi = False
		else:
			self.update_moved_rois(event)
			
	def update_moved_rois(self,event)
		xmove = event.x-self.xmouse
		ymove = event.y-self.ymouse
	
	def add_roi(coords):
		self.roi_list.append(ROI(coords))

class EasyViewer(Frame):
	def __init__(self,master,im_array):
		Frame.__init__(self)
		self.master = master
		self.master.imcanvas = Canvas(self.master,width=im_array.shape[1],height=im_array.shape[0])
		self.master.imobject = MIPPY_8bitviewer(im_array)
		self.master.imcanvas.im1 = self.master.imobject.photoimage
		self.master.imcanvas.create_image((0,0),image=self.master.imcanvas.im1,anchor='nw')
		self.master.imcanvas.pack()

########################################
########################################

class MIPPY_8bitviewer():
	"""
	This class wraps up Image.Image and ImageTk.PhotoImage classes so that they can be
	easily rescaled with whatever window and level for display purposes.  It's only 8-bit so
	you don't have the biggest dynamic range, but I'm sure I've heard that the eye can't
	resolve more than 256 shades of grey anyway...
	
	The actual floating point values are stored as an attribute "px_float", so that the actual
	scaled values can also be called for any given x,y position.  This should help when
	constructing an actual viewer.
	
	I should type "actual" some more...
	"""
	
	def __init__(self,dicom_dataset):
		if type(dicom_dataset) is str or type(dicom_dataset) is unicode:
			ds = dicom.read_file(dicom_dataset)
		elif type(dicom_dataset) is dicom.dataset.FileDataset:
			ds = dicom_dataset
		elif type(dicom_dataset) is np.ndarray:
			self.construct_from_array(dicom_dataset)
			return
		else:
			print "ERROR GENERATING IMAGE: Constructor input type not understood"
			return
		bitdepth = int(ds.BitsStored)
		pixels = ds.pixel_array.astype(np.float64)
		# DO NOT KNOW IF PIXEL ARRAY ALREADY HANDLES RS AND RI
		try:
			rs = ds[0x28,0x1053].value
		except:
			rs = 1
		try:
			ri = ds[0x28,0x1052].value
		except:
			ri = 0
		try:
			ss = ds[0x2005,0x100E].value
		except:
			ss = 1
		self.rows = ds.Rows
		self.columns = ds.Columns
		self.px_float = generate_px_float(pixels, rs, ri, ss)
		self.rangemax = generate_px_float(np.power(2,bitdepth), rs, ri, ss)
		self.rangemin = generate_px_float(0,rs,ri,ss)
		self.image_position = np.array(ds.ImagePositionPatient)
		self.image_orientation = np.array(ds.ImageOrientationPatient).reshape((2,3))
		try:
			self.xscale = ds.PixelSpacing[0]
			self.yscale = ds.PixelSpacing[1]
		except:
			self.xscale = 1
			self.yscale = 1
		try:
			self.overlay = Image.fromarray(bits_to_ndarray(ds[0x6000,0x3000].value, shape=(self.rows,self.columns))*255)
		except:
			self.overlay = None
		#~ self.px_8bit = np.power(2,8)*(((self.px_float)-np.amin(self.px_float))/(np.amax(self.px_float-np.amin(self.px_float))))
		#~ self.px_view = self.px_8bit
		#~ self.image = Image.fromarray(self.px_view)
		#~ self.photoimage = ImageTk.PhotoImage(image)
		self.image = None
		self.photoimage = None
		self.wl_and_display()
		return
		
	def construct_from_array(self,pixel_array):
		self.px_float = pixel_array
		self.rangemax = np.amax(pixel_array)
		self.rangemin = np.amin(pixel_array)
		self.xscale=1
		self.yscale=1
		self.overlay=None
		self.image = None
		self.photoimage = None
		self.wl_and_display()
		return
	
	def get_pt_coords(self,image_coords):
		"""
		Assumes you've passed a tuple (x,y) as your image coordinates
		"""
		voxel_position =  (self.image_position + image_coords[0]*self.xscale*self.image_orientation[0]
							+ image_coords[1]*self.yscale*self.image_orientation[1])
		return (voxel_position[0],voxel_position[1],voxel_position[2])

	def wl_and_display(self,window=None,level=None):
		if window and level:
			self.window = window
			self.level = level
		else:
			self.window = self.rangemax-self.rangemin
			self.level = (self.rangemax-self.rangemin)/2+self.rangemin
		if self.image:
			size=self.image.size
		else:
			size=(np.shape(self.px_float)[1],np.shape(self.px_float)[0])
		
		if self.level-self.rangemin<self.window/2:
			self.window=2*(self.level-self.rangemin)
		#~ elif self.rangemax-self.level<self.window/2:
			#~ self.window = 2*(self.rangemax-self.level)
		
		windowed_px = np.clip(self.px_float,self.level-self.window/2,self.level+self.window/2-1)
		px_view = np.clip(((windowed_px-np.amin(windowed_px))/self.window * np.power(2,8)),0.,255.).astype(np.uint8)
		self.image = Image.fromarray(px_view, mode='L')
		self.apply_overlay()
		if not size==self.image.size:
			self.resize(size[0],size[1])
		self.set_display_image()
		return
		
	def resize(self,dim1=256,dim2=256):
		self.image = self.image.resize((dim1,dim2), Image.ANTIALIAS)
		self.set_display_image()
		return
		
	def apply_overlay(self):
		if self.overlay:
			self.image.paste(self.overlay,box=(0,0),mask=self.overlay)
		return

	def set_display_image(self):
		self.photoimage = ImageTk.PhotoImage(self.image)
		return