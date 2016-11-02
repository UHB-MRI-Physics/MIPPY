import dicom
import numpy as np
from Tkinter import *
from ttk import *
from PIL import Image,ImageTk
import platform
import scipy.stats as sps
from datetime import datetime
import scipy.ndimage.interpolation as spim

########################################
########################################
"""
GENERIC FUNCTIONS NOT ATTACHED TO CLASSES
"""

def display_results(results,master_window):
	"""
	Method for displaying results table in a pop-up window.

	Results are expected in the format of a dictionary, e.g.
		results = {
			'SNR Tra': snr_tra,
			'SNR Sag': snr_sag,
			'SNR Cor': snr_cor,
			'SNR Mean': snr_mean,
			'SNR Std': snr_std,
			'SNR CoV': snr_cov}

	Master needs to be the variable pointing to the parent window.

	"""
	timestamp = str(datetime.now()).replace(" ","_").replace(":","")

#	if not name:
#		fname = "RESULTS_"+timestamp+".csv"
#	else:
#		fname = "RESULTS_"+timestamp+"_"+name+".csv"

	result_header = []
	result_values = []
	for key,value in results.items():
		result_header.append(key)
		result_values.append(value)
	result_array = np.array(result_values,dtype=np.float64)	# There's a problem here but I'm not sure what it is...
	result_array = np.transpose(result_array)
	try:
		lines = np.shape(result_array)[1]
	except IndexError:
		result_array = np.reshape(result_array,(1,np.shape(result_array)[0]))
#	if not directory:
#		current_dir = os.getcwd()
#		outputdir = os.path.join(current_dir,"Results")
#		if not os.path.exists(outputdir):
#			os.makedirs(outputdir)
#	else:
#		outputdir = directory
#		if not os.path.exists(outputdir):
#			os.makedirs(outputdir)
#	outpath = os.path.join(outputdir,fname)
#	with open(outpath,'wb') as csvfile:
#		csvwriter = csv.writer(csvfile,delimiter=',')
#		csvwriter.writerow(result_header)
#		for row in result_array:
#			csvwriter.writerow(row)
#
#	tkMessageBox.showinfo("INFO","Results saved to:\n"+outpath)

	popup = Toplevel(master_window)
	popup.title = 'Results'
	popup.holder = Frame(popup)
	popup.tree = Treeview(popup.holder)
	popup.tree['columns']=range(len(result_header))
	for i,value in enumerate(result_header):
		popup.tree.heading(i,text=value)
		popup.tree.column(i,width=200,stretch=True)
	popup.tree.column('#0',width=100,stretch=False)
	popup.scrollbarx = Scrollbar(popup.holder,orient='horizontal')
	popup.scrollbarx.config(command=popup.tree.xview)
	popup.scrollbary = Scrollbar(popup.holder,orient='vertical')
	popup.scrollbary.config(command=popup.tree.yview)
	for row in result_array:
		popup.tree.insert('','end',values=row)	# row[0]?
	popup.tree.grid(row=0,column=0)
	popup.scrollbarx.grid(row=1,column=0)
	popup.scrollbary.grid(row=0,column=1)
	popup.holder.pack()




	return


def quick_display(im_array,master_window):
	"""
	Requires a numpy array and an existing Tk instance to use as a
	master window.  im_array can be 2D or 3D.
	"""
	dim = len(np.shape(im_array))
	if dim==2:
		im_array = [im_array]
	win = Toplevel(master_window)
	win.imcanvas = MIPPYCanvas(win)
	win.imcanvas.img_scrollbar = Scrollbar(win,orient='horizontal')
	win.imcanvas.configure_scrollbar()
	win.imcanvas.grid(row=0,column=0,sticky='nsew')
	win.imcanvas.img_scrollbar.grid(row=1,column=0,sticky='ew')
	win.rowconfigure(0,weight=1)
	win.rowconfigure(1,weight=0)
	win.columnconfigure(0,weight=1)

	win.imcanvas.load_images(im_array)
	return

#~ def generate_px_float(pixels,rs,ri,ss):
	#~ return (pixels*rs+ri)/(rs*ss)

def bits_to_ndarray(bits, shape):
    abytes = np.frombuffer(bits, dtype=np.uint8)
    abits = np.zeros(8*len(abytes), np.uint8)

    for n in range(8):
        abits[n::8] = (abytes & (2 ** n)) !=0

    return abits.reshape(shape)

