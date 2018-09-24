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

########################################
########################################
"""
GENERIC FUNCTIONS NOT ATTACHED TO CLASSES
"""


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
    Requires a numpy array and an existing Tk instance to use as a
    master window.  im_array can be 2D or 3D.
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
    Expects DICOM dataset
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


def generate_px_float(pixels, rs, ri, ss=None):
    if ss:
        return (pixels * rs + ri) / (rs * ss)
    else:
        return (pixels * rs + ri)


def get_global_min_and_max(image_list):
    """
    Will only work with MIPPY_8bitviewer type objects
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

    a = semiaxis in x direction
    b = semiaxis in y direction
    DO NOT CONFUSE THE TWO!
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
    def __init__(self, coords, tags=[], roi_type=None, color='yellow'):
        """
        Expecting a string of 2- or 3-tuples to define bounding coordinates.
        Type of ROI will be inferred from number of points.
        """
        self.coords = coords
        self.color = color
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
        if not 'roi' in tags:
            tags.append('roi')
        self.tags = tags

    def contains(self, point):
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

    def update(self, xmove=0, ymove=0):
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
    def __init__(self, master, canvas):
        Frame.__init__(self, master)
        self.canvas = canvas
        self.rot_left_button = Button(self, text="Rot L", command=lambda: self.rot_left(canvas))
        self.rot_right_button = Button(self, text="Rot R", command=lambda: self.rot_right(canvas))
        self.flip_h_button = Button(self, text="Flip H", command=lambda: self.flip_h(canvas))
        self.flip_v_button = Button(self, text="Flip V", command=lambda: self.flip_v(canvas))
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

    def rot_left(self, canvas):
        for im in canvas.images:
            im.rotate_left()
            im.wl_and_display()
        canvas.show_image()
        return

    def rot_right(self, canvas):
        for im in canvas.images:
            im.rotate_right()
            im.wl_and_display()
        canvas.show_image()
        return

    def flip_h(self, canvas):
        for im in canvas.images:
            im.flip_horizontal()
            im.wl_and_display()
        canvas.show_image()
        return

    def flip_v(self, canvas):
        for im in canvas.images:
            im.flip_vertical()
            im.wl_and_display()
        canvas.show_image()
        return


class MIPPYCanvas(Canvas):
    def __init__(self, master, width=256, height=256, bd=0, drawing_enabled=False, autostats=False, antialias=True,
                 use_masks=True):
        Canvas.__init__(self, master, width=width, height=height, bd=bd, bg='#444444')
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

    def reconfigure(self, event):
        if not self.images == []:
            # Already images loaded. Recalculate zoom factor and redraw
            self.width = event.width - 4
            self.height = event.height - 4
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
        if self.img_scrollbar:
            self.img_scrollbar.config(command=self.scroll_images)
            self.img_scrollbar.set(0, 1)
        if self.active and not self.images == []:
            if not len(self.images) == 1:
                self.img_scrollbar.set(self.active - 1 / (len(self.images) - 1), self.active / (len(self.images) - 1))
            else:
                self.img_scrollbar.set(0, 1)

    def scroll_images(self, command, value, mode='unit'):
        if command == 'scroll':
            self.show_image(self.active + int(value))
        elif command == 'moveto':
            selected_img = int(np.round((float(value) * float((len(self.images)))), 0)) + 1
            if not selected_img == self.active:
                self.show_image(selected_img)

    def update_scrollbar(self, value):
        current_img = float(self.active)
        total_img = float(len(self.images))
        lo = (self.active - 1) / total_img
        hi = self.active / total_img
        self.img_scrollbar.set(lo, hi)

    def reset(self):
        self.images = []
        self.delete('all')
        self.active = None

    def show_image(self, num=None):
        """
        Takes slice number (which starts from 1, not zero).  Doesn't do anything
        if there are no images loaded.
        """
        if len(self.images) == 0:
            return
        if num and not num < 1 and not num > len(self.images):
            self.active = num
            self.active_str.set(str(num) + "/" + str(len(self.images)))
            self.update_scrollbar((num - 1.) / len(self.images))
        self.delete('image')
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
        try:
            self.delete('image')
            self.create_image((0, 0), image=self.images[self.active - 1].photoimage, anchor='nw', tags='image')
            self.tag_lower('image')
        except:
            pass

    def update_roi_masks(self):
        """
        Returns a binary mask of all ROIs
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
        Same idea as update_roi_masks, but cycles through all images
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
        Returns a LIST of pixel values from an ROI.
        ROIS must be a list of ROI numbers.
        """
        im = self.get_active_image()
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
                print("Pixels in mask = {}".format(np.sum(maskflat)))
                pxlist = [pxflat[ind] for ind, val in enumerate(maskflat) if val > 0]
                px.append(pxlist)

            return px

    def get_roi_statistics(self, rois=[], tags=[]):
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
        """Returns a line profile from the image"""

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
        if system == 'image':
            coords = self.canvas_coords(coords)
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        if not 'roi' in tags:
            tags.append('roi')
        self.draw_roi(coords, tags=tags, color=color)
        self.add_roi(coords, tags, color=color)
        return

    def draw_roi(self, coords, tags, color='yellow'):
        if not 'roi' in tags:
            tags.append('roi')

        if not 'polygon' in tags:
            for i in range(len(coords)):
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
                                         tags=tags, dash=(4, 2))
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

    def redraw_rois(self, color='yellow'):
        # color option is redundant, I think...
        self.delete('roi')
        for roi in self.roi_list:
            self.draw_roi(roi.coords, roi.tags, color=roi.color)
        return

    def roi_rectangle(self, x_start, y_start, width, height, tags=[], system='canvas', color='yellow'):
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
        coords = get_ellipse_coords(center, radius_x, radius_y, resolution)
        if system == 'image':
            for i in range(len(coords)):
                coords[i] = tuple(x * self.zoom_factor for x in coords[i])
        elif not system == 'canvas':
            print("Invalid coordinate system specified")
            return
        self.new_roi(coords, tags=tags, color=color)
        return

    def load_images(self, image_list, keep_rois=False, limitbitdepth=False):
        self.images = []
        self.delete('all')
        if not keep_rois or not len(self.roi_list_2d) == len(image_list):
            # Will replace ROIs no matter what if you load a
            # different number of images
            self.roi_list_2d = []
            self.masks_2d = []

        self.roi_list = []
        self.masks = []
        n = 0

        if len(image_list) > 500:
            print("More than 500 images - cannot be loaded to canvas.")
            print("Loading first 500 only...")
            image_list = image_list[0:100]

        for ref in image_list:
            self.progress(45. * n / len(image_list) + 10)
            self.images.append(MIPPYImage(ref,
                                          limitbitdepth=limitbitdepth))  # Included limitbitdepth to allow restriction to 8 bit int
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
        return self.images[self.active - 1]

    def get_3d_array(self):
        """
        Only works if all images are same dimensions
        """
        px_array = []
        for image in self.images:
            px_array.append(image.px_float)
        px_array = np.array(px_array)
        return px_array

    def reset_window_level(self):
        self.temp_window = self.default_window
        self.temp_level = self.default_level
        self.window = self.default_window
        self.level = self.default_level

        for image in self.images:
            image.wl_and_display(window=self.default_window, level=self.default_level)
        self.show_image(self.active)
        return

    def left_click(self, event):
        if not self.drawing_enabled:
            return
        self.xmouse = event.x
        self.ymouse = event.y
        self.tempx = event.x
        self.tempy = event.y
        moving = False
        for roi in self.roi_list:
            if roi.contains((self.xmouse, self.ymouse)):
                moving = True
                break
        if not moving:
            self.drawing_roi = True
            # Need to add stuff to detect if "shift" or "ctrl" held when drawing, as
            # in this case, don't want to delete existing ROIs
            self.delete_rois()
            self.temp = []
            self.tempcoords.append((self.xmouse, self.ymouse))

    def left_drag(self, event):
        if not self.drawing_enabled:
            return
        xmove = event.x - self.tempx
        ymove = event.y - self.tempy
        if self.drawing_roi:
            if self.roi_mode == 'rectangle' or self.roi_mode == 'ellipse':
                self.delete('roi')
            if self.roi_mode == 'rectangle':
                self.create_rectangle((self.xmouse, self.ymouse, event.x, event.y), fill='', outline='yellow',
                                      tags='roi')
            elif self.roi_mode == 'ellipse':
                self.create_oval((self.xmouse, self.ymouse, event.x, event.y), fill='', outline='yellow', tags='roi')
            elif self.roi_mode == 'freehand':
                self.create_line((self.tempx, self.tempy, event.x, event.y), fill='yellow', width=1, tags='roi')
                self.tempcoords.append((event.x, event.y))
            elif self.roi_mode == 'line':
                self.delete('roi')
                self.create_line((self.xmouse, self.ymouse, event.x, event.y), fill='yellow', width=1, tags='roi')

        else:
            self.move('roi', xmove, ymove)

        self.tempx = event.x
        self.tempy = event.y

    def left_release(self, event):
        if not self.drawing_enabled:
            return
        if self.drawing_roi:
            self.roi_list = []
            if self.roi_mode == 'rectangle':
                self.add_roi(
                    [(self.xmouse, self.ymouse), (event.x, self.ymouse), (event.x, event.y), (self.xmouse, event.y)])
            elif self.roi_mode == 'ellipse':
                positive_coords = []
                negative_coords = []
                # http://mathworld.wolfram.com/Ellipse-LineIntersection.html
                # get points in circle by incrementally adding rays from centre
                # and getting intersections with ellipse
                bbox = self.bbox('roi')
                a = (bbox[2] - bbox[0]) / 2
                b = (bbox[3] - bbox[1]) / 2
                c = (bbox[0] + a, bbox[1] + b)
                self.add_roi(get_ellipse_coords(c, a, b, n=2 * max([a, b])))
                coords = self.roi_list[0].coords
            elif self.roi_mode == 'line':
                self.add_roi([(self.xmouse, self.ymouse), (event.x, event.y)])
            else:
                # Freehand
                self.create_line((self.tempx, self.tempy, self.xmouse, self.ymouse), fill='yellow', width=1, tags='roi')
                if len(self.tempcoords) > 1:
                    self.add_roi(self.tempcoords)
                else:
                    self.delete('roi')
            self.drawing_roi = False
        else:
            total_xmove = event.x - self.xmouse
            total_ymove = event.y - self.ymouse
            if len(self.roi_list) > 0:
                for roi in self.roi_list:
                    roi.update(total_xmove, total_ymove)
                    if self.use_masks:
                        self.update_roi_masks()
        if self.autostats == True:
            print(self.get_roi_statistics())
        self.tempcoords = []
        self.tempx = None
        self.tempy = None

    def left_double(self, event):
        pass

    def right_click(self, event):
        if self.images == []:
            # If no active display slices, just skip this whole function
            return
        self.xmouse = event.x
        self.ymouse = event.y

    def right_drag(self, event):
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
        if abs(self.xmouse - event.x) < 1 and abs(self.ymouse - event.y) < 1:
            return
        self.set_window_level(self.temp_window, self.temp_level)

    def set_window_level(self, window, level, antialias=True):
        self.window = window
        self.level = level
        for image in self.images:
            image.wl_and_display(window=self.window, level=self.level, antialias=self.antialias)
        self.show_image()

    def right_double(self, event):
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
        self.roi_list.append(ROI(coords, tags, roi_type, color=color))
        bbox = self.roi_list[-1].bbox
        # DEBUGGING: This line was to draw location of bounding box
        # self.create_rectangle((bbox[0],bbox[1],bbox[2],bbox[3]),outline='cyan',tags='roi')
        self.roi_list_2d[self.active - 1] = self.roi_list
        if self.use_masks:
            self.update_roi_masks()

    def delete_rois(self):
        self.roi_list = []
        self.masks = []
        gc.collect()
        self.delete('roi')
       
    def save_rois(self,savepath=None):
        """
        Saves all ROIs from the current active image only.
        If you want to save all ROIs across all slices, loop the function
        yourself.
        """
        if savepath is None:
            from tkinter import filedialog
            savepath = tkFileDialog.asksaveasfilename(filetypes=(("MIPPY ROI set","*.roiset")),
                                                        defaultextension=".roiset",parent=self.master)
        if savepath is None:
            return
        if not os.path.exists(os.path.split(savepath)[0]):
            os.makedirs(os.path.split(savepath)[0])
        with open(savepath,'wb') as f:
            pickle.dump(self.roi_list,f)
        return
       
    def load_rois(self,loadpath=None):
        """
        Loads ROIs from a .roiset file
        """
        if loadpath is None:
            from tkinter import filedialog
            loadpath = tkFileDialog.askopenfilename(filetypes=(("MIPPY ROI set","*.roiset")),title="Select ROI set",
                                                    parent = self.master)
        if loadpath is None:
            return
        with open(loadpath,'rb') as f:
            self.roi_list = pickle.load(f)
        if self.use_masks:
            self.update_roi_masks()
        self.roi_list_2d[self.active-1] = self.roi_list
        self.quick_redraw_image()
        return

    def progress(self, percentage):
        try:
            self.master.progressbar['value'] = percentage
            self.master.progressbar.update()
        except:
            pass

    def draw_rectangle_roi(self):
        self.drawing_enabled = True
        self.roi_mode = 'rectangle'

    def draw_ellipse_roi(self):
        self.drawing_enabled = True
        self.roi_mode = 'ellipse'

    def draw_freehand_roi(self):
        self.drawing_enabled = True
        self.roi_mode = 'freehand'

    def draw_line_roi(self):
        self.drawing_enabled = True
        self.roi_mode = 'line'

    def canvas_coords(self, image_coords, zoom=None):
        if zoom is None:
            zoom = self.zoom_factor
        new_coords = []
        for thing in image_coords:
            new_coords.append((thing[0] * zoom, thing[1] * zoom))
        return new_coords

    def image_coords(self, canvas_coords, zoom=None):
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
    This class wraps up Image.Image and ImageTk.PhotoImage classes so that they can be
    easily rescaled with whatever window and level for display purposes.  It's only 8-bit so
    you don't have the biggest dynamic range, but I'm sure I've heard that the eye can't
    resolve more than 256 shades of grey anyway...

    The actual floating point values are stored as an attribute "px_float", so that the actual
    scaled values can also be called for any given x,y position.  This should help when
    constructing an actual viewer.

    I should type "actual" some more...
    """

    def __init__(self, dicom_dataset, create_pillow=True, limitbitdepth=False):

        # Need some tags to describe the state of the image
        # Use integers, increment as approrpriate and test with % function
        self.flip_h = 0
        self.flip_v = 0
        # Describe 90 degrees clockwise as 1 rotation
        self.rotations = 0

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
        self.rows = ds.Rows
        self.columns = ds.Columns
        self.px_float = generate_px_float(pixels, self.rs, self.ri, self.ss)
        self.rangemax = generate_px_float(np.power(2, bitdepth), self.rs, self.ri, self.ss)
        self.rangemin = generate_px_float(0, self.rs, self.ri, self.ss)
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
        if len(np.shape(pixel_array)) > 2:
            # Assume RGB?
            print(np.shape(pixel_array))
            pixel_array = np.mean(pixel_array, axis=0)
            print(np.shape(pixel_array))
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
        if not hasattr(self, 'pe_direction'):
            return
        else:
            if self.pe_direction == 'ROW':
                self.pe_direction == 'COL'
            elif self.pe_direction == 'COL':
                self.pe_direction == 'ROW'

    def swap_dimensions(self):
        # Standard pythonic way of swapping pointers
        self.rows, self.columns = self.columns, self.rows
        return

    def rotate_right(self):
        self.px_float = spim.rotate(self.px_float, 270., order=0, prefilter=False)
        self.rotations += 1
        self.swap_phase()
        self.swap_dimensions()
        return

    def rotate_left(self):
        self.px_float = spim.rotate(self.px_float, 90., order=0, prefilter=False)
        self.rotations -= 1
        self.swap_phase()
        self.swap_dimensions()
        return

    def flip_horizontal(self):
        self.px_float = np.fliplr(self.px_float)
        self.flip_h += 1
        return

    def flip_vertical(self):
        self.px_float = np.flipud(self.px_float)
        self.flip_v += 1
        return

    def get_pt_coords(self, image_coords):
        """
        Assumes you've passed a tuple (x,y) as your image coordinates
        """
        voxel_position = (self.image_position + image_coords[0] * self.xscale * self.image_orientation[0]
                          + image_coords[1] * self.yscale * self.image_orientation[1])
        return (voxel_position[0], voxel_position[1], voxel_position[2])

    def wl_and_display(self, window=None, level=None, zoom=None, antialias=True):
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

        self.image = Image.fromarray(px_view, mode='L')

        self.apply_overlay()
        if not size == self.image.size:
            self.resize(size[0], size[1], resampling)

        self.set_display_image()

        return

    def resize(self, dim1=256, dim2=256, antialias=True):
        if antialias:
            sampling = Image.ANTIALIAS
        else:
            sampling = Image.NEAREST
        self.image = self.image.resize((dim1, dim2), sampling)
        self.set_display_image()
        return

    def zoom(self, zoom, antialias=True):
        if antialias:
            sampling = Image.ANTIALIAS
        else:
            sampling = Image.NEAREST
        self.image = self.image.resize((int(np.round(self.columns * zoom, 0)), int(np.round(self.rows * zoom, 0))),
                                       sampling)
        self.set_display_image()
        return

    def apply_overlay(self):
        if not self.overlay is None:
            self.image.paste(self.overlay, box=(0, 0), mask=self.overlay)
        return

    def set_display_image(self):
        self.photoimage = ImageTk.PhotoImage(self.image)
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
