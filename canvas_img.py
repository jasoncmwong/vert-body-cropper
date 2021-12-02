import tkinter as tk
from PIL import Image, ImageTk
import math
import numpy as np

MIN_SIZE = 30


class CanvasImage:
    """
    This code is a modified version of the CanvasImage class found in 'gui_canvas.py' located at:
        https://github.com/foobar167/junkyard/tree/master/manual_image_annotation1/polygon
    """
    show_overlay = True  # Whether to display mask overlay
    contrast = 1.0  # Contrast for the viewers
    brightness = 0  # Brightness for the viewers

    def __init__(self, frame, img):
        self.imscale = 1.0  # Scale for the canvas image zoom
        self._zoom_factor = 1.1  # Zoom scaling factor
        self._filter = Image.NEAREST  # Filter used for zoom interpolation
        self.img_origin = np.array([0, 0], dtype=int)  # Origin of the image relative to the visible area
        self.imframe = tk.Frame(frame)  # Frame used as a placeholder
        self.lam_overlay = np.zeros(img.size, dtype=np.uint8).T  # Mask used to overlay with the image
        self.spc_overlay = np.zeros(img.size, dtype=np.uint8).T
        self.zero_layer = np.zeros(self.lam_overlay.shape, dtype=np.uint8)
        self.overlay_img = Image.fromarray(np.dstack((self.lam_overlay, self.zero_layer, self.zero_layer, self.lam_overlay)))  # Overlay image

        # Create canvas
        self.canvas = tk.Canvas(self.imframe, highlightthickness=0, bd=0, cursor='arrow')
        self.canvas.grid(row=0, column=0, sticky='nesw')
        self.canvas.update()  # Wait until the canvas is created

        # Bind events to the canvas
        self.canvas.bind('<Configure>', lambda e: self.show_image())  # Canvas resized
        self.canvas.bind('<ButtonPress-1>', self.v_lclick)
        self.canvas.bind('<B1-Motion>', self.v_ldrag)
        # self.canvas.bind('<ButtonPress-1>', self.v_lclick)
        # self.canvas.bind('<B1-Motion>', self.v_ldrag)

        self.prev_y = None  # Stored y coordinate used to determine how much to zoom
        self.old_x = None  # Stored x coordinate to determine centerpoint of zoom
        self.old_y = None  # Stored y coordinate to determine centerpoint of zoom

        self.orig_img = img  # Original copy of the image
        self.raw_img = np.asarray(img)  # Raw data
        self.img = img  # Modified copy of the image
        self.imwidth, self.imheight = self.img.size  # Image height and width
        self._min_side = min(self.imwidth, self.imheight)  # Smallest dimension of the image

        # Create image pyramid
        self._pyramid = [img]
        # Set ratio coefficient for image pyramid
        self._ratio = 1.0
        self._curr_img = 0  # Current image from the pyramid
        self._scale = self.imscale * self._ratio  # Image pyramid scale
        self._reduction = 2  # Reduction degree of image pyramid
        w, h = self._pyramid[-1].size
        while w > 512 and h > 512:  # Top pyramid image is larger than 512 pixels
            # Divide by reduction degree
            w /= self._reduction
            h /= self._reduction
            self._pyramid.append(self._pyramid[-1].resize((int(w), int(h)), self._filter))

        # Put image into container rectangle and use it to set proper coordinates of the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)

    def init_view(self):
        self.show_image()  # Show image on the canvas
        self.canvas.focus_set()  # Set focus on the canvas

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.imframe.grid(**kw)
        self.imframe.grid(sticky='nesw')
        self.imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    def bind(self, *args):
        self.canvas.bind(*args)

    def unbind(self, *args):
        self.canvas.unbind(*args)

    def show_image(self):
        """
        Show image on the canvas, taking into account the desired zoom and translation
        """
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly

        # Get coordinates (x1, y1, x2, y2) of the image tile
        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]

        # Show image if it is in the visible area
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            new_x1 = int(x1/self._scale)
            new_x2 = int(x2/self._scale)
            new_y1 = int(y1/self._scale)
            new_y2 = int(y2/self._scale)
            image = self._pyramid[max(0, self._curr_img)].crop(  # Crop current img from pyramid
                (new_x1, new_y1,
                 new_x2, new_y2))

            # Get coordinates of the image origin
            if x1 > 0:
                origin_x = -new_x1
            else:
                origin_x = box_image[0] - box_canvas[0]

            if y1 > 0:
                origin_y = -new_y1
            else:
                origin_y = box_image[1] - box_canvas[1]
            self.img_origin = np.array([origin_x, origin_y], dtype=int)

            # Update image
            resized_img = image.resize((int(x2-x1), int(y2-y1)), self._filter)
            contrast_img = resized_img.point(lambda l: l*CanvasImage.contrast+CanvasImage.brightness)

            if CanvasImage.show_overlay:  # Overlay to be shown
                self.overlay_img = Image.fromarray(np.maximum(np.dstack((self.lam_overlay, self.zero_layer, self.zero_layer, self.lam_overlay)),
                                                              np.dstack((self.zero_layer, self.spc_overlay, self.spc_overlay, self.spc_overlay))))
                proc_overlay = self.overlay_img.crop((new_x1, new_y1,
                                                      new_x2, new_y2))
                proc_overlay = proc_overlay.resize((int(x2-x1), int(y2-y1)), self._filter)

                imagetk = ImageTk.PhotoImage(Image.alpha_composite(contrast_img.convert('RGBA'), proc_overlay))
            else:
                imagetk = ImageTk.PhotoImage(contrast_img)
            self.canvas.imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                                           max(box_canvas[1], box_img_int[1]),
                                                           anchor='nw', image=imagetk)
            self.canvas.lower(self.canvas.imageid)  # Set image into background
            self.canvas.imagetk = imagetk

    def outside(self, x, y):
        """
        Checks if the point (x, y) is outside of the image area
        """
        bbox = self.canvas.coords(self.container)  # Get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # Point (x,y) is inside the image area
        else:
            return True  # Point (x,y) is outside the image area

    def v_lclick(self, e):
        """
        Move event handler for a mouse scroll click on the canvas in view mode.
        Updates 'old_x' and 'old_y' with mouse click coordinates.
        Args:
            e (Event): Mouse event state
        """
        self.old_x, self.old_y = e.x, e.y
        self.canvas.scan_mark(e.x, e.y)

    def v_ldrag(self, e):
        """
        Move event handler for a mouse scroll click drag motion on the canvas in view mode.
        Args:
            e (Event): Mouse event state
        """
        self.canvas.scan_dragto(e.x, e.y, gain=1)
        self.show_image()

    # def v_lclick(self, e):
    #     """
    #     Zoom event handler for a mouse left click on the canvas in view mode.
    #     Updates 'old_x', 'old_y', and 'prev_y' with mouse click coordinates.
    #     Args:
    #         e (Event): Mouse event state
    #     """
    #     self.old_x, self.old_y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
    #     self.prev_y = self.canvas.canvasy(e.y)
    #
    # def v_ldrag(self, e):
    #     """
    #     Zoom event handler for a mouse left click drag motion on the canvas in view mode.
    #     Args:
    #         e (Event): Mouse event state
    #     """
    #     if self.outside(self.old_x, self.old_y):  # Mouse outside of the image
    #         return
    #     scale = 1.0
    #
    #     if self.prev_y - self.canvas.canvasy(e.y) < 0:  # Mouse moved down - zoom in
    #         i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
    #         if i < self.imscale:  # One pixel is bigger than the visible area
    #             self.prev_y = self.canvas.canvasy(e.y)
    #             return
    #         self.imscale *= self._zoom_factor
    #         scale *= self._zoom_factor
    #     elif self.prev_y - self.canvas.canvasy(e.y) > 0:  # Moused moved up - zoom out
    #         if round(self._min_side*self.imscale) < MIN_SIZE:  # Image is less than minimum pixels
    #             self.prev_y = self.canvas.canvasy(e.y)
    #             return
    #         self.imscale /= self._zoom_factor
    #         scale /= self._zoom_factor
    #     else:  # Mouse is in the same position vertically
    #         return
    #
    #     # Take appropriate image from the pyramid
    #     k = self.imscale * self._ratio  # temporary coefficient
    #     self._curr_img = min((-1) * int(math.log(k, self._reduction)), len(self._pyramid) - 1)
    #     self._scale = k * math.pow(self._reduction, max(0, self._curr_img))
    #
    #     self.canvas.scale('all', self.old_x, self.old_y, scale, scale)  # rescale all objects
    #
    #     self.show_image()
    #     self.prev_y = self.canvas.canvasy(e.y)

    def destroy(self):
        """ ImageFrame destructor """
        self.img.close()
        map(lambda i: i.close, self._pyramid)  # close all pyramid images
        del self._pyramid[:]  # delete pyramid list
        del self._pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.imframe.destroy()

    def get_coords(self):
        """
        Convenient accessor method to get canvas origin coordinates
        Returns:
            canvas_x (float): X coordinate of canvas origin
            canvas_y (float): Y coordinate of canvas origin
        """
        return self.canvas.coords(self.canvas.imageid)

    def update_img(self, new_img):
        """
        Updates current canvas with a new image
        Args:
            new_img (PIL Image): New image
        """
        self.orig_img = new_img
        self.raw_img = np.asarray(new_img)
        self.img = new_img
        self._pyramid = [new_img]
        self.show_image()

    def switch_mode(self, mode):
        """
        Switches modes by re-binding and un-binding shortcuts on the canvases
        Updates 'cor_view' and 'ax_view' key bindings.
        Args:
            mode (char): Mode key shortcut
        """
        if mode == 'v':  # View mode
            self.canvas.unbind('<Motion>')

            # self.canvas.bind('<ButtonPress-1>', self.v_lclick)  # Zooming
            # self.canvas.bind('<B1-Motion>', self.v_ldrag)
            self.canvas.bind('<ButtonPress-1>', self.v_lclick)  # Moving
            self.canvas.bind('<B1-Motion>', self.v_ldrag)

            self.canvas.configure(cursor='arrow')
        elif mode == 'c':  # Crop mode
            self.canvas.unbind('<B1-Motion>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.unbind('<B2-Motion>')
            self.canvas.unbind('<MouseWheel>')

            self.canvas.configure(cursor='pencil')
        else:
            raise ValueError('Invalid mode')