def px_bytes_to_array(byte_array,rows,cols,bitdepth=16,mode='littleendian',rs=1,ri=0,ss=None):
	if bitdepth==16:
		if mode=='littleendian':
			this_dtype = np.dtype('<u2')
		else:
			this_dtype = np.dtype('>u2')
	elif bitdepth==8:
		this_dtype = np.dytpe('u1')
	abytes = np.frombuffer(byte_array, dtype=this_dtype)
#	print np.mean(abytes)
#	print np.shape(abytes)
#	print abytes
	abytes = abytes.reshape((cols,rows))
	px_float = generate_px_float(abytes,rs,ri,ss)
#	print np.mean(px_float)
	return px_float

def generate_px_float(pixels,rs,ri,ss=None):
	if ss:
		return (pixels*rs+ri)/(rs*ss)
	else:
		return (pixels*rs+ri)

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

def isLeft(P0,P1,P2):
	"""
	Tests if testpoint (P2) is to the left/on/right of an infinite line passing through
	point0 (P0) and point1 (P1).  Returns:
	>0 for left of line
	=0 for on line
	<0 for right of line
	"""
	x=0
	y=1 #Just to convert x and y into indices 0 and 1
	value = ( (P1[x]-P0[x])*(P2[y]-P0[y]) - (P2[x]-P0[x])*(P1[y]-P0[y]) )
	return value

def cn_PnPoly(point, coords):
	"""
	Calculates the "crossing number" for an infinite ray passing through point
	to determine if point is inside of outside the polygon defined by coords
	"""
	cn = 0	# crossing number counter
	n = len(coords)
	x = 0
	y = 0	# just to convert x and y to indices
	for i in range(n):
		if i==n-1: j=0
		else: j=i+1
		if ((coords[i][y]<=point[y] and coords[j][y]>point[y])			# Upward crossing
			or (coords[i][y]>point[y] and coords[j][y]<=point[y])):		# Downward crossing
			# Calculate x-coordinate of intersect
			vt = (point[y]-coords[i][y])/(coords[j][y]-coords[i][y])
			if point[x] < coords[i][x] + vt*(coords[j][x]-coords[i][x]):
				cn+=1
	return cn%2	# 0 if even (outside region), 1 if odd (inside region)

def wn_PnPoly(point,coords):
	x=0
	y=1
	wn = 0
	n = len(coords)
	#~ print "n =",n
	for i in range(n):
		if i==n-1: j=0
		else: j=i+1
		#~ print i,j
		if coords[i][y]<=point[y]:
			if coords[j][y]>point[y]:		# upward crossing
				if isLeft(coords[i],coords[j],point)>0:
					wn+=1				# a valid "up intersect", so add to winding number
		else:
			if coords[j][y]<=point[y]:		# downward crossing
				if isLeft(coords[i],coords[j],point)<0:
					wn-=1			# valid "down" intersect, so remove from wn
	return wn

def get_ellipse_coords(center,a,b,n=128):
	"""
	Returns an array of the bounding coordinates for an ellipse with "radii"
	(more correct term??) of a and b.
	Takes "n" angular rays through 180 degrees and determines intersections
	of rays with perimeter of ellipse.
	Coordinates are tuples, returns coordinates as a list going clockwise from top
	center.

	Based on http://mathworld.wolfram.com/Ellipse-LineIntersection.html

	a = semiaxis in x direction
	b = semiaxis in y direction
	DO NOT CONFUSE THE TWO!
	"""
	coords_pos = []
	coords_neg = []

	for i in range(n):
		"""
		Find point on line (x0,y0), then intersection with of ellipse with line
		passing through that point and origin of ellipse
		"""
		angle = (float(i)/float(n))*np.pi
		x0 = 100.*np.sin(angle)
		y0 = 100.*np.cos(angle)
		#~ print str((x0,y0))
		xpos = (a*b*x0)/np.sqrt(a**2 * y0**2 + b**2 * x0**2)
		xneg = -xpos
		ypos = (a*b*y0)/np.sqrt(a**2 * y0**2 + b**2 * x0**2)
		yneg = -ypos
		coords_pos.append((xpos+center[0],ypos+center[1]))
		coords_neg.append((xneg+center[0],yneg+center[1]))
	return coords_pos+coords_neg



