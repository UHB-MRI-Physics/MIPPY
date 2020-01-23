import pydicom
import numpy as np
from tkinter import *
from tkinter.ttk import *
from PIL import Image, ImageTk
import platform
import scipy.stats as sps
from datetime import datetime
import scipy.ndimage.interpolation as spim
import gc
import time
import sys
import pickle
import os
import datetime
from pkg_resources import resource_filename
import mippy
import mippy.mdicom
from mippy.mdicom.pixel import get_voxel_location
import uuid
import copy

########################################
########################################
"""
GENERIC FUNCTIONS NOT ATTACHED TO CLASSES
"""

def open_lut(name):
    try:
        lutpath = resource_filename('mippy','luts/'+name+'.csv')
    except:
        print("Unable to find LUT: {}".format(name))
        raise
    lut = np.genfromtxt(lutpath,skip_header=1,delimiter=',').swapaxes(0,1).astype(np.uint8)
    #print(lut[1:4])
    return lut[1:4]

def display_results(results, master_window):
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
    timestamp = str(datetime.now()).replace(" ", "_").replace(":", "")

    result_header = []
    result_values = []
    for key, value in list(results.items()):
        result_header.append(key)
        result_values.append(value)
    result_array = np.array(result_values, dtype=np.float64)  # There's a problem here but I'm not sure what it is...
    result_array = np.transpose(result_array)
    try:
        lines = np.shape(result_array)[1]
    except IndexError:
        result_array = np.reshape(result_array, (1, np.shape(result_array)[0]))

    popup = Toplevel(master_window)
    popup.title = 'Results'
    popup.holder = Frame(popup)
    popup.tree = Treeview(popup.holder)
    popup.tree['columns'] = list(range(len(result_header)))
    for i, value in enumerate(result_header):
        popup.tree.heading(i, text=value)
        popup.tree.column(i, width=200, stretch=True)
    popup.tree.column('#0', width=100, stretch=False)
    popup.scrollbarx = Scrollbar(popup.holder, orient='horizontal')
    popup.scrollbarx.config(command=popup.tree.xview)
    popup.scrollbary = Scrollbar(popup.holder, orient='vertical')
    popup.scrollbary.config(command=popup.tree.yview)
    for row in result_array:
        popup.tree.insert('', 'end', values=row)  # row[0]?
    popup.tree.grid(row=0, column=0)
    popup.scrollbarx.grid(row=1, column=0)
    popup.scrollbary.grid(row=0, column=1)
    popup.holder.pack()

    return


def quick_display(im_array, master_window):
    """
    Given a 2D or 3D numpy.ndarray, opens a new window and displays the image(s) on
    a new 256x256 image canvas.  Bit of a quick and dirty function, but occasionally
    useful.

    Requires an existing Tk instance to use as a master for the window.

    Parameters
    ----------------------
    im_array: numpy.ndarray
        2D array of pixel values
    master_window: tkinter object
        Open/running tkinter instance or widget

    """
    dim = len(np.shape(im_array))
    if dim == 2:
        im_array = [im_array]
    win = Toplevel(master_window)
    win.imcanvas = MIPPYCanvas(win)
    win.imcanvas.img_scrollbar = Scrollbar(win, orient='horizontal')
    win.imcanvas.configure_scrollbar()
    win.imcanvas.grid(row=0, column=0, sticky='nsew')
    win.imcanvas.img_scrollbar.grid(row=1, column=0, sticky='ew')
    win.rowconfigure(0, weight=1)
    win.rowconfigure(1, weight=0)
    win.columnconfigure(0, weight=1)

    win.imcanvas.load_images(im_array)
    return


def get_overlay(ds):
    """
    Given a Pydicom dataset, this extracts and returns the 1-bit bitmap overlay as a
    2D numpy.ndarray containing values of 0 or 255.

    If it exists, this bitmap exists in Siemens MRI data as tag (6000,3000).

    Parameters
    --------------------
    ds: pydicom.Dataset.Dataset or pydicom.Dataset.FileDataset
        Pydicom dataset from which the overlay (6000,3000) should be extracted

    Returns
    ---------------------
    overlay: numpy.ndarray
        2D array of 8-bit integer values
    """
    try:
        bits = ds[0x6000, 0x3000].value
        # ~ print "OVERLAY LENGTH",len(bits)
        # ~ print "EXPECTED LENGTH",ds.Rows*ds.Columns
        # ~ if len(bits)>ds.Rows*ds.Columns:
        # ~ bits = bits[0:ds.Rows*ds.Columns]
        # ~ print "NEW OVERLAY LENGTH",len(bits)
        overlay = bits_to_ndarray(bits, shape=(ds.Rows, ds.Columns)) * 255
    except KeyError:
        return None
    except:
        raise
    return overlay


def px_bytes_to_array(byte_array, rows, cols, bitdepth=16, mode='littleendian', rs=1, ri=0, ss=None):
    """
    Takes a byte-string of pixel value (as in PixelData from a DICOM instance), and converts
    to a numpy.ndarray of float values.

    Parameters
    ---------------------
    byte array: bytes
        Byte-string of PixelData
    rows: int
        Number of rows in the image
    cols: int
        Number of columns in the image
    bitdepth: int, optional
        Bit-depth of your byte array (default = 16)
    mode: str, optional
        'Endedness' of your byte array (default = 'littleendian')
    rs: float, optional
        Rescale slope for the pixel values (default = 1)
    ri: float, optional
        Rescale intercept for the pixel values (default = 0)
    ss: float, optional
        Additional reciprocal scaling factor often found in Philips images (default = None)

    Returns
    --------------
    px_float: numpy.ndarray
        2D array of 64-bit float values
    """
    if bitdepth == 16:
        if mode == 'littleendian':
            this_dtype = np.dtype('<u2')
        else:
            this_dtype = np.dtype('>u2')
    elif bitdepth == 8:
        this_dtype = np.dytpe('u1')
    abytes = np.frombuffer(byte_array, dtype=this_dtype)
    abytes = abytes.reshape((cols, rows))
    px_float = generate_px_float(abytes, rs, ri, ss)
    return px_float


def generate_px_float(pixels, rs, ri, ss=None, pad_zero=False):
    """
    Takes a numpy.ndarray of unscaled integer pixel values (typically 16 bit) and applies
    the relevant scaling factors from the DICOM header to generate the correct rescaled
    pixel values.

    Parameters
    --------------------------
    pixels: numpy.ndarray
        The unscaled integer pixel data
    rs: float
        Rescale slope
    ri: float
        Rescale intercept
    ss: float, optional
        Additional reciprocal scaling factor (typically used in Philips images to get 'real world' values.

    Returns
    --------------------
    px_float: numpy.ndarray
        N-dimensional array of scaled pixel values. The shape of the output array matched the shape of the input array.
    """
    if pad_zero and np.shape(pixels)[0]!=np.shape(pixels)[1]:
        # Zero pad to make the image square
        pad_width_col = np.shape(pixels)[0]-np.shape(pixels)[1]
        pad_width_row = np.shape(pixels)[1]-np.shape(pixels)[0]
        if pad_width_col>0:
            # print("Padding columns")
            pixels = np.pad(pixels,((0,0),(0,pad_width_col)),mode='constant')
        elif pad_width_row>0:
            # print("Padding rows")
            pixels = np.pad(pixels,((0,pad_width_row),(0,0)),mode='constant')
    if ss:
        return (pixels * rs + ri) / (rs * ss)
    else:
        return (pixels * rs + ri)


def get_global_min_and_max(image_list):
    """
    Takes a list of MIPPYImage objects and returns the minimum and maximum pixel value
    from the whole list.

    Parameters
    -------------------------
    image_list: list
        1D list of MIPPYImage objects, as found in MIPPYCanvas.image_list

    Returns
    -------------------------
    min: float
        Minimum pixel value
    max: float
        Maximum pixel value
    """
    min = np.min(image_list[0].px_float)
    max = np.max(image_list[0].px_float)
    for image in image_list[1:]:
        newmin = np.min(image.px_float)
        newmax = np.max(image.px_float)

        if newmin < min:
            min = newmin
        if newmax > max:
            max = newmax
    return float(min), float(max)


# ~ def bits_to_ndarray(bits, shape):
# ~ abytes = np.frombuffer(bits, dtype=np.uint8)
# ~ abits = np.zeros(8*len(abytes), np.uint8)

# ~ for n in range(8):
# ~ abits[n::8] = (abytes & (2 ** n)) !=0

# ~ return abits.reshape(shape)

def bits_to_ndarray(bits, shape):
    """
    Converts an 8-bit byte string of 1-bit pixel data into a numpy.ndarray
    of ones and zeros.

    Parameters
    -----------------------
    bits: bytes
        Byte-string containing the 1-bit pixel data
    shape: tuple
        The desired output shape as (rows,columns)

    Returns
    -----------------------------
    bitmap: numpy.ndarray
        Binary pixel data of the required shape
    """
    abytes = np.frombuffer(bits, dtype=np.uint8)
    abits = np.zeros(8 * len(abytes), np.uint8)

    for n in range(8):
        abits[n::8] = (abytes & (2 ** n)) != 0

    if len(abits) > shape[0] * shape[1]:
        abits = abits[0:shape[0] * shape[1]]

    return abits.reshape(shape)


def isLeft(P0, P1, P2):
    """
    Tests if testpoint (P2) is to the left/on/right of an infinite line passing through
    point0 (P0) and point1 (P1).  Returns:
    >0 for left of line
    =0 for on line
    <0 for right of line
    """
    x = 0
    y = 1  # Just to convert x and y into indices 0 and 1
    value = ((P1[x] - P0[x]) * (P2[y] - P0[y]) - (P2[x] - P0[x]) * (P1[y] - P0[y]))
    return value


def cn_PnPoly(point, coords):
    """
    Calculates the "crossing number" for an infinite ray passing through point
    to determine if point is inside of outside the polygon defined by coords
    """
    cn = 0  # crossing number counter
    n = len(coords)
    x = 0
    y = 0  # just to convert x and y to indices
    for i in range(n):
        if i == n - 1:
            j = 0
        else:
            j = i + 1
        if ((coords[i][y] <= point[y] and coords[j][y] > point[y])  # Upward crossing
                or (coords[i][y] > point[y] and coords[j][y] <= point[y])):  # Downward crossing
            # Calculate x-coordinate of intersect
            vt = (point[y] - coords[i][y]) / (coords[j][y] - coords[i][y])
            if point[x] < coords[i][x] + vt * (coords[j][x] - coords[i][x]):
                cn += 1
    return cn % 2  # 0 if even (outside region), 1 if odd (inside region)


def wn_PnPoly(point, coords):
    x = 0
    y = 1
    wn = 0
    n = len(coords)
    for i in range(n):
        if i == n - 1:
            j = 0
        else:
            j = i + 1
        if coords[i][y] <= point[y]:
            if coords[j][y] > point[y]:  # upward crossing
                if isLeft(coords[i], coords[j], point) > 0:
                    wn += 1  # a valid "up intersect", so add to winding number
        else:
            if coords[j][y] <= point[y]:  # downward crossing
                if isLeft(coords[i], coords[j], point) < 0:
                    wn -= 1  # valid "down" intersect, so remove from wn
    return wn