########################################
########################################

class ROI():
	def __init__(self,coords,roi_type=None):
		"""
		Expecting a string of 2- or 3-tuples to define bounding coordinates.
		Type of ROI will be inferred from number of points.
		"""
		self.coords = coords
		if not roi_type:
			if len(coords)==1:
				self.roi_type = "point"
			elif len(coords)==2:
				self.roi_type = "line"
			elif (len(coords)==4
				and coords[0][0]==coords[3][0]
				and coords[0][1]==coords[1][1]
				and coords[1][0]==coords[2][0]
				and coords[2][1]==coords[3][1]):
				self.roi_type = 'rectangle'
			elif len(coords)>len(coords[0]):
				self.roi_type = "3d"
			elif len(coords)==len(coords[0]):
				self.roi_type = "polygon"
			else:
				self.roi_type = "Unknown type"
		else:
			self.roi_type = roi_type
		arr_co=np.array(self.coords)
		self.bbox=(np.amin(arr_co[:,0]),np.amin(arr_co[:,1]),np.amax(arr_co[:,0]),np.amax(arr_co[:,1]))

	def contains(self,point):
		# This bounding box thing is a problem
		if (not self.bbox[0]<=point[0]<=self.bbox[2]
			or not self.bbox[1]<=point[1]<=self.bbox[3]):
			return False
		wn = wn_PnPoly(point,self.coords)
		if wn==0:
			#~ print "OUTSIDE: ",wn
			return False
		else:
			#~ print "INSIDE: ",wn
			return True

	def update(self,xmove,ymove):
		for i in range(len(self.coords)):
			self.coords[i]=(self.coords[i][0]+xmove,self.coords[i][1]+ymove)
		self.bbox=(self.bbox[0]+xmove,self.bbox[1]+ymove,self.bbox[2]+xmove,self.bbox[3]+ymove)
		#~ self.generate_mask()
		return

	#~ def generate_mask(self):
		#~ pass




class MIPPYCanvas(Canvas):
	def __init__(self,master,width=256,height=256,bd=0,drawing_enabled=False):
		Canvas.__init__(self,master,width=width,height=height,bd=bd,bg='black')
		self.master = master
		self.zoom_factor = 1
		self.roi_list = []
		self.shift = False
		self.roi_mode = 'rectangle'
		self.bind('<Button-1>',self.left_click)
		self.bind('<B1-Motion>',self.left_drag)
		self.bind('<ButtonRelease-1>',self.left_release)
		self.bind('<Double-Button-1>',self.left_double)
		if not platform.system()=='Darwin':
			self.bind('<Button-3>',self.right_click)
			self.bind('<B3-Motion>',self.right_drag)
			self.bind('<ButtonRelease-3>',self.right_release)
			self.bind('<Double-Button-3>',self.right_double)
		else:
			self.bind('<Button-2>',self.right_click)
			self.bind('<B2-Motion>',self.right_drag)
			self.bind('<ButtonRelease-2>',self.right_release)
			self.bind('<Double-Button-2>',self.right_double)
		self.drawing_roi = False
		self.xmouse = None
		self.ymouse = None
		self.tempx = None
		self.tempy = None
		self.tempcoords = []
		self.images = []
		self.active = 1
		self.drawing_enabled = drawing_enabled
		self.width=width
		self.height=height
		#~ self.zoom_factor=None
		self.pixel_array=None
		self.img_scrollbar=None

#	def shift_down(self,event):
#		self.shift = True
#		print "SHIFT DOWN"
#
#	def shift_up(self,event):
#		self.shift = False
#		print "SHIFT UP"

	def configure_scrollbar(self):
		if self.img_scrollbar:
			self.img_scrollbar.config(command=self.scroll_images)
			self.img_scrollbar.set(0,1)
		if self.active and not self.images==[]:
			if not len(self.images)==1:
				self.img_scrollbar.set(self.active-1/(len(self.images)-1),self.active/(len(self.images)-1))
			else:
				self.img_scrollbar.set(0,1)

	def scroll_images(self,command,value,mode='unit'):
		if command=='scroll':
			self.show_image(self.active+int(value))
		elif command=='moveto':
			selected_img = int(np.round((float(value)*float((len(self.images)))),0))+1
			if not selected_img==self.active:
				self.show_image(selected_img)

	def update_scrollbar(self,value):
		current_img = float(self.active)
		total_img = float(len(self.images))
		lo = (self.active-1)/total_img
		hi = self.active/total_img
		self.img_scrollbar.set(lo,hi)

	def reset(self):
		self.images = []
		self.delete('all')
		self.active=None

	def show_image(self,num=None):
		"""
		Takes slice number (which starts from 1, not zero).  Doesn't do anything
		if there are no images loaded.
		"""
		if len(self.images)==0:
			return
		if num and not num<1 and not num>len(self.images):
			self.active = num
			self.update_scrollbar((num-1.)/len(self.images))
		self.delete('image')
		self.create_image((0,0),image=self.images[self.active-1].photoimage,anchor='nw')


	def get_roi_pixels(self,rois=[]):
		"""
		Returns a LIST of pixel values from an ROI.
		ROIS must be a list of ROI numbers.
		"""
		px = []
		im = self.get_active_image()
		if len(rois)==0:
			rois = range(len(self.roi_list))
		for y in range(im.rows):
			for x in range(im.columns):
				for i in rois:
					if i==len(px):
						px.append([])
					if self.roi_list[i].contains((x*self.zoom_factor,y*self.zoom_factor)):
						px[i].append(im.px_float[y][x])

		print "GOT PIXELS"
		return px

	def get_roi_statistics(self,rois=[]):
		if len(self.roi_list)<1:
			return None
#		else:
#			stats = []
		if self.roi_list[0].roi_type=='line':
			return None
		px_list = self.get_roi_pixels()
		stats = {
				'mean':		map(np.mean,px_list),
				'std':		map(np.std,px_list),
				'min':		map(np.amin,px_list),
				'max':		map(np.amax,px_list),
				'mode':		map(sps.mode,px_list),
				'skewness':		map(sps.skew,px_list),
				'kurtosis':		map(sps.kurtosis,px_list),
				'cov':		map(sps.variation,px_list),
#							'histogram':	sps.cumfreq(px),
				'sum':		map(np.sum,px_list),
				'area_px':		map(len,px_list)
				}

		print stats
		return stats

	def get_profile(self,resolution=1,width=1,interpolate=False,direction='horizontal',index=0):
		"""Returns a line profile from the image"""

#		if len(tags)==0:
#			if not len(self.roi_list)==1:
#				return None
#			rois = self.roi_list
#
#		else:
#			rois = []
#			for roi in self.roi_list:
#				if all(tags) in roi.tags:
#					rois.append(roi)
#		if len(rois)>1:
#			print "Too many ROI's found."
#			return None


		print self.roi_list[index].roi_type
		if not (self.roi_list[index].roi_type=='line' or self.roi_list[index].roi_type=='rectangle'):
			print "Not a valid ROI type for profile.  Line or rectangle required."
			return None
#		if self.shift:
#			direction='vertical'
#		else:
#			direction='horizontal'

		roi = self.roi_list[index]
		coords = roi.coords/self.zoom_factor

		if roi.roi_type=='line':
			profile_length = np.sqrt( (coords[1][0]-coords[0][0])**2 + (coords[1][1]-coords[0][1])**2 )
		elif direction=='horizontal':
			profile_length = coords[1][0]-coords[0][0]
		elif direction=='vertical':
			profile_length = coords[3][1]-coords[0][1]
		else:
			print "Profile direction not understood!"
			return None

		length_int = int(np.round(profile_length/resolution,0))
		if interpolate:
			intorder=1
		else:
			intorder=0

		profile = None

		if roi.roi_type=='line':
			x_arr = np.linspace(coords[0][0],coords[1][0],length_int)
			y_arr = np.linspace(coords[0][1],coords[1][1],length_int)

			profile = spim.map_coordinates(self.get_active_image().px_float,np.vstack((y_arr,x_arr)),order=intorder,prefilter=False)

		elif direction=='horizontal':
			y_len = int(np.round(coords[3][1]-coords[0][1],0))
			x_arr = np.linspace(coords[0][0],coords[1][0],length_int)
			profiles = np.zeros((y_len,len(x_arr)))
			for i in range(y_len):
				y_arr = np.zeros(np.shape(x_arr))+coords[0][1]+i
				profiles[i] = spim.map_coordinates(self.get_active_image().px_float,np.vstack((y_arr,x_arr)),order=intorder,prefilter=False)
			profile = np.mean(profiles,axis=0)
		elif direction=='vertical':
			x_len = int(np.round(coords[1][0]-coords[0][0],0))
			y_arr = np.linspace(coords[0][1],coords[3][1],length_int)
			profiles = np.zeros((x_len,len(y_arr)))
			for i in range(x_len):
				x_arr = np.zeros(np.shape(y_arr))+coords[0][0]+i
				profiles[i] = spim.map_coordinates(self.get_active_image().px_float,np.vstack((y_arr,x_arr)),order=intorder,prefilter=False)
			profile = np.mean(profiles,axis=0)

		return profile, np.array(range(length_int))

	def new_roi(self,coords,tags=[],system='canvas'):
		if system=='image':
			coords=self.canvas_coords(coords)
		elif not system=='canvas':
			print "Invalid coordinate system specified"
			return
		for i in range(len(coords)):
			j = i+1
			if j==len(coords):
				j=0
			tags.append('roi')
			self.create_line((coords[i][0],coords[i][1],coords[j][0],coords[j][1]),fill='yellow',width=1,tags=tags)
		self.add_roi(coords)