def get_ellipse_coords(center, a, b, n=128):
    """
    Returns an array of the bounding coordinates for an ellipse with "radii"
    (more correct term??) of a and b.
    Takes "n" angular rays through 180 degrees and determines intersections
    of rays with perimeter of ellipse.
    Coordinates are tuples, returns coordinates as a list going clockwise from top
    center.

    Based on http://mathworld.wolfram.com/Ellipse-LineIntersection.html

    Parameters
    ----------------------------------------
    center: tuple
        Center coordinate (x,y)
    a: float
        Semi-axis length in X direction (like 'X radius')
    b: float
        Semi-axis length in Y direction (like 'Y radius')
    n: int, optional
        Number of rays to use in the calculation.  The number of coordinates returned around your
        ellipse will be 2*n.  More rays = finer resolution = 'curvier' ellipse.  However, this takes
        longer to compute!  Consider going smaller for smaller ellipses. (default = 128)

    Returns
    -----------------------------------
    coords: list
        List of (x,y) coordinate tuples
    """
    coords_pos = []
    coords_neg = []

    n = int(np.round(n,0))

    for i in range(n):
        """
        Find point on line (x0,y0), then intersection with of ellipse with line
        passing through that point and origin of ellipse
        """
        angle = (float(i) / float(n)) * np.pi
        x0 = 100. * np.sin(angle)
        y0 = 100. * np.cos(angle)
        xpos = (a * b * x0) / np.sqrt(a ** 2 * y0 ** 2 + b ** 2 * x0 ** 2)
        xneg = -xpos
        ypos = (a * b * y0) / np.sqrt(a ** 2 * y0 ** 2 + b ** 2 * x0 ** 2)
        yneg = -ypos
        coords_pos.append((xpos + center[0], ypos + center[1]))
        coords_neg.append((xneg + center[0], yneg + center[1]))
    return coords_pos + coords_neg


########################################
########################################

class ROI():
    """
    Region of interest objects in MIPPY, as stored in MIPPYCanvas.roi_list and MIPPYCanvas.roi_list_2d

    Parameters
    -----------------------
    coords: list(tuple)
        list of tuple (x,y) coordinates defining the boundary of the ROI
    tags: list(str), optional
        List of string objects used to 'tag' the ROI on the canvas.  The list will always
        have the string 'roi' appended so ROI objects are ALWAYS tagged 'roi'. (default = [])
    roi_type: str, optional
        Specifies the type of ROI for easier processing later on.  If omitted, the type is
        established as best as possible from the ROI coordinates. (default = None)
    color: str, optional
        The color the ROI should appear on a MIPPYCanvas. Colors must be understood by
        tkinter. (default = 'yellow')
    """
    def __init__(self, coords, tags=[], roi_type=None, color='yellow'):
        """
        Expecting a string of 2- or 3-tuples to define bounding coordinates.
        Type of ROI will be inferred from number of points.
        """
        self.coords = coords
        self.color = color
        self.tags = []
        for tag in tags:
            self.tags.append(tag)
        self.uuid = str(uuid.uuid4())
        self.tags.append(str(self.uuid))
        # print("Tags in ROI init",self.tags)
        if not 'roi' in self.tags:
            self.tags.append('roi')
        if not roi_type:
            if len(coords) == 1:
                self.roi_type = "point"
            elif len(coords) == 2:
                self.roi_type = "line"
            elif (len(coords) == 4
                  and coords[0][0] == coords[3][0]
                  and coords[0][1] == coords[1][1]
                  and coords[1][0] == coords[2][0]
                  and coords[2][1] == coords[3][1]):
                self.roi_type = 'rectangle'
            elif len(coords) > len(coords[0]):
                self.roi_type = "3d"
            elif len(coords) == len(coords[0]):
                self.roi_type = "polygon"
            else:
                self.roi_type = "Unknown type"
        else:
            self.roi_type = roi_type
        arr_co = np.array(self.coords)
        self.bbox = (np.min(arr_co[:, 0]), np.min(arr_co[:, 1]), np.max(arr_co[:, 0]), np.max(arr_co[:, 1]))

        return

    def contains(self, point):
        """
        Tests whether a point (x,y) is inside or outside of the ROI object.

        Parameters
        -----------------------
        point: tuple
            (x,y) coordinate of the point of interest

        Returns
        --------------------------
        bool
            True or False
        """
        # Check whether or not the point is within the extreme bounds of the ROI
        # coordinates first...
        # Could do with a faster way of doing this. Originally used self.bbox
        # stored as an attribute, but had trouble updating dynamically with
        # a resizing canvas
##        arr_co = np.array(self.coords)
##        if (not np.amin(arr_co[:, 0]) <= point[0] <= np.amax(arr_co[:, 0])
##                or not np.amin(arr_co[:, 1]) <= point[1] <= np.amax(arr_co[:, 1])):
##            return False
        if (not self.bbox[0]<=point[0]<=self.bbox[2]
            or not self.bbox[1]<=point[1]<=self.bbox[3]):
            return False
        wn = wn_PnPoly(point, self.coords)
        if wn == 0:
            return False
        else:
            return True

    def update(self, xmove=0., ymove=0.):
        """
        Move an ROI by a specified distance in the X and Y directions (updating the ROI coordinates).
        One, both or neither distance may be specified.

        .. note::
            This does not redraw the ROI on a canvas, it only updates the ROI coordinates.  The
            canvas/ROI must be redrawn to update on screen.

        Parameters
        -----------------------
        xmove: float, optional
            The distance moved in the X direction (positive or negative)
        ymove: float, optional
            The distance moved in the Y direction (positive or negative)


        """
        if not (xmove==0 and ymove==0):
            for i in range(len(self.coords)):
                self.coords[i] = (self.coords[i][0] + xmove, self.coords[i][1] + ymove)
            self.bbox = (self.bbox[0] + xmove, self.bbox[1] + ymove, self.bbox[2] + xmove, self.bbox[3] + ymove)
            return
        else:
            arr_co = np.array(self.coords)
            self.bbox = (np.amin(arr_co[:, 0]), np.amin(arr_co[:, 1]), np.amax(arr_co[:, 0]), np.amax(arr_co[:, 1]))
        return