#		print "ROI should be on image now..."
		return

	def roi_rectangle(self,x_start,y_start,width,height,tags=[],system='canvas'):
		x1 = x_start
		x2 = x_start+width
		y1 = y_start
		y2 = y_start+height
		if system=='image':
			x1 = x1*self.zoom_factor
			x2 = x2*self.zoom_factor
			y1 = y1*self.zoom_factor
			y2 = y2*self.zoom_factor
		elif not system=='canvas':
			print "Invalid coordinate system specified"
			return
		print x1,y1,x2,y2
		self.new_roi([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],tags=tags)
		return


	def load_images(self,image_list):
		self.images = []
		self.delete('all')
		n=0
#		open_ds = None
#		current_path = None
		for ref in image_list:

			self.progress(45.*n/len(image_list)+10)
			self.images.append(MIPPYImage(ref))
			n+=1

		#~ for image in self.images:
			#~ image.resize(self.width,self.height)
			#~ image.zoom(self.zoom_factor)

		self.global_min,self.global_max = get_global_min_and_max(self.images)
		self.global_rangemin = self.images[0].rangemin
		self.global_rangemax = self.images[0].rangemax
		self.fullrange = self.global_rangemax-self.global_rangemin
		self.default_window = self.global_max-self.global_min
		self.default_level = self.global_min + self.default_window/2
		self.level = self.default_level
		self.window = self.default_window
		self.zoom_factor = np.amin([float(self.width)/float(self.images[0].columns),float(self.height)/float(self.images[0].rows)])

		for i in range(len(self.images)):
			self.progress(45.*i/len(self.images)+55)
			self.images[i].zoom(self.zoom_factor)
			self.images[i].wl_and_display(window=self.window,level=self.level)
		self.configure_scrollbar()
		self.show_image(1)

		print "canvas width,height: %s,%s" %(self.width,self.height)
		print "image width,height: %s,%s" %(self.get_active_image().columns,self.get_active_image().rows)
		print "zoom: %s" %(self.zoom_factor)

		#~ self.pixel_array = np.array(a.px_float for a in self.images)

		self.progress(0.)
		return

	def get_active_image(self):
		return self.images[self.active-1]

	def reset_window_level(self):
		self.temp_window = self.default_window
		self.temp_level = self.default_level
		self.window = self.default_window
		self.level = self.default_level

		for image in self.images:
			image.wl_and_display(window = self.default_window, level = self.default_level)
		self.show_image(self.active)
		return


	def left_click(self,event):
		if not self.drawing_enabled:
			return
		self.xmouse = event.x
		self.ymouse = event.y
		self.tempx = event.x
		self.tempy = event.y
		#~ print self.xmouse
		#~ print self.ymouse
		moving = False
		for roi in self.roi_list:
			if roi.contains((self.xmouse,self.ymouse)):
				moving = True
				break
		if not moving:
			self.drawing_roi = True
			# Need to add stuff to detect if "shift" or "ctrl" held when drawing, as
			# in this case, don't want to delete existing ROIs
			self.delete_rois()
			self.temp = []
			self.tempcoords.append((self.xmouse,self.ymouse))

	def left_drag(self,event):
		if not self.drawing_enabled:
			return
		xmove = event.x-self.tempx
		ymove = event.y-self.tempy
		if self.drawing_roi:
			if self.roi_mode=='rectangle' or self.roi_mode=='ellipse':
				self.delete('roi')
			if self.roi_mode=='rectangle':
				self.create_rectangle((self.xmouse,self.ymouse,event.x,event.y),fill='',outline='yellow',tags='roi')
			elif self.roi_mode=='ellipse':
				self.create_oval((self.xmouse,self.ymouse,event.x,event.y),fill='',outline='yellow',tags='roi')
			elif self.roi_mode=='freehand':
				self.create_line((self.tempx,self.tempy,event.x,event.y),fill='yellow',width=1,tags='roi')
				self.tempcoords.append((event.x,event.y))
			elif self.roi_mode=='line':
				self.delete('roi')
				self.create_line((self.xmouse,self.ymouse,event.x,event.y),fill='yellow',width=1,tags='roi')

		else:
			self.move('roi',xmove,ymove)

		self.tempx = event.x
		self.tempy = event.y

	def left_release(self,event):
		if not self.drawing_enabled:
			return
		if self.drawing_roi:
			self.roi_list=[]
			if self.roi_mode=='rectangle':
				self.add_roi([(self.xmouse,self.ymouse),(event.x,self.ymouse),(event.x,event.y),(self.xmouse,event.y)])
			elif self.roi_mode=='ellipse':
				positive_coords = []
				negative_coords = []
				# http://mathworld.wolfram.com/Ellipse-LineIntersection.html
				# get points in circle by incrementally adding rays from centre
				# and getting intersections with ellipse
				#~ print self.bbox('roi')
				bbox = self.bbox('roi')
				a = (bbox[2]-bbox[0])/2
				b = (bbox[3]-bbox[1])/2
				c = (bbox[0]+a,bbox[1]+b)
				self.add_roi(get_ellipse_coords(c,a,b,n=2*max([a,b])))
				coords = self.roi_list[0].coords
				#~ for i in range(len(coords)):
					#~ if i==len(coords)-1: j=0
					#~ else: j=i+1
					#~ self.create_line((coords[i][0],coords[i][1],coords[j][0],coords[j][1]),fill='red',width=1,tag='roi')
			elif self.roi_mode=='line':
				self.add_roi([(self.xmouse,self.ymouse),(event.x,event.y)])
			else:
				self.create_line((self.tempx,self.tempy,self.xmouse,self.ymouse),fill='yellow',width=1,tags='roi')
				if len(self.tempcoords)>1:
					self.add_roi(self.tempcoords)
				else:
					self.delete('roi')
			self.drawing_roi = False
		else:
			total_xmove = event.x-self.xmouse
			total_ymove = event.y-self.ymouse
			if len(self.roi_list)>0:
				for roi in self.roi_list:
					roi.update(total_xmove,total_ymove)
		self.tempcoords = []
		self.tempx = None
		self.tempy = None

	def left_double(self,event):
		pass

	def right_click(self,event):
		if self.images==[]:
			# If no active display slices, just skip this whole function
			return
		self.xmouse = event.x
		self.ymouse = event.y

	def right_drag(self,event):
		xmove = event.x-self.xmouse
		ymove = event.y-self.ymouse
		# Windowing is applied to the series as a whole...
		# Sensitivity needs to vary with the float pixel scale.  Map default window
		# (i.e. full range of image) to "sensitivity" px motion => 1px up/down adjusts level by
		# "default_window/sensitivity".  1px left/right adjusts window by
		# "default_window/sensitivity"
		window_sensitivity = 300
		level_sensitivity = 500
		min_window = self.fullrange/255
		i = self.active-1
		self.temp_window = self.window+xmove*(self.fullrange/window_sensitivity)
		self.temp_level = self.level-ymove*(self.fullrange/level_sensitivity)
		if self.temp_window<min_window:
			self.temp_window=min_window
		if self.temp_level<self.global_rangemin+min_window/2:
			self.temp_level=self.global_rangemin+min_window/2
		self.images[i].wl_and_display(window=self.temp_window,level=self.temp_level)
		self.show_image()

	def right_release(self,event):
		if abs(self.xmouse-event.x)<1 and abs(self.ymouse-event.y)<1:
			return
		self.set_window_level(self.temp_window,self.temp_level)
#		self.window = self.temp_window
#		self.level = self.temp_level
#		for image in self.images:
#			image.wl_and_display(window=self.window,level=self.level)
#		self.show_image()

	def set_window_level(self,window,level):
		self.window = window
		self.level = level
		for image in self.images:
			image.wl_and_display(window=self.window,level=self.level)
		self.show_image()

	def right_double(self,event):
		if self.images == []:
			return

		self.temp_window = self.default_window
		self.temp_level = self.default_level
		self.window = self.default_window
		self.level = self.default_level

		for image in self.images:
			image.wl_and_display(window = self.default_window, level = self.default_level)
		self.show_image(self.active)


	def add_roi(self,coords,roi_type=None):
		self.roi_list.append(ROI(coords,roi_type))

	def delete_rois(self):
		self.roi_list = []
		self.delete('roi')

	def progress(self,percentage):
		try:
			self.master.progressbar['value']=percentage
			self.master.progressbar.update()
		except:
			pass

	def draw_rectangle_roi(self):
		self.drawing_enabled=True
		self.roi_mode='rectangle'

	def draw_ellipse_roi(self):
		self.drawing_enabled=True
		self.roi_mode='ellipse'

	def draw_freehand_roi(self):
		self.drawing_enabled=True
		self.roi_mode='freehand'

	def draw_line_roi(self):
		self.drawing_enabled=True
		self.roi_mode='line'

	def canvas_coords(self,image_coords):
		new_coords = []
		for thing in image_coords:
			new_coords.append((thing[0]*self.zoom_factor,thing[1]*self.zoom_factor))
		return new_coords

	def image_coords(self,canvas_coords):
		new_coords = []
		for thing in canvas_coords:
			new_coords.append((thing[0]/self.zoom_factor,thing[1]/self.zoom_factor))
		return new_coords