class ImageFlipper(Frame):
    """
    Toolbar for performing simple flip/rotate functions on images on
    an instance of MIPPYCanvas. Extends tkinter.Frame.

    The toolbar has 4 buttons:

    * Rot R (Rotate clockwise 90 degrees)
    * Rot L (Rotate anti-clockwise 90 degrees)
    * Flip H (Reflect through a vertical line down the center of the image)
    * Flip V (Reflect through a horzontal like across the center of the image)

    Functions are designed to be invoked by buttons, but could theoretically
    be invoked with a direct call.

    Parameters
    --------------------------
    master: tkinter widget
        Master object for displaying the widget (usually a ``tkinter.Frame`` instance)
    canvas: mippy.viewing.MIPPYCanvas
        MIPPYCanvas object you want the ImageFlipper toolbar to work with.


    """
    def __init__(self, master, canvas):
        Frame.__init__(self, master)
        self.canvas = canvas
        self.rot_left_button = Button(self, text="Rot L", command=lambda: self.rot_left())
        self.rot_right_button = Button(self, text="Rot R", command=lambda: self.rot_right())
        self.flip_h_button = Button(self, text="Flip H", command=lambda: self.flip_h())
        self.flip_v_button = Button(self, text="Flip V", command=lambda: self.flip_v())
        self.rot_left_button.grid(row=0, column=0, sticky='nsew')
        self.rot_right_button.grid(row=0, column=1, sticky='nsew')
        self.flip_h_button.grid(row=0, column=2, sticky='nsew')
        self.flip_v_button.grid(row=0, column=3, sticky='nsew')
        self.rowconfigure(0, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        return

    def rot_left(self):
        """
        Rotates the images through 90 degrees anticlockwise.

        """
        for im in self.canvas.images:
            im.rotate_left()
            im.wl_and_display()
        self.canvas.show_image()
        return

    def rot_right(self):
        """
        Rotates the images through 90 degrees clockwise.

        """
        for im in self.canvas.images:
            im.rotate_right()
            im.wl_and_display()
        self.canvas.show_image()
        return

    def flip_h(self):
        """
        Reflects the images about a central vertical axis.

        """
        for im in self.canvas.images:
            im.flip_horizontal()
            im.wl_and_display()
        self.canvas.show_image()
        return

    def flip_v(self):
        """
        Reflects the images about a central horizontal axis.

        """
        for im in self.canvas.images:
            im.flip_vertical()
            im.wl_and_display()
        self.canvas.show_image()
        return


class MIPPYCanvas(Canvas):
    """
    MIPPYCanvas is an extension of ``tkinter.Canvas`` with additional functionality for working with
    DICOM images and region-of-interest based image analysis.

    Parameters
    -------------------

    master: tkinter object
        The tkinter object which will hold the canvas (typically a tkinter.Frame)
    width: int, optional
        The on-screen width of the canvas in pixels (default = 256)
    height: int, optional
        The on-screen height of the canvas in pixels (default = 256)
    bd: int, optional
        Canvas border width (default = 0)
    drawing_enabled: bool, optional
        Specifies whether the canvas interacts with left-mouse clicks for ROI drawing (default = False)
    autostats: bool, optional
        If True, ROI stats will be printed to stdout immediately whenever an ROI is drawn. (default = False)
    antialias: bool, optional
        If True, antialiasing will be applied when scaling images for display. (default = True)
    use_masks: bool, optional
        If True, binary ROI masks will be generated whenever an ROI is drawn/updated. This makes it slower to
        generate the ROI, but much faster to perform stats/analysis on the ROI. (default = True)


    :ivar int active: The number of the currently displayed image, **indexed from 1** (initial value: 1)
    :ivar tkinter.StringVar active_str: ``tkinter.StringVar`` instance of ``MIPPYCanvas.active`` (so that image number can be displayed in a ``tkinter.Label``)
    :ivar bool antialias: If True, antialiasing will be applied when scaling images for display (intial value from Constuctor)
    :ivar bool autostats: If True, ROI stats will be printed to stdout immediately whenever an ROI is drawn (intial value from Contructor)
    :ivar bool drawing_enabled: Specifies whether the canvas interacts with left-mouse clicks for ROI drawing (intial value from Constructor)
    :ivar list images: The list of ``mippy.viewing.MIPPYImage`` objects currently loaded on the MIPPYCanvas (initial value: [ ])
    :ivar int height: Height of the canvas in pixels (intial value from Constructor)
    :ivar datetime.datetime last_clicked: The timestamp of the last time the canvas was drawn on using the left mouse button (initial value: ``datetime.datetime.now()``)
    :ivar tkinter.Frame master: The master tkinter widget on which the canvas is displayed
    :ivar list roi_list: List of ``mippy.viewing.ROI`` objects currently active on the displayed image (initial value: [ ])
    :ivar list roi_list_2d: 2D list of ``mippy.viewing.ROI`` objects currently active on all loaded images (initial value: [ [ ] ])
    :ivar str roi_mode: The currently active ROI drawing mode (inital value: 'rectangle')
    :ivar bool use_masks: If True, binary ROI masks will be generated whenever an ROI is drawn/updated. This makes it slower to generate the ROI, but much faster to perform stats/analysis on the ROI. (intial value from Constructor)
    :ivar int width: Width of the canvas in pixels (intial value from Constructor)
    :ivar float zoom_factor: The scaling factor applied to the raw pixel data for display on the MIPPYCanvas (initial value: 1)




    """
    def __init__(self, master, width=256, height=256, bd=0, drawing_enabled=False, autostats=False, antialias=True,
                 use_masks=True,bg='#444444',limit_loading=True):
        Canvas.__init__(self, master, width=width, height=height, bd=bd, bg=bg)
        self.master = master
        self.zoom_factor = 1
        self.roi_list = []
        self.roi_list_2d = []
        self.masks = []
        self.masks_2d = []
        if use_masks == True:
            self.use_masks = True
        else:
            self.use_masks = False
        self.shift = False
        self.roi_mode = 'rectangle'
        self.bind('<Button-1>', self.left_click)
        self.bind('<B1-Motion>', self.left_drag)
        self.bind('<ButtonRelease-1>', self.left_release)
        self.bind('<Double-Button-1>', self.left_double)
        if not platform.system() == 'Darwin':
            self.bind('<Button-3>', self.right_click)
            self.bind('<B3-Motion>', self.right_drag)
            self.bind('<ButtonRelease-3>', self.right_release)
            self.bind('<Double-Button-3>', self.right_double)
        else:
            self.bind('<Button-2>', self.right_click)
            self.bind('<B2-Motion>', self.right_drag)
            self.bind('<ButtonRelease-2>', self.right_release)
            self.bind('<Double-Button-2>', self.right_double)
        self.bind('<Configure>', self.reconfigure)
        self.bind('<Delete>',self.delete_roi)
        self.bind('<Control-KeyPress-c>',self.duplicate_roi_keyboard)
        self.bind('<Shift-Delete>',self.clear_roi_keyboard)
        self.bind('<Shift-Button-1>',self.shift_left_click)
        self.bind('<Control-KeyPress-z>',self.undo_draw)
        self.bind('<Control-Shift-KeyPress-Z>',self.redo_draw)
        self.drawing_roi = False
        self.xmouse = None
        self.ymouse = None
        self.tempx = None
        self.tempy = None
        self.tempcoords = []
        self.images = []
        self.active = 1
        self.active_str = StringVar(self)
        self.active_str.set(str(self.active))
        self.drawing_enabled = drawing_enabled
        self.width = width
        self.height = height
        self.pixel_array = None
        self.img_scrollbar = None
        self.antialias = antialias
        self.autostats = autostats
        self.last_clicked = datetime.datetime.now()
        self.limit_loading = limit_loading
        self.linked_rois = True
        self.active_rois = []
        self.roi_colors = {'default':'yellow','active':'red'}
        self.interactive_roi_colors = False
        self.double_to_clear = False
        self.roi_recycle = []

    def enable_advanced_rois(self):
        self.linked_rois = False
        self.interactive_roi_colors = True
        self.double_to_clear = True

    def reconfigure(self, event):
        """
        Detects a rescaling event and adjusts width, height attributes.
        If images are loaded on canvas, rescale images and rescale ROIs according to new zoom_factor.
        """
        self.width = event.width - 4
        self.height = event.height - 4
        if not self.images == []:
            # Already images loaded. Recalculate zoom factor and redraw
            oldzoom = self.zoom_factor
            self.zoom_factor = np.min(
                [float(self.width) / float(self.images[0].columns), float(self.height) / float(self.images[0].rows)])
            for image in self.images:
                image.wl_and_display(window=self.window, level=self.level, antialias=self.antialias,
                                     zoom=self.zoom_factor)
            self.rescale_rois(oldzoom, self.zoom_factor)
            self.show_image()
            return
        else:
            # No images loaded, shouldn't need to do anything...?
            pass

    def rescale_rois(self, oldzoom, newzoom):
        """
        Rescales ROIs to keep up with canvas when the canvas is resized.
        Only invoked by MIPPYCanvas.reconfigure()
        """
        self.roi_list_2d[self.active-1] = self.roi_list
        for im in range(len(self.images)):
            for r in range(len(self.roi_list_2d[im])):
                self.roi_list_2d[im][r].coords = self.canvas_coords(
                    self.image_coords(self.roi_list_2d[im][r].coords, zoom=oldzoom),
                    zoom=newzoom)

                self.roi_list_2d[im][r].update()   # Run update method to update roi.bbox
        self.redraw_rois()
        self.roi_list = self.roi_list_2d[self.active - 1]
        # self.update_all_roi_masks()
        return

    def configure_scrollbar(self):
        """
        This method expects that a tkinter Scrollbar object has been created as the
        attribute *img_scrollbar*. It needs to be run after the scrollbar is created to
        establish the link between the scrollbar and the canvas.

        Although the scrollbar is created as an attribute of the canvas, you will
        need to specify the window/frame you want the scrollbar to **appear**
        on as its master when you construct it.

        Example:

        .. code-block:: python

            my_window.canvas1 = MIPPYCanvas(my_window)
            my_window.canvas1.img_scrollbar = Scrollbar(my_window, orient='horizontal')
            my_window.canvas1.configure_scrollbar()
        """
        if self.img_scrollbar:
            self.img_scrollbar.config(command=self.scroll_images)
            self.img_scrollbar.set(0, 1)
        if self.active and not self.images == []:
            if not len(self.images) == 1:
                self.img_scrollbar.set(self.active - 1 / (len(self.images) - 1), self.active / (len(self.images) - 1))
            else:
                self.img_scrollbar.set(0, 1)

    def scroll_images(self, command, value, mode='unit'):
        """
        Responds to the scrollbar to display the correct image as the scrollbar moves
        """
        if command == 'scroll':
            self.show_image(self.active + int(value))
        elif command == 'moveto':
            selected_img = int(np.round((float(value) * float((len(self.images)))), 0)) + 1
            if not selected_img == self.active:
                self.show_image(selected_img)

    def update_scrollbar(self, value):
        """
        Responds to show_image to ensure the scrollbar position always reflects
        the currently displayed image
        """
        current_img = float(self.active)
        total_img = float(len(self.images))
        lo = (self.active - 1) / total_img
        hi = self.active / total_img
        self.img_scrollbar.set(lo, hi)

    def reset(self):
        """
        Unloads all images from the canvas.

        .. note::
            Does not automatically remove ROIs from the list, they are only removed
            when a new set of images are loaded with ``MIPPYCanvas.load_images()``.
        """
        self.images = []
        self.delete('all')
        self.active = 1

    def show_image(self, num=None, recalculate=False):
        """
        Display the requested image.

        Parameters
        -------------------
        num: int
            The required image number, **indexed from 1**.


        """
        if len(self.images) == 0:
            return
        if num and not num < 1 and not num > len(self.images):
            self.active = num
            self.active_str.set(str(num) + "/" + str(len(self.images)))
            self.update_scrollbar((num - 1.) / len(self.images))
        self.delete('image')
        if recalculate:
            for i in range(len(self.images)):
                self.images[i].wl_and_display(window=self.window, level=self.level, zoom=self.zoom_factor,antialias=self.antialias)
        self.create_image((0, 0), image=self.images[self.active - 1].photoimage, anchor='nw', tags='image')
        self.tag_lower('image')
        self.roi_list = self.roi_list_2d[self.active - 1]
        self.masks = self.masks_2d[self.active - 1]
        self.redraw_rois()
        self.tag_raise('layer5')
        self.tag_raise('layer4')
        self.tag_raise('layer3')
        self.tag_raise('layer2')
        self.tag_raise('layer1')

    def quick_redraw_image(self):
        """
        Does a quick redraw of the image layer on the canvas without recalculating
        the PhotoImage or any other objects, intended only to force the canvas to
        update.
        """
        try:
            self.delete('image')
            self.create_image((0, 0), image=self.images[self.active - 1].photoimage, anchor='nw', tags='image')
            self.tag_lower('image')
        except:
            pass
        try:
            self.tag_raise('roi')
        except:
            pass

    def update_roi_masks(self):
        """
        Recalculates the binary masks for all ROIs on the active image
        """
        if self.roi_list == []:
            self.masks = []
            return
        width = self.get_active_image().columns
        height = self.get_active_image().rows

        mask = np.zeros((len(self.roi_list), height, width))

        for y in range(height):
            for x in range(width):
                for i in range(len(self.roi_list)):
                    minx = self.roi_list[i].bbox[0]/self.zoom_factor
                    maxx = self.roi_list[i].bbox[2]/self.zoom_factor
                    miny = self.roi_list[i].bbox[1]/self.zoom_factor
                    maxy = self.roi_list[i].bbox[3]/self.zoom_factor
                    #print("{} {} {} {} {} {}".format(x,y,minx,maxx,miny,maxy))
                    if not minx <= x <= maxx or not miny <= y <= maxy:
                        continue
                    if self.roi_list[i].contains((x * self.zoom_factor, y * self.zoom_factor)):
                        mask[i, y, x] = 1
        self.masks = mask
        self.masks_2d[self.active - 1] = mask

        return

    def update_all_roi_masks(self):
        """
        Cycles through all images loaded onto a canvas and recalculates the binary masks for all ROIs
        """
        i = -1
        for roilist in self.roi_list_2d:
            i += 1
            if roilist == []:
                continue
            else:
                print(str(len(roilist)) + " ROIs found on image " + str(i + 1))
                height = self.images[i].rows
                width = self.images[i].columns
                print(width, height)
                mask = np.zeros((len(roilist), height, width))
                for y in range(height):
                    for x in range(width):
                        for r in range(len(roilist)):
                            if roilist[r].contains((x * self.zoom_factor, y * self.zoom_factor)):
                                mask[r, y, x] = 1
                self.masks_2d[i] = mask
                self.masks = self.masks_2d[self.active - 1]
        return

    def get_roi_pixels(self, rois=[], tags=[]):
        """
        Returns a LIST of pixel values from an ROI.  This list has no shape, and needs
        converting to a ``numpy.ndarray`` to be able to do any useful stats on it.

        Parameters
        -----------------------
        rois: list(int), optional
            List of indices.  If specified, only the specified positions in
            ``MIPPYCanvas.roi_list`` will be analysed.
        tags: list(str), optional
            List of tags.  If specified, only ROIs with any of the specified tags will
            be analysed.

        Returns
        -----------------------
        px_list: list
            1D list of pixel values
        """
        im = self.get_active_image()
        if len(self.roi_list)==0:
            return []
        if len(rois) == 0:
            rois = list(range(len(self.roi_list)))
        if len(self.masks) == 0:
            px = []
            for y in range(im.rows):
                for x in range(im.columns):
                    j = 0
                    for i in rois:
                        if len(tags) > 0 and not any([tag in self.roi_list[i].tags for tag in tags]):
                            continue
                        if j == len(px):
                            px.append([])
                        if self.roi_list[i].contains((x * self.zoom_factor, y * self.zoom_factor)):
                            px[j].append(im.px_float[y][x])
                        j += 1
            return px
        else:
            px = []
            pxflat = im.px_float.flatten().tolist()
            for i in rois:
                if len(tags) > 0 and not any([tag in self.roi_list[i].tags for tag in tags]):
                    continue
                maskflat = self.masks[i, :, :].flatten().tolist()
                pxlist = [pxflat[ind] for ind, val in enumerate(maskflat) if val > 0]
                px.append(pxlist)

            return px

    def get_roi_statistics(self, rois=[], tags=[]):
        """
        Returns some statistics from ROIs on the canvas.  The stats are returned as a
        dictionary, where each key contains the values per-ROI as a list.

        Available stats (use these as dictionary keys, as shown in the example):

        * **mean** (mean value)
        * **min** (minimum value)
        * **max** (maximu value)
        * **std** (standard deviation)
        * **mode** (modal value)
        * **skewness** (skewness of the distribution)
        * **kurtosis** (kurtosis of the distribution)
        * **cov** (coefficient of variation)
        * **sum** (sum of all values)
        * **area_px** (number of pixels within the ROI)

        Example:

        .. code-block:: python

            stats = my_window.canvas1.get_roi_statistics()

            # To get the mean of the first ROI...
            val = stats['mean'][0]


        Parameters
        -----------------------
        rois: list(int), optional
            List of indices.  If specified, only the specified positions in
            ``MIPPYCanvas.roi_list`` will be analysed.
        tags: list(str), optional
            List of tags.  If specified, only ROIs with any of the specified tags will
            be analysed.

        Returns
        -----------------------
        stats: dict
            Results as a dictionary

        """
        if len(self.roi_list) < 1:
            return None
        if self.roi_list[0].roi_type == 'line':
            return None
        px_list = self.get_roi_pixels(rois=rois, tags=tags)
        for i in range(len(px_list)):
            if len(px_list[i]) == 0:
                px_list[i] = [0., 0., 0.]
        stats = {
            'mean': list(map(np.mean, px_list)),
            'std': list(map(np.std, px_list)),
            'min': list(map(np.min, px_list)),
            'max': list(map(np.max, px_list)),
            'mode': list(map(sps.mode, px_list)),
            'skewness': list(map(sps.skew, px_list)),
            'kurtosis': list(map(sps.kurtosis, px_list)),
            'cov': list(map(sps.variation, px_list)),
            'sum': list(map(np.sum, px_list)),
            'area_px': list(map(len, px_list))
        }
        return stats

    def get_profile(self, resolution=1, width=1, interpolate=False, direction='horizontal', index=0):
        """
        Returns a line profile from the image, with interpolation when required.

        Parameters
        ---------------------
        resolution: float, optional
            The spacing between points in the profile, measured in pixels (default = 1)
        width: int, optional
            The width of the profile that should be averaged across, in pixels. Only applies
            with a 'line' ROI type. (default = 1)
        interpolate: bool, optional
            Whether or not interpolation should be performed. If False, nearest neighbour
            pixel values are taken.  If true, bilinear interpolation is used.  False is not
            recommended when using resolutions <1. (default = False)
        direction: str, optional
            Only applies when using a 'rectangle' ROI 'horizontal' or 'vertical'.  If
            'horizontal', pixels are averaged vertically to form a 1D profile.  If
            'vertical', the opposite applies. (default = 'horizontal')
        index: int, optional
            The ROI to be used for the profile, with ``index`` representing the position
            in ``MIPPYCanvas.roi_list``. (default = 0)

        Returns
        -------------------------
        profile: numpy.ndarray
            1D numpyndarray of the values in the profile
        x: numpy.ndarray
            1D numpy.ndarray of the length (x) position of each point in the profile, in pixels

        """

        if not (self.roi_list[index].roi_type == 'line' or self.roi_list[index].roi_type == 'rectangle'):
            print("Not a valid ROI type for profile.  Line or rectangle required.")
            return None

        roi = self.roi_list[index]
        coords = roi.coords / self.zoom_factor

        if roi.roi_type == 'line':
            profile_length = np.sqrt((coords[1][0] - coords[0][0]) ** 2 + (coords[1][1] - coords[0][1]) ** 2)
        elif direction == 'horizontal':
            profile_length = coords[1][0] - coords[0][0]
        elif direction == 'vertical':
            profile_length = coords[3][1] - coords[0][1]
        else:
            print("Profile direction not understood!")
            return None

        length_int = int(np.round(profile_length / resolution, 0))
        if interpolate:
            intorder = 1
        else:
            intorder = 0

        profile = None

        if roi.roi_type == 'line':
            x_arr = np.linspace(coords[0][0], coords[1][0], length_int)
            y_arr = np.linspace(coords[0][1], coords[1][1], length_int)

            profile = spim.map_coordinates(self.get_active_image().px_float, np.vstack((y_arr, x_arr)), order=intorder,
                                           prefilter=False)

        elif direction == 'horizontal':
            y_len = int(np.round(coords[3][1] - coords[0][1], 0))
            x_arr = np.linspace(coords[0][0], coords[1][0], length_int)
            profiles = np.zeros((y_len, len(x_arr)))
            for i in range(y_len):
                y_arr = np.zeros(np.shape(x_arr)) + coords[0][1] + i
                profiles[i] = spim.map_coordinates(self.get_active_image().px_float, np.vstack((y_arr, x_arr)),
                                                   order=intorder, prefilter=False)
            profile = np.mean(profiles, axis=0)
        elif direction == 'vertical':
            x_len = int(np.round(coords[1][0] - coords[0][0], 0))
            y_arr = np.linspace(coords[0][1], coords[3][1], length_int)
            profiles = np.zeros((x_len, len(y_arr)))
            for i in range(x_len):
                x_arr = np.zeros(np.shape(y_arr)) + coords[0][0] + i
                profiles[i] = spim.map_coordinates(self.get_active_image().px_float, np.vstack((y_arr, x_arr)),
                                                   order=intorder, prefilter=False)
            profile = np.mean(profiles, axis=0)

        return profile, np.array(list(range(length_int))) * resolution

    def new_roi(self, coords, tags=[], system='canvas', color='yellow'):
        """
        Generates a new ROI from a set of coordinates.  Coordinates can be in 'canvas'
        coordinates or 'image' coordinates.

        Usually called from within MIPPY rather than being invoked directly.  For easier
        ways of generating ROIs programmatically, see ``roi_rectangle``, ``roi_circle`` and
        ``roi_ellipse``.

        Tags can be used to define the ROI appearance (e.g. dashed borders, stippled appearance).  Please see
        :ref:`useful-roi-tags` for more information.

        Parameters
        ----------------------------

        coords: list(tuple)
            List of (x,y) tuple coordinates defining the boundary of the ROI in a
            clockwise direction.
        tags: list(str), optional
            List of tags for the ROI.  The tags can be used to identify the ROI at a later
            date.  ``'roi'`` is always appended to this list, so all ROIs have the tag
            ``'roi'``. (default = [ ])
        system: str, optional
            Either ``'canvas'`` or ``'image'`` to identify the coordinate system/reference
            used for ``coords``. (default = 'canvas')
        color: str, optional
            Color in which the ROI will be drawn - must be understood by tkinter
            (default = 'yellow')

        """
        if system == 'image':
            coords = self.canvas_coords(coords)
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        if not 'roi' in tags:
            tags.append('roi')
        self.add_roi(coords, tags=tags, color=color)
        self.redraw_rois()
        return

    def draw_roi(self, coords, tags=[], color='yellow'):
        """
        Draw the ROI defined by its bounding coordinates on the canvas.  The tags can be
        used to define the ROI appearance (e.g. dashed borders, stippled appearance).

        Please see :ref:`useful-roi-tags` for more information.

        Parameters
        ---------------------------

        coords: list(tuple)
            Coordinates as a list of (x,y) tuples defining the boundary of the ROI
        tags: list(str), optional
            List of tags to be attached to the ROI; can be used to define the
            appearance of the ROI or select ROIs for statistics/analysis (default = [ ])
        color: str, optional
            Color of the ROI (default = 'yellow')

        """
        if not 'roi' in tags:
            tags.append('roi')
        # print(tags)

        if not 'polygon' in tags:
            for i in range(len(coords)):
                if 'invisible' in tags:
                    continue
                j = i + 1
                if j == len(coords):
                    j = 0
                if not 'dash' in tags:
                    self.create_line((coords[i][0], coords[i][1], coords[j][0], coords[j][1]), fill=color, width=1,
                                     tags=tags)
                else:
                    if 'dash42' in tags:
                        self.create_line((coords[i][0], coords[i][1], coords[j][0], coords[j][1]), fill=color, width=1,
                                         tags=tags, dash=(4, 2))
                    elif 'dash44' in tags:
                        self.create_line((coords[i][0], coords[i][1], coords[j][0], coords[j][1]), fill=color, width=1,
                                         tags=tags, dash=(4, 4))
                    elif 'dash22' in tags:
                        self.create_line((coords[i][0], coords[i][1], coords[j][0], coords[j][1]), fill=color, width=1,
                                         tags=tags, dash=(2, 2))
                    else:
                        print("Dash/gap length not specified. Use the tag 'dashAB' where A is dash length and B is gap length.")
                        return
            return
        elif 'polygon' in tags:
            coords = np.array(coords).flatten()
            if 'stipple' in tags:
                if 'gray25' in tags:
                    self.create_polygon(*coords, fill=color, width=1, stipple='gray25', tags=tags, outline=color)
                    return
                elif 'gray12' in tags:
                    self.create_polygon(*coords, fill=color, width=1, stipple='gray12', tags=tags, outline=color)
                    return
                elif 'gray50' in tags:
                    self.create_polygon(*coords, fill=color, width=1, stipple='gray50', tags=tags, outline=color)
                    return
                elif 'gray75' in tags:
                    self.create_polygon(*coords, fill=color, width=1, stipple='gray75', tags=tags, outline=color)
                    return
                else:
                    print("Stipple type not specified. Add a stipple type as a tag. See tkinter create_rectangle docs for details")
                    return
            else:
                self.create_polygon(*coords, fill=color, width=1, tags=tags, outline=color)
                return
        return

    def redraw_rois(self):
        # color option is redundant, I think...
        """
        Redraws all ROIs on the active slice without redrawing the image.
        """
        self.delete('roi')
        for roi in self.roi_list:
            # print("Tags at redrawing",roi.tags)
            self.draw_roi(roi.coords, tags=roi.tags, color=roi.color)
        return

    def delete_roi(self,event):
        """
        Deletes the active ROI(s)
        """
        for roi in self.active_rois:
            self.delete(roi.uuid)
            self.roi_recycle.append(roi)
        while len(self.roi_recycle)>10:
            self.roi_recycle.pop(0)
        self.roi_list = [i for i in self.roi_list if not i in self.active_rois]
        self.active_rois = []
        return

    def roi_rectangle(self, x_start, y_start, width, height, tags=[], system='canvas', color='yellow'):
        """
        Adds a rectangular ROI to the image.

        Parameters
        ---------------------------

        x_start: float
            X-coordinate of the top-left corner of the ROI
        y_start: float
            Y-coordinate of the top-left corner of the ROI
        width: float
            Width of the ROI
        height: float
            Height of the ROI
        tags: list(str), optional
            Tags to be added to the ROI (default = [ ]) - :ref:`useful-roi-tags`
        system: str, optional
            Coordinate system being used for coordinates provided; 'canvas' or 'image' (default = 'canvas')
        color: str, optional
            Color of the ROI; must be understandable by tkinter (default = 'yellow')

        """
        x1 = x_start
        x2 = x_start + width
        y1 = y_start
        y2 = y_start + height
        if system == 'image':
            x1 = x1 * self.zoom_factor
            x2 = x2 * self.zoom_factor
            y1 = y1 * self.zoom_factor
            y2 = y2 * self.zoom_factor
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        self.new_roi([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], tags=tags, color=color)
        return

    def roi_circle(self, center, radius, tags=[], system='canvas', resolution=128, color='yellow'):
        """
        Adds a circular ROI to the image.

        Parameters
        ----------------------------

        center: tuple
            (x,y) coordinate of the center of the circle
        radius: float
            Radius of the ROI
        tags: list(str), optional
            Tags to be added to the ROI (default = [ ]) - :ref:`useful-roi-tags`
        system: str, optional
            Coordinate system being used for coordinates provided; 'canvas' or 'image' (default = 'canvas')
        color: str, optional
            Color of the ROI; must be understandable by tkinter (default = 'yellow')

        """
        coords = get_ellipse_coords(center, radius, radius, resolution)
        if system == 'image':
            for i in range(len(coords)):
                coords[i] = tuple(x * self.zoom_factor for x in coords[i])
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        self.new_roi(coords, tags=tags, color=color)
        return

    def roi_ellipse(self, center, radius_x, radius_y, tags=[], system='canvas', resolution=128, color='yellow'):
        """
        Adds a circular ROI to the image.

        Parameters
        ----------------------------

        center: tuple
            (x,y) coordinate of the center of the circle
        radius_x: float
            Semi-axis of the ellipse in the X direction
        radius_y: float
            Semi-axis of the ellipse in the Y direction
        tags: list(str), optional
            Tags to be added to the ROI (default = [ ]) - :ref:`useful-roi-tags`
        system: str, optional
            Coordinate system being used for coordinates provided; 'canvas' or 'image' (default = 'canvas')
        resolution: int, optional
            Number of points used to describe one half of the ROI boundary (default = 128)
        color: str, optional
            Color of the ROI; must be understandable by tkinter (default = 'yellow')

        """
        coords = get_ellipse_coords(center, radius_x, radius_y, resolution)
        if system == 'image':
            for i in range(len(coords)):
                coords[i] = tuple(x * self.zoom_factor for x in coords[i])
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        self.new_roi(coords, tags=tags, color=color)
        return

    def set_lut(self,lut):
        for i in range(len(self.images)):
            if not lut==None:
                self.images[i].lut=open_lut(lut)
            else:
                self.images[i].lut=None
        return

    def load_images(self, image_list, keep_rois=False, limitbitdepth=False, lut=None, pad_zero=False):
        """
        Loads images onto the canvas, autoscaling pixel values where appropriate
        and automatically windowing to the full range of pixel values provided.

        ``mippy.viewing.MIPPYImage`` objects will be created for all images passed in,
        which are added to ``MIPPYCanvas.images`` (a list).

        There is a hard-coded limit of 500 images that can be loaded onto the canvas.
        If you attempt to load a list of images longer than 500, only the first 500
        will be displayed.

        .. note::
            The image_list object must be a 1D list of objects.  These objects can be:

            * ``pydicom.Dataset.Dataset`` or ``pydicom.Dataset.FileDataset``
            * ``str`` absolute paths to DICOM files on the disk
            * 2-dimensional ``numpy.ndarray`` objects of pixel data to be loaded directly onto the canvas.


        Parameters
        --------------------------
        image_list: list
            List of images to be loaded.  See the note above for allowed object types.
        keep_rois: bool, optional
            If ``True``, any ROIs present on the canvas will be preserved if the image
            geometry (slices, height, width) is the same as the currently loaded images.
            (default = False)
        limitbitdepth: bool, optional
            If ``True``, all pixels will be automatically scaled to 8-bit integer values
            in order to limit memory usage and speed up image loading.  This is used in
            the preview window in the main MIPPY GUI. (default = False)
        """
        self.images = []
        self.delete('all')
        if not keep_rois or not len(self.roi_list_2d) == len(image_list):
            # Will replace ROIs no matter what if you load a
            # different number of images
            self.roi_list_2d = []
            self.masks_2d = []

        self.roi_list = []
        self.masks = []
        self.pad_zero=pad_zero
        n = 0

        if len(image_list) > 500 and self.limit_loading:
            print("More than 500 images - cannot be loaded to canvas.")
            print("Loading first 500 only...")
            image_list = image_list[0:100]

        for ref in image_list:
            self.progress(45. * n / len(image_list) + 10)
            self.images.append(MIPPYImage(ref,
                                          limitbitdepth=limitbitdepth,lut=lut,
                                          pad_zero=self.pad_zero))  # Included limitbitdepth to allow restriction to 8 bit int
            if not keep_rois or not len(self.roi_list_2d) == len(image_list):
                self.roi_list_2d.append([])
                self.masks_2d.append([])
            n += 1

        self.global_min, self.global_max = get_global_min_and_max(self.images)
        self.fullrange = self.global_max - self.global_min
        self.default_window = self.global_max - self.global_min
        self.default_level = self.global_min + self.default_window / 2
        self.level = self.default_level
        self.window = self.default_window
        self.zoom_factor = np.min(
            [float(self.width) / float(self.images[0].columns), float(self.height) / float(self.images[0].rows)])

        for i in range(len(self.images)):
            self.progress(45. * i / len(self.images) + 55)
            self.images[i].wl_and_display(window=self.window, level=self.level, zoom=self.zoom_factor,
                                          antialias=self.antialias)

        # ~ from mippy.misc import deep_getsizeof,getsizeof
        # ~ print np.round(float(deep_getsizeof(self.images,set()))/1024./1024,3),"MB (deep_getsizeof)"
        # ~ print np.round(float(getsizeof(self.images))/1024./1024,3),"MB (pympler asizeof)"

        self.configure_scrollbar()

        self.show_image(1)

        self.progress(0.)
        return

    def get_active_image(self):
        """
        Returns the ``mippy.viewing.MIPPYImage`` object for the
        image currently being displayed.

        Returns
        -------------
        image: mippy.viewing.MIPPYImage

        """
        return self.images[self.active - 1]

    def get_3d_array(self):
        """
        If all images on the canvas are of the same dimensions, this returns
        the pixel data of the whole image stack as a 3-dimensional
        ``numpy.ndarray``.

        .. warning::
            The axes of this array may seem counter-intuitive to those less
            familiar with the python concept of 'slicing'.

            * Axis 0 = image number (z)
            * Axis 1 = row number (y)
            * Axis 2 = column number (x)

            So you would reference pixel (100,250) in your 7th image as:

            .. code-block:: python

                px_data = my_canvas.get_3d_array()
                # Either of the below are acceptable
                val = px_data[6][250][100]
                val = px_data[6,250,100]


        Returns
        -----------------
        px_array: numpy.ndarray
            3-dimensional array of pixel data.

        """
        px_array = []
        for image in self.images:
            px_array.append(image.px_float)
        px_array = np.array(px_array)
        return px_array

    def reset_window_level(self):
        """
        Resets the window/level of the canvas to the full range of pixel values loaded.
        """
        self.temp_window = self.default_window
        self.temp_level = self.default_level
        self.window = self.default_window
        self.level = self.default_level

        for image in self.images:
            image.wl_and_display(window=self.default_window, level=self.default_level)
        self.show_image(self.active)
        return

    def shift_left_click(self,event):
        self.focus_set()
        self.xmouse = event.x
        self.ymouse = event.y
        self.tempx = event.x
        self.tempy = event.y
        for roi in self.roi_list:
            if roi.contains((self.xmouse, self.ymouse)):
                roi.color = self.roi_colors['active']
                if not roi in self.active_rois:
                    self.active_rois.append(roi)
        self.redraw_rois()

    def left_click(self, event):
        """
        Check if drawing enabled, and then check if inside or outside an ROI and act accordingly.

        If inside, move.  If outside (or if no ROI), clear ROIs and start drawing a new one.
        """
        if not self.drawing_enabled:
            return
        self.focus_set()
        self.xmouse = event.x
        self.ymouse = event.y
        self.tempx = event.x
        self.tempy = event.y
        self.active_rois = []
        moving = False
        for roi in self.roi_list:
            # print("UUID",roi.uuid)
            # print("Tags",roi.tags)
            current_color = roi.color
            # print(current_color)
            if roi.contains((self.xmouse, self.ymouse)):
                moving = True
                if not self.linked_rois:
                    if self.interactive_roi_colors:
                        roi.color = self.roi_colors['active']
                    if not roi in self.active_rois:
                        self.active_rois.append(roi)

            else:
                if self.interactive_roi_colors and not self.linked_rois:
                    roi.color = self.roi_colors['default']
        self.redraw_rois()

        if not moving:
            self.drawing_roi = True
            # Need to add stuff to detect if "shift" or "ctrl" held when drawing, as
            # in this case, don't want to delete existing ROIs
            if not self.double_to_clear:
                self.delete_rois()
            self.temp = []
            self.tempcoords.append((self.xmouse, self.ymouse))

    def left_drag(self, event):
        """
        Check roi_type and incrementally redraw ROI as required by mouse movement.

        This will need editing in order to handle ROIs individually.
        """

        if not self.drawing_enabled:
            return
        xmove = event.x - self.tempx
        ymove = event.y - self.tempy
        if self.drawing_roi:
            if self.interactive_roi_colors:
                roi_color = self.roi_colors['active']
            else:
                roi_color='yellow'
            if self.roi_mode == 'rectangle' or self.roi_mode == 'ellipse':
                self.delete('roi_drawing')
            if self.roi_mode == 'rectangle':
                self.create_rectangle((self.xmouse, self.ymouse, event.x, event.y), fill='', outline=roi_color,
                                      tags='roi_drawing')
            elif self.roi_mode == 'ellipse':
                self.create_oval((self.xmouse, self.ymouse, event.x, event.y), fill='', outline=roi_color, tags='roi_drawing')
            elif self.roi_mode == 'freehand':
                self.create_line((self.tempx, self.tempy, event.x, event.y), fill=roi_color, width=1, tags='roi_drawing')
                self.tempcoords.append((event.x, event.y))
            elif self.roi_mode == 'line':
                self.delete('roi_drawing')
                self.create_line((self.xmouse, self.ymouse, event.x, event.y), fill=roi_color, width=1, tags='roi_drawing')

        else:
            if not self.linked_rois:
                # print(datetime.datetime.now(), len(self.active_rois))
                for roi in self.active_rois:
                    # print(roi.uuid)
                    # print(self.find_withtag(roi.uuid))
                    self.move(roi.uuid, xmove, ymove)
            else:
                self.move('roi', xmove, ymove)

        self.tempx = event.x
        self.tempy = event.y

    def left_release(self, event):
        """
        Stop drawing ROIs and create the ROI objects.
        """
        if not self.drawing_enabled:
            return
        self.last_clicked = datetime.datetime.now()
        if self.drawing_roi:
            if not self.double_to_clear:
                self.roi_list = []
            if self.interactive_roi_colors:
                roi_color = self.roi_colors['active']
            else:
                roi_color='yellow'
            if self.roi_mode == 'rectangle':
                self.add_roi(
                    [(self.xmouse, self.ymouse), (event.x, self.ymouse), (event.x, event.y), (self.xmouse, event.y)],color=roi_color)
                # self.draw_roi([(self.xmouse, self.ymouse), (event.x, self.ymouse), (event.x, event.y), (self.xmouse, event.y)],color=roi_color)
            elif self.roi_mode == 'ellipse':
                positive_coords = []
                negative_coords = []
                # http://mathworld.wolfram.com/Ellipse-LineIntersection.html
                # get points in circle by incrementally adding rays from centre
                # and getting intersections with ellipse
                bbox = self.bbox('roi_drawing')
                a = (bbox[2] - bbox[0]) / 2
                b = (bbox[3] - bbox[1]) / 2
                c = (bbox[0] + a, bbox[1] + b)
                self.add_roi(get_ellipse_coords(c, a, b, n=2 * max([a, b])),color=roi_color)
                # self.draw_roi(get_ellipse_coords(c, a, b, n=2 * max([a, b])),color=roi_color)
                # coords = self.roi_list[-1].coords
            elif self.roi_mode == 'line':
                self.add_roi([(self.xmouse, self.ymouse), (event.x, event.y)],color=roi_color)
            else:
                # Freehand
                self.create_line((self.tempx, self.tempy, self.xmouse, self.ymouse), fill=roi_color, width=1, tags='roi_drawing')
                if len(self.tempcoords) > 1:
                    self.add_roi(self.tempcoords,color=roi_color)
                    # self.draw_roi(self.tempcoords,color=roi_color)
                    self.delete('roi_drawing')
                else:
                    self.delete('roi_drawing')
            self.drawing_roi = False
        else:
            total_xmove = event.x - self.xmouse
            total_ymove = event.y - self.ymouse
            if len(self.roi_list) > 0:
                for roi in self.roi_list:
                    if len(self.active_rois)>0:
                        if roi in self.active_rois:
                            roi.update(total_xmove,total_ymove)
                    else:
                        roi.update(total_xmove, total_ymove)
                if self.use_masks:
                    self.update_roi_masks()
        if self.autostats == True:
            print(self.get_roi_statistics())
        self.tempcoords = []
        self.tempx = None
        self.tempy = None
        self.delete('roi_drawing')
        self.redraw_rois()

    def left_double(self, event):
        if self.double_to_clear:
            self.delete_rois()

    def right_click(self, event):
        """
        Prepare to adjust window and level by recording the starting mouse position
        """
        if self.images == []:
            # If no active display slices, just skip this whole function
            return
        self.xmouse = event.x
        self.ymouse = event.y

    def right_drag(self, event):
        """
        Adjust window and level.
        Key parameters here are sensitivity of mouse controls. Higher numbers = slower changes.
        That's kinda backwards...
        """
        xmove = event.x - self.xmouse
        ymove = event.y - self.ymouse
        # Windowing is applied to the series as a whole...
        # Sensitivity needs to vary with the float pixel scale.  Map default window
        # (i.e. full range of image) to "sensitivity" px motion => 1px up/down adjusts level by
        # "default_window/sensitivity".  1px left/right adjusts window by
        # "default_window/sensitivity"
        window_sensitivity = 300
        level_sensitivity = 500
        min_window = self.fullrange / 255
        i = self.active - 1
        self.temp_window = self.window + xmove * (self.fullrange / window_sensitivity)
        self.temp_level = self.level - ymove * (self.fullrange / level_sensitivity)
        if self.temp_window < min_window:
            self.temp_window = min_window
        if self.temp_level < self.global_min + min_window / 2:
            self.temp_level = self.global_min + min_window / 2
        self.images[i].wl_and_display(window=self.temp_window, level=self.temp_level, antialias=self.antialias)
        self.quick_redraw_image()

    def right_release(self, event):
        """
        Store the current window and level values on the canvas
        """
        if abs(self.xmouse - event.x) < 1 and abs(self.ymouse - event.y) < 1:
            return
        self.set_window_level(self.temp_window, self.temp_level)

    def undo_draw(self,event):
        self.delete_last_roi()

    def redo_draw(self,event):
        self.restore_last_roi()

    def restore_last_roi(self):
        """
        Restore the last ROI deleted with undo
        """
        if len(self.roi_recycle)>0:
            self.roi_list.append(self.roi_recycle[-1])
            self.roi_recycle.pop(-1)
            self.redraw_rois()
        return

    def delete_last_roi(self):
        """
        Remove the last ROI created
        """
        if len(self.roi_list)>0:
            self.roi_recycle.append(self.roi_list[-1])
            while len(self.roi_recycle)>10:
                self.roi_recycle.pop(0)
            self.roi_list.pop(-1)
            self.roi_list_2d[self.active-1] = self.roi_list
            self.redraw_rois()
        return

    def set_window_level(self, window, level):
        """
        Programatically set a new window and level value rather than using mouse interaction.

        Parameters
        ---------------
        window: float
            The width of the window
        level: float
            The center value of the window
        """
        self.window = window
        self.level = level
        for image in self.images:
            image.wl_and_display(window=self.window, level=self.level, antialias=self.antialias)
        self.show_image()
        return

    def right_double(self, event):
        """
        Reset window and level to default values
        """
        if self.images == []:
            return

        self.temp_window = self.default_window
        self.temp_level = self.default_level
        self.window = self.default_window
        self.level = self.default_level

        for image in self.images:
            image.wl_and_display(window=self.default_window, level=self.default_level, antialias=self.antialias)
        self.show_image(self.active)

    def add_roi(self, coords, tags=['roi'], roi_type=None, color='yellow'):
        """
        Generates the ``mippy.viewing.ROI`` object and updates the canvas ROI lists.

        Usually called as part of ``MIPPYCanvas.new_roi()``.

        Parameters
        -------------
        coords: list(tuple)
            List of (x,y) coordinate tuples
        tags: list(str), optional
            List of tags to be applied to the ROI.  For useful tags, see :ref:`useful-roi-tags`. (default = ['roi'])
        roi_type: str, optional
            ROI type; can be 'rectangle','ellipse','freehand','line'.  If None specified, it will be
            automatically determined from the coordinates provided. (default = None)
        color: str, optional
            Color of the ROI to be displayed on the canvas; must be a color recognised by tkinter (default = 'yellow')

        """
        if not 'roi' in tags:
            tags.append('roi')
        self.roi_list.append(ROI(coords, tags, roi_type, color=color))
        bbox = self.bbox('roi')
        # DEBUGGING: This line was to draw location of bounding box
        # self.create_rectangle((bbox[0],bbox[1],bbox[2],bbox[3]),outline='cyan',tags='roi')
        self.roi_list_2d[self.active - 1] = self.roi_list
        if self.use_masks:
            self.update_roi_masks()
        return

    def clear_roi_keyboard(self,event):
        self.delete_rois()
        return

    def duplicate_roi_keyboard(self,event):
        self.duplicate_roi()
        return

    def duplicate_roi(self):
        for roi in self.roi_list:
            if roi in self.active_rois:
                offset_coords = []
                for coord in roi.coords:
                    offset_coords.append((coord[0]+10,coord[1]+10))
                self.add_roi(offset_coords)
        self.redraw_rois()
        return

    def delete_rois(self):
        """
        Deletes all objects with the tag 'roi' on the canvas.
        """
        self.roi_list = []
        self.masks = []
        gc.collect()
        self.delete('roi')
        return

    def save_rois(self,savepath=None):
        """
        Saves all ROIs from the current active image only.
        If you want to save all ROIs across all slices, loop the function
        yourself.

        Parameters
        ----------------
        savepath: str, optional
            The absolute path at with which the ROI set should be saved.  If no path is provided, a
            save file dialog box is opened to generate the path. (default = None)

        """

        # Transform coordinates to image coordinates for saving
        # This is a bit of a fudge to ensure coordinates are loaded
        # correctly when loading onto a different size canvas
        for roi in self.roi_list:
            roi.coords = self.image_coords(roi.coords)
            bbox_coords = self.image_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
            roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

        if savepath is None:
            from tkinter import filedialog
            savepath = filedialog.asksaveasfilename(filetypes=[("MIPPY Object","*.obj")],
                                                        defaultextension=".obj",parent=self.master)
        if savepath is None:
            return
        if not os.path.exists(os.path.split(savepath)[0]):
            os.makedirs(os.path.split(savepath)[0])
        with open(savepath,'wb') as f:
            pickle.dump(self.roi_list,f)

        # Put ROI coordinates back to where they need to be
        for roi in self.roi_list:
            roi.coords = self.canvas_coords(roi.coords)
            bbox_coords = self.canvas_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
            roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

        return

    def save_multislice_rois(self,savepath=None):
        """
        Saves all ROIs from all slices as a single file.

        Parameters
        ----------------
        savepath: str, optional
            The absolute path at with which the ROI set should be saved.  If no path is provided, a
            save file dialog box is opened to generate the path. (default = None)

        """

        # Transform coordinates to image coordinates for saving
        # This is a bit of a fudge to ensure coordinates are loaded
        # correctly when loading onto a different size canvas
        for roi_list in self.roi_list_2d:
            for roi in roi_list:
                roi.coords = self.image_coords(roi.coords)
                bbox_coords = self.image_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
                roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

        if savepath is None:
            from tkinter import filedialog
            savepath = filedialog.asksaveasfilename(filetypes=[("MIPPY Object","*.obj")],
                                                        defaultextension=".obj",parent=self.master)
        if savepath is None:
            return

        if not os.path.exists(os.path.split(savepath)[0]):
            os.makedirs(os.path.split(savepath)[0])

        with open(savepath,'wb') as f:
            pickle.dump(self.roi_list_2d,f)

        # Put ROI coordinates back to where they need to be
        for roi_list in self.roi_list_2d:
            for roi in roi_list:
                roi.coords = self.canvas_coords(roi.coords)
                bbox_coords = self.canvas_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
                roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

    def load_multislice_rois(self,loadpath=None):
        """
        Loads all ROIs from a file to all open slices.
        If you want to load ROIs across multiple slices, loop the function
        yourself.

        Parameters
        ----------------
        loadpath: str, optional
            The absolute path at with which the ROI set is saved.  If no path is provided, a
            load file dialog box is opened to generate the path. (default = None)

        """
        if loadpath is None:
            from tkinter import filedialog
            loadpath = filedialog.askopenfilename(filetypes=(("MIPPY Object","*.obj"),("All files",'*')),title="Select ROI set to load",
                                                    parent = self.master)
        if loadpath is None:
            return
        with open(loadpath,'rb') as f:
            self.roi_list_2d = pickle.load(f)

        # Transform coordinates to canvas coordinates after loading
        # This is a bit of a fudge to ensure coordinates are loaded
        # correctly when loading onto a different size canvas
        for roi_list in self.roi_list_2d:
            for roi in roi_list:
                roi.coords = self.canvas_coords(roi.coords)
                bbox_coords = self.canvas_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
                roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

        if self.use_masks:
            self.update_all_roi_masks()
        self.show_image(self.active)
        return


    def load_rois(self,loadpath=None):
        """
        Loads all ROIs from am roipickle file to the current active image only.
        If you want to load ROIs across multiple slices, loop the function
        yourself.

        Parameters
        ----------------
        loadpath: str, optional
            The absolute path at with which the ROI set is saved.  If no path is provided, a
            load file dialog box is opened to generate the path. (default = None)

        """



        if loadpath is None:
            from tkinter import filedialog
            loadpath = filedialog.askopenfilename(filetypes=(("MIPPY Object","*.obj"),("All files",'*')),title="Select ROI set to load",
                                                    parent = self.master)
        if loadpath is None:
            return
        with open(loadpath,'rb') as f:
            self.roi_list = pickle.load(f)

        # Transform coordinates to canvas coordinates after loading
        # This is a bit of a fudge to ensure coordinates are loaded
        # correctly when loading onto a different size canvas
        for roi in self.roi_list:
            roi.coords = self.canvas_coords(roi.coords)
            bbox_coords = self.canvas_coords([(roi.bbox[0],roi.bbox[1]),(roi.bbox[2],roi.bbox[3])])
            roi.bbox = (bbox_coords[0][0],bbox_coords[0][1],bbox_coords[1][0],bbox_coords[1][1])

        if self.use_masks:
            self.update_roi_masks()
        self.roi_list_2d[self.active-1] = self.roi_list
        self.quick_redraw_image()
        return

    def progress(self, percentage):
        """
        If there is a progress bar on the master canvas, this will update the progressbar
        to the percentage specified.  If the progressbar object cannot be found, this method
        will simply pass without throwing an error.

        Parameters
        ------------------
        percentage: float
            Percentage value (between 0 and 100) to which the progress bar should update

        """
        try:
            self.master.progressbar['value'] = percentage
            self.master.progressbar.update()
        except:
            pass
        return

    def draw_rectangle_roi(self):
        """Enables drawing on the MIPPYCanvas object and sets the active ROI mode to 'rectangle'"""
        self.drawing_enabled = True
        self.roi_mode = 'rectangle'

    def draw_ellipse_roi(self):
        """Enables drawing on the MIPPYCanvas object and sets the active ROI mode to 'ellipse'"""
        self.drawing_enabled = True
        self.roi_mode = 'ellipse'

    def draw_freehand_roi(self):
        """Enables drawing on the MIPPYCanvas object and sets the active ROI mode to 'freehand'"""
        self.drawing_enabled = True
        self.roi_mode = 'freehand'

    def draw_line_roi(self):
        """Enables drawing on the MIPPYCanvas object and sets the active ROI mode to 'line'"""
        self.drawing_enabled = True
        self.roi_mode = 'line'

    def canvas_coords(self, image_coords, zoom=None):
        """
        Converts image coordinates to canvas coordinates (determined by size of the canvas).

        Parameters
        ---------------------
        image_coords: list(tuple)
            List of (x,y) image coordinate tuples
        zoom: float, optional
            Zoom factor to use. If None is specified (as should be done generally) the current
            ``MIPPYCanvas.zoom_factor`` is used. (default = none)

        Returns
        ---------------
        new_coords: list(tuple)
            List of (x,y) coordinate tuples of transformed coordinates.

        """

        if zoom is None:
            zoom = self.zoom_factor
        new_coords = []
        for thing in image_coords:
            new_coords.append((thing[0] * zoom, thing[1] * zoom))
        return new_coords

    def image_coords(self, canvas_coords, zoom=None):
        """
        Converts canvas coordinates (determined by the size of the canvas relative to the image) to
        the coordinates within the image frame of reference.

        Parameters
        ---------------------
        canvas_coords: list(tuple)
            List of (x,y) canvas coordinate tuples
        zoom: float, optional
            Zoom factor to use. If None is specified (as should be done generally) the current
            ``MIPPYCanvas.zoom_factor`` is used. (default = none)

        Returns
        ---------------
        new_coords: list(tuple)
            List of (x,y) coordinate tuples of transformed coordinates.

        """
        if zoom is None:
            zoom = self.zoom_factor
        new_coords = []
        for thing in canvas_coords:
            new_coords.append((thing[0] / zoom, thing[1] / zoom))
        return new_coords


class EasyViewer(Frame):
    def __init__(self, master, im_array):
        Frame.__init__(self)
        self.master = master
        self.master.imcanvas = MIPPYCanvas(self.master, width=im_array.shape[1], height=im_array.shape[0],
                                           drawing_enabled=True)
        self.master.imobject = MIPPYImage(im_array)
        self.master.imcanvas.im1 = self.master.imobject.photoimage
        self.master.imcanvas.create_image((0, 0), image=self.master.imcanvas.im1, anchor='nw')
        self.master.imcanvas.pack()


########################################
########################################

class MIPPYImage():
    """
    The purpose of MIPPYImage is to have a single object which handles everything
    required to make images viewable on a Canvas.  It keeps and updates an Image.Image
    and ImageTk.PhotoImage object, the actual pixel values as px_float, and a few
    other useful functions to do with image rotation/flipping etc.

    .. note::
        This is currently very MRI-specific, and will not work with other DICOM objects.
        The intention is to generalise this further and remove some of the dependency
        on e.g. InPlanePhaseEncodingDirection, which will happen in a future version of
        MIPPY.

    Parameters
    ----------------------
    dicom_dataset: pydicom.Dataset.Dateset / pydicom.Dataset.FileDataset / numpy.ndarray / str
        The 'image' object to be loaded.  This can be a pydicom-loaded DICOM object, an array
        of pixel values, or a path to a DICOM file.
    limitbitdepth: bool, optional
        If True, it limits the bitdepth of px_float to 8-bit integers. Pixel values are
        scaled to fit this, so will no longer be representative of the 'true' pixel value.
        Recommended for use with e.g. reference images/landmarking images where pixel
        values are unimportant in order to reduce memory burden. (default = False)




    :ivar numpy.ndarray px_float: 2D pixel value array, indexed as [row,col] or [y,x]
    :ivar int flip_h: Number of times image has been flipped horizontally since loading. (initial value: 0)
    :ivar int flip_v: Number of times image has been flipped vertically since loading (initial value: 0)
    :ivar int rotations: Number of 90-degree rotations the image has been through relative to orientation when loaded. Positive values indicate a clockwise rotation. (initial value: 0)
    :ivar float rs: Rescale slope (initial value: from DICOM if present, 1 if not)
    :ivar float ri: Rescale intercept (initial value: from DICOM if present, 1 if not)
    :ivar float ss: Reciprocal scaling factor, specific to Philips images (initial value: from DICOM if present, None if not)
    :ivar int rows: Number of rows in image (inital value: from DICOM/pixel array)
    :ivar int columns: Number of columns in image (inital value: from DICOM/pixel array)
    :ivar float rangemax: Maximum possible value in MIPPYImage.px_float (taking account of bitdepth and rescaling)
    :ivar float rangemax: Minimum possible value in MIPPYImage.px_float (taking account of bitdepth and rescaling)
    :ivar tuple image_position: Position of pixel [0,0] in 3D space relative to patient/isocenter (initial value: from DICOM if available, None if not)
    :ivar tuple image_orientation: 6-tuple representing the unit vectors for X and Y axes of images (initial value: from DICOM if available, None if not)
    :ivar str pe_direction: Phase-encoding direction, specific to MRI. Allowed values are ``'ROW'`` or ``'COL'``. (initial value: from DICOM, if available, None if not)
    :ivar float pixel_bandwidth: The pixel bandwidth in Hz, MRI-specific (initial value: from DICOM if available, None if not)
    :ivar float xscale: The spacing of pixels in the X direction in mm (initial value: from DICOM if available, 1 if not)
    :ivar float yscale: The spacing of pixels in the Y direction in mm (initial value: from DICOM if available, 1 if not)
    :ivar numpy.ndarray overlay: Bitmap overlay for the image (inital value: from DICOM if available, None if not)
    :ivar PIL.Image.Image image: PIL/pillow ``Image`` object generated from the windowed pixel values (initial value: None)
    :ivar PIL.ImageTk.PhotoImage photoimage: The final representation of data that can be loaded onto the canvas (initial value: None)

    """

    def __init__(self, dicom_dataset, limitbitdepth=False,lut=None,pad_zero=False):

        # Need some tags to describe the state of the image
        # Use integers, increment as approrpriate and test with % function
        self.flip_h = 0
        self.flip_v = 0
        self.pad_zero=pad_zero
        # Describe 90 degrees clockwise as 1 rotation
        self.rotations = 0

        if not lut is None:
            self.lut=open_lut(lut)
        else:
            self.lut = None

        if type(dicom_dataset) is str or type(dicom_dataset) is str:
            ds = pydicom.dcmread(dicom_dataset)
        elif type(dicom_dataset) is pydicom.dataset.FileDataset:
            ds = dicom_dataset
        elif type(dicom_dataset) is np.ndarray:
            self.construct_from_array(dicom_dataset)
            return
        else:
            print("ERROR GENERATING IMAGE: Constructor input type not understood")
            return
        bitdepth = int(ds.BitsStored)
        # DO NOT KNOW IF PIXEL ARRAY ALREADY HANDLES RS AND RI
        pixels = ds.pixel_array.astype(np.float64)
        try:
            self.rs = float(ds[0x28, 0x1053].value)
        except:
            self.rs = 1.
        try:
            self.ri = float(ds[0x28, 0x1052].value)
        except:
            self.ri = 0.
        try:
            self.ss = float(ds[0x2005, 0x100E].value)
        except:
            self.ss = None

        # Attempt at bugfixing - Philips image scaling throwing off ADC values...
        # Comment this out if you need ss to be included in the pixel value calculation again
        # Added in version 2.9.2
        self.ss = None

        self.rows = ds.Rows
        self.columns = ds.Columns
        self.px_float = generate_px_float(pixels, self.rs, self.ri, self.ss,self.pad_zero)
        self.rangemax = np.max(generate_px_float(np.power(2, bitdepth), self.rs, self.ri, self.ss))
        self.rangemin = np.min(generate_px_float(0, self.rs, self.ri, self.ss))
        if limitbitdepth:
            # Added this to try and reduce memory burden on things like MRS reference images where
            # multiple 3D datasets might be loaded
            bitdepth_scale_factor = 1. / np.max(self.px_float) * 255.
            self.px_float = np.round(self.px_float * bitdepth_scale_factor).astype(np.uint8)
            self.rangemax = self.rangemax * bitdepth_scale_factor
            self.rangemin = self.rangemin * bitdepth_scale_factor
        try:
            self.image_position = np.array(ds.ImagePositionPatient)
            self.image_orientation = np.array(ds.ImageOrientationPatient).reshape((2, 3))
        except:
            self.image_position = None
            self.image_orientation = None

        # Change this tag with rotations
        try:
            pe_direction = ds.InPlanePhaseEncodingDirection
        except AttributeError:
            pe_direction = 'NONE'
        if 'ROW' in pe_direction.upper():
            self.pe_direction = 'ROW'
        elif 'COL' in pe_direction.upper():
            self.pe_direction = 'COL'
        else:
            self.pe_direction = 'UNKNOWN'
        try:
            self.pixel_bandwidth = ds.PixelBandwidth
            if 'ROW' in self.pe_direction:
                self.image_bandwidth = float(self.pixel_bandwidth) * float(self.columns) / 2
            elif 'COL' in self.pe_direction:
                self.image_bandwidth = float(self.pixel_bandwidth) * float(self.rows) / 2
        except AttributeError:
            # Here because images from Toshiba ExcelART 1.5T MR scanner do not write pixel_bandwidth into the header. Which is annoying.
            print("PIXEL BANDWIDTH NOT FOUND IN HEADER. REPLACED WITH A VALUE OF -1")
            self.pixel_bandwidth = -1
            self.image_bandwidth = -1
        try:
            self.xscale = ds.PixelSpacing[0]
            self.yscale = ds.PixelSpacing[1]
        except:
            self.xscale = 1
            self.yscale = 1
        try:
            self.overlay = Image.fromarray(get_overlay(ds), 'L')
        except:
            self.overlay = None
        self.image = None
        self.photoimage = None
        self.wl_and_display()

        return

    def construct_from_array(self, pixel_array):
        """
        Called within the constructor function __init__ if an array is passed instead
        of a DICOM object or path to DICOM object.
        """
#        if len(np.shape(pixel_array)) > 2:
#            # Assume RGB?
#            print(np.shape(pixel_array))
#            pixel_array = np.mean(pixel_array, axis=0)
#            print(np.shape(pixel_array))
        self.px_float = pixel_array.astype(np.float64)
        self.rangemax = np.amax(pixel_array)
        self.rangemin = np.amin(pixel_array)
        self.xscale = 1
        self.yscale = 1
        self.overlay = None
        self.image = None
        self.photoimage = None
        self.rows = np.shape(pixel_array)[0]
        self.columns = np.shape(pixel_array)[1]
        self.wl_and_display()
        return

    def swap_phase(self):
        """
        Swaps the phase encode direction when image is rotated. Never called
        explicitly, only ever done as part of a rotation method.
        """
        if not hasattr(self, 'pe_direction'):
            return
        else:
            if self.pe_direction == 'ROW':
                self.pe_direction == 'COL'
            elif self.pe_direction == 'COL':
                self.pe_direction == 'ROW'

    def swap_dimensions(self):
        """
        Swaps dimensions rows and columns when a rotation is performed.
        Only ever called from rotate method
        """
        # Standard pythonic way of swapping pointers
        self.rows, self.columns = self.columns, self.rows
        return

    def rotate_right(self):
        """
        Rotates the image clockwise by 90-degrees.  Only intended to be called
        using a ``mippy.viewing.ImageFlipper`` toolbar object.

        .. note::
            The MIPPYImage.image and MIPPYImage.photoimage are not regenerated
            as part of this method. It is expected that MIPPYCanvas will trigger
            this.

        """
        self.px_float = spim.rotate(self.px_float, 270., order=0, prefilter=False)
        self.rotations += 1
        self.swap_phase()
        self.swap_dimensions()
        return

    def rotate_left(self):
        """
        Rotates the image anti-clockwise by 90-degrees.  Only intended to be called
        using a ``mippy.viewing.ImageFlipper`` toolbar object.

        .. note::
            The MIPPYImage.image and MIPPYImage.photoimage are not regenerated
            as part of this method. It is expected that MIPPYCanvas will trigger
            this.

        """
        self.px_float = spim.rotate(self.px_float, 90., order=0, prefilter=False)
        self.rotations -= 1
        self.swap_phase()
        self.swap_dimensions()
        return

    def flip_horizontal(self):
        """
        Flips/reflects the image about a central vertical axis. Only intended to be called
        using a ``mippy.viewing.ImageFlipper`` toolbar object.

        .. note::
            The MIPPYImage.image and MIPPYImage.photoimage are not regenerated
            as part of this method. It is expected that MIPPYCanvas will trigger
            this.

        """
        self.px_float = np.fliplr(self.px_float)
        self.flip_h += 1
        return

    def flip_vertical(self):
        """
        Flips/reflects the image about a central horizontal axis. Only intended to be called
        using a ``mippy.viewing.ImageFlipper`` toolbar object.

        .. note::
            The MIPPYImage.image and MIPPYImage.photoimage are not regenerated
            as part of this method. It is expected that MIPPYCanvas will trigger
            this.

        """
        self.px_float = np.flipud(self.px_float)
        self.flip_v += 1
        return

    def get_pt_coords(self, image_coords):
        """
        Converts image coordinates (x,y) into a 3D-coordinate representing the location
        of that point in 3D space.

        .. deprecated:: 2.0
            These transformations should now always be handled using the
            ``get_voxel_location`` and ``get_img_coords`` methods in
            :ref:`mippy-mdicom-pixel`.

        """
        voxel_position = (self.image_position + image_coords[0] * self.xscale * self.image_orientation[0]
                          + image_coords[1] * self.yscale * self.image_orientation[1])
        return (voxel_position[0], voxel_position[1], voxel_position[2])

    def wl_and_display(self, window=None, level=None, zoom=None, antialias=True):
        """
        Generates the MIPPYImage.image and MIPPYImage.photoimage objects for
        the specified window and level.  If no window and level are specified,
        it defaults to the maximum/minimum of the dynamic range of the image.

        It is not usually necessary to invoke this function - it is primarily used
        by MIPPYCanvas and MIPPYImage to control the interaction with the mouse.

        To set your own window/level programmatically, use ``MIPPYCanvas.set_window_level``.

        Parameters
        -------------------------

        window: float, optional
            Width of the window applied to the pixel values for display
        level: float, optional
            Center of the window applied to the pixel values for display
        zoom: float, optional
            Zoom-factor to be used when generating the Image and PhotoImage objects, usually
            taken from the canvas.  If not provided, existing image size is used by default.
        antialias: bool, optional
            Specify whether antialiasing is to be used when generating the Image object. This
            is usually specified by the MIPPYCanvas object.


        """
        if antialias:
            resampling = Image.ANTIALIAS
        else:
            resampling = Image.NEAREST
        if window and level:
            self.window = window
            self.level = level
        else:
            self.window = self.rangemax - self.rangemin
            self.level = (self.rangemax - self.rangemin) / 2 + self.rangemin
        if zoom:
            size = (
            int(np.round(np.shape(self.px_float)[1] * zoom, 0)), int(np.round(np.shape(self.px_float)[0] * zoom, 0)))
        elif self.image:
            size = self.image.size
        else:
            size = (np.shape(self.px_float)[1], np.shape(self.px_float)[0])

        if self.level - self.rangemin < self.window / 2:
            self.window = 2 * (self.level - self.rangemin)
        windowed_px = np.clip(self.px_float, self.level - self.window / 2, self.level + self.window / 2 - 1).astype(
            np.float64)
        px_view = np.clip(((windowed_px - np.min(windowed_px)) / self.window * 255.), 0., 255.).astype(np.uint8)

        if not self.lut is None and not len(np.shape(px_view))>2:
            px_view_color = np.zeros((self.rows,self.columns,3))
            px_view_color[:,:,0] = np.take(self.lut[0],px_view)
            px_view_color[:,:,1] = np.take(self.lut[1],px_view)
            px_view_color[:,:,2] = np.take(self.lut[2],px_view)
            px_view = px_view_color.astype(np.uint8)


        #print('px_shape:', np.shape(px_view))

        if len(np.shape(px_view))>2:
                # More than 1 value per pixel to worry about (>2 axes), probably RGB
                self.image = Image.fromarray(px_view, mode='RGB')
        else:
            self.image = Image.fromarray(px_view, mode='L')

        self.apply_overlay()
        if not size == self.image.size:
            self.resize(size[0], size[1], resampling)

        self.set_display_image()

        return

    def resize(self, dim1=256, dim2=256, antialias=True):
        """
        Resizes the MIPPYImage.image and MIPPYImage.photoimage objects
        that are displayed on the canvas.

        .. note::
            No transformation of the actual pixel data is performed; this
            only updates the display image.

        Parameters
        -------------------
        dim1: int, optional
            Dimension 1 (usually X) in pixels for the resized display image (default = 256)
        dim2: int, optional
            Dimension 2 (usually Y) in pixels for the resized display image (default = 256)
        antialias: bool, optional
            Specify if antialiasing should be used when resizing the image (default = True)


        """
        if antialias:
            sampling = Image.ANTIALIAS
        else:
            sampling = Image.NEAREST
        self.image = self.image.resize((dim1, dim2), sampling)
        self.set_display_image()
        return

    def zoom(self, zoom, antialias=True):
        """
        Resizes the MIPPYImage.image and MIPPYImage.photoimage objects
        that are displayed on the canvas.

        .. note::
            No transformation of the actual pixel data is performed; this
            only updates the display image.

        Parameters
        -------------------
        zoom: float
            Zoom factor (relative to size of MIPPYImage.px_float) to be used
            when rescaling the image
        antialias: bool, optional
            Specify if antialiasing should be used when resizing the image (default = True)


        """
        if antialias:
            sampling = Image.ANTIALIAS
        else:
            sampling = Image.NEAREST
        self.image = self.image.resize((int(np.round(self.columns * zoom, 0)), int(np.round(self.rows * zoom, 0))),
                                       sampling)
        self.set_display_image()
        return

    def apply_overlay(self):
        """
        Applies the bitmap overlay to the display image MIPPYImage.image (if one exists).
        """
        if not self.overlay is None:
            self.image.paste(self.overlay, box=(0, 0), mask=self.overlay)
        return

    def set_display_image(self):
        """
        Generates the MIPPYImage.photoimage for display on the canvas. Only called from within
        MIPPYImage functions once window-level/zoom/overlay etc are all finished.
        """
        self.photoimage = ImageTk.PhotoImage(self.image)
        return

class MIPPYImage3DCoreg():
    """

    """
    def __init__(self, dicom_datasets, limitbitdepth=False,luts=None,pad_zero=False):
        # Do initial creation of instance using first series passed
        self.ref_images = []
        self.ref_geometry = []
        self.luts = []
        if luts is None:
            for i in range(len(dicom_datasets)):
                self.luts.append(None)
        else:
            self.luts = luts
        for i in range(len(dicom_datasets[0])):
            self.ref_images.append(MIPPYImage(dicom_datasets[0][i], limitbitdepth=limitbitdepth,lut=self.luts[0],pad_zero=pad_zero))
            self.ref_geometry.append([np.array(dicom_datasets[0][i].ImagePositionPatient),
                                        np.array(dicom_datasets[0][i].ImageOrientationPatient),
                                        float(dicom_datasets[0][i].PixelSpacing[0]),
                                        float(dicom_datasets[0][i].PixelSpacing[0])])

        # Grab 3D pixel array
        ref_px = []
        for image in self.ref_images:
            ref_px.append(image.px_float)
        self.ref_px = np.array(ref_px)

        # Generate 4D pixel array?

        # Generate 3D coordinate array
        self.ref_coords = np.zeros(np.shape(self.ref_px), dtype=(float,3))
        for z in range(np.shape(self.ref_coords)[0]):
            for y in range(np.shape(self.ref_coords)[1]):
                for x in range(np.shape(self.ref_coords)[2]):
                    self.ref_coords[z,y,x] = get_voxel_location((x,y),*self.ref_geometry[z])
        print(self.ref_coords)

        return



class Image3D():
    """
    Class for viewing and slicing 3D image datasets.
    Uses loaded DICOM datasets (via pydicom)
    """

    def __init__(self, datasets):
        """
        Datasets should be a list of pydicom DICOM objects.
        Images should be the same resolution with unique slice
        positions. Any set of slices can be displayed this way, but
        reslicing works better with 3D or thin-slice images. The
        nearer to isotropic resolution the better!
        """

        # Lazy check to make sure data is from the same series (assuming passed by MIPPY!)
        if not datasets[0].SeriesInstanceUID == datasets[-1].SeriesInstanceUID:
            # Not the same series!
            return None

        # Need to get:
        # - Matrix size
        # - Slice positions / thicknesses / spacing
        # - Slice orientation
        # - Pixel data!!!!
        # - Number of slices

        nSlices = len(datasets)
        orientations = []
        positions = []
        rows = []
        cols = []
        for ds in datasets:
            orientations.append(ds.ImageOrientationPatient)
            positions.append(ds.ImagePositionPatient)
            rows.append(ds.Rows)
            cols.append(ds.Columns)

        # Less lazy checks to make sure you actually have a single stack of data
        if len(np.unique(orientations)) > 1:
            print("Slice orientations not consistent")
            return
        if len(np.unique(positions)) < len(datasets):
            print("Some duplicated slice positions")
            return
        if len(np.unique(rows)) > 1 or len(np.unique(cols)) > 1:
            print("Inconsistent matrix sizes")
            return

        # Sort images based on slice position
        # TRA = 1,0,0,0,-1,0
        # SAG = 0,-1,0,0,0,-1
        # COR = 1,0,0,0,0,-1

        xdir = np.argmax(np.absolute(orientations[0][0:3]))
        ydir = np.argmax(np.absolute(orientations[0][3:6]))

        if not xdir == 0 and not ydir == 0:
            # X is missing direction, so sort based on X position
            sort_axis = 0
        elif not xdir == 1 and not ydir == 1:
            # Y is missing direction, so sort based on Y position
            sort_axis = 1
        elif not xdir == 2 and not ydir == 2:
            # Z is missing direction, so sort based on Z position
            sort_axis = 2
        else:
            print("Perfectly oblique slices. Too confused!")
            return None

        ds_sorted = sorted(datasets, key=lambda x: x.ImagePositionPatient[sort_axis], reverse=True)

        # Create empty pixel array
        px = np.zeros((nSlices, rows[0], cols[0])).astype(np.float64)

        # Populate pixel array with slice data
        for i in range(len(ds_sorted)):
            px[i] = ds_sorted[i].pixel_array().astype(np.float64)
        # Store px as an attribute of the object
        self.px = px

        # Get pixel spacing
        xspc = ds_sorted[0].PixelSpacing[0]
        yspc = ds_sorted[0].PixelSpacing[1]
        zspc = ds_sorted[0].SliceThickness + ds_sorted[0].SpacingBetweenSlices
        self.spacing = (xspc, yspc, zspc)

        # Get origin
        self.origin = ds_sorted[0].ImagePositionPatient
        ds0 = ds_sorted[0]
        xvector = ds0.ImageOrientationPatient[0:3]
        yvector = ds0.ImageOrientationPatient[3:6]

        return