class EasyViewer(Frame):
	def __init__(self,master,im_array):
		Frame.__init__(self)
		self.master = master
		self.master.imcanvas = MIPPYCanvas(self.master,width=im_array.shape[1],height=im_array.shape[0],drawing_enabled=True)
		self.master.imobject = MIPPYImage(im_array)
		self.master.imcanvas.im1 = self.master.imobject.photoimage
		self.master.imcanvas.create_image((0,0),image=self.master.imcanvas.im1,anchor='nw')
		self.master.imcanvas.pack()

########################################
########################################

class MIPPYImage():
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
			self.rs = float(ds[0x28,0x1053].value)
		except:
			self.rs = 1.
		try:
			self.ri = float(ds[0x28,0x1052].value)
		except:
			self.ri = 0.
		try:
			self.ss = float(ds[0x2005,0x100E].value)
		except:
			self.ss = None
		self.rows = ds.Rows
		self.columns = ds.Columns
		self.px_float = generate_px_float(pixels, self.rs, self.ri, self.ss)
		self.rangemax = generate_px_float(np.power(2,bitdepth), self.rs, self.ri, self.ss)
		self.rangemin = generate_px_float(0,self.rs,self.ri,self.ss)
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
#		print "Max",self.rangemax
#		print "Min",self.rangemin
#		self.rangemax = np.ones(np.shape(pixel_array)).astype(np.float64)*maxval
#		self.rangemin = np.ones(np.shape(pixel_array)).astype(np.float64)*minval
		self.xscale=1
		self.yscale=1
		self.overlay=None
		self.image = None
		self.photoimage = None
		self.rows = np.shape(pixel_array)[0]
		self.columns = np.shape(pixel_array)[1]
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

	def zoom(self,zoom):
		self.image = self.image.resize((int(np.round(self.columns*zoom,0)),int(np.round(self.rows*zoom,0))), Image.ANTIALIAS)
		self.set_display_image
		return

	def apply_overlay(self):
		if self.overlay:
			self.image.paste(self.overlay,box=(0,0),mask=self.overlay)
		return

	def set_display_image(self):
		self.photoimage = ImageTk.PhotoImage(self.image)
		return