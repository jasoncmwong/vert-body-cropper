import tkinter as tk
import tkinter.filedialog as tkfd
import imageio
from info_view import *
from canvas_img import *
from PIL import Image
import matplotlib.pyplot as plt

START_CROP_DIM = 384
MIN_CROP_DIM = 100


class App(tk.Frame):
    def __init__(self):
        super().__init__()
        self.img = None                 # Loaded image to crop smaller images from
        self.img_name = None            # Name of file

        self.img_frame = None           # Frame that holds loaded image
        self.info_frame = None          # Frame that holds info about the image and cropping
        self.crop_frame = None          # Frame that holds cropped image
        self.img_view = None            # CanvasImage that displays loaded image
        self.crop_view = None           # CanvasImage that displays cropped image

        self.c_box = None               # Square used to determine cropping
        self.c_dim = START_CROP_DIM     # Dimension of square cropping box
        self.c_img = None               # Cropped out image
        self.prev_box = None            # Previous cropped box

        self.save_button = None         # Save button to save cropped image

        self._init_ui()

    def _init_ui(self):
        """
        Initializes layout of the GUI with frames and widgets
        """
        ### MAIN WINDOW ###
        self.master.title('Vertebral Body Cropper')
        self.master.state('zoomed')
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=3)
        self.master.grid_columnconfigure(0, weight=7)
        self.master.grid_columnconfigure(1, weight=3)

        ### IMAGE WINDOW ###
        self.img_frame = tk.Frame(self.master, bg='green')
        self.img_frame.grid(row=0, column=0, rowspan=2, sticky='nesw')
        self.img_frame.grid_rowconfigure(0, weight=10)
        self.img_frame.grid_rowconfigure(1, weight=975)
        self.img_frame.grid_rowconfigure(2, weight=10)
        self.img_frame.grid_rowconfigure(3, weight=5)
        self.img_frame.grid_columnconfigure(0, weight=2)
        self.img_frame.grid_columnconfigure(1, weight=10)
        self.img_frame.grid_columnconfigure(2, weight=83)
        self.img_frame.grid_columnconfigure(3, weight=10)
        self.img_frame.grid_columnconfigure(4, weight=83)
        self.img_frame.grid_columnconfigure(5, weight=10)
        self.img_frame.grid_columnconfigure(6, weight=2)
        self.img_frame.grid_propagate(False)

        ### INFO WINDOW ###
        self.info_frame = tk.Frame(self.master, bg='black')
        self.info_frame.grid(row=0, column=1, sticky='nesw')
        self.info_frame.grid_rowconfigure(0, weight=10)
        self.info_frame.grid_rowconfigure(1, weight=975)
        self.info_frame.grid_rowconfigure(2, weight=10)
        self.info_frame.grid_rowconfigure(3, weight=5)
        self.info_frame.grid_columnconfigure(0, weight=2)
        self.info_frame.grid_columnconfigure(1, weight=10)
        self.info_frame.grid_columnconfigure(2, weight=83)
        self.info_frame.grid_columnconfigure(3, weight=10)
        self.info_frame.grid_columnconfigure(4, weight=83)
        self.info_frame.grid_columnconfigure(5, weight=10)
        self.info_frame.grid_columnconfigure(6, weight=2)
        self.info_frame.grid_propagate(False)

        self.info_viewer = InfoView(self.info_frame)
        self.info_viewer.grid(row=0, column=1, sticky='nesw')
        self.info_viewer.add_label('Image name', 'img_name')
        self.info_viewer.add_label('Dimensions', 'dim')
        self.info_viewer.add_label('Crop dimensions', 'c_dim')

        ### CROPPED WINDOW ###
        self.crop_frame = tk.Frame(self.master, bg='blue')
        self.crop_frame.grid(row=1, column=1, sticky='nesw')
        self.crop_frame.grid_rowconfigure(0, weight=9)
        self.crop_frame.grid_rowconfigure(1, weight=1)
        self.crop_frame.grid_columnconfigure(0, weight=2)
        self.crop_frame.grid_columnconfigure(1, weight=10)
        self.crop_frame.grid_columnconfigure(2, weight=83)
        self.crop_frame.grid_columnconfigure(3, weight=10)
        self.crop_frame.grid_columnconfigure(4, weight=83)
        self.crop_frame.grid_columnconfigure(5, weight=10)
        self.crop_frame.grid_columnconfigure(6, weight=2)
        self.crop_frame.grid_propagate(False)
        self.save_button = tk.Button(self.crop_frame, text='Save image', command=self.save_cropped)
        self.save_button.grid(row=2, column=3, sticky='nesw')

        ### MENU BAR ###
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label='Open image', command=self.file_menu_open, accelerator='Ctrl+O')
        self.master.bind('<Control-o>', lambda e: self.file_menu_open())
        file_menu.add_command(label='Save cropped', command=self.save_cropped, accelerator='Ctrl+S')
        self.master.bind('<Control-s>', lambda e: self.save_cropped())
        menu_bar.add_cascade(label='File', menu=file_menu)

        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=False)
        tools_menu.add_command(label='View', command=lambda: self.switch_mode('v'), accelerator='V')
        self.master.bind('v', lambda e: self.switch_mode(e.keysym))
        tools_menu.add_command(label='Crop', command=lambda: self.switch_mode('c'), accelerator='C')
        self.master.bind('c', lambda e: self.switch_mode(e.keysym))
        menu_bar.add_cascade(label='Tools', menu=tools_menu)

    def _init_view(self):
        """
        Initializes widgets with the loaded x-ray image and pertinent info
        """
        ### IMAGE VIEW ###
        disp_img = Image.fromarray(self.img)
        self.img_view = CanvasImage(self.img_frame, disp_img)
        self.img_view.init_view()
        self.img_view.grid(row=1, column=1, columnspan=5, sticky='nesw')

        ### INFO VIEW ###
        self.info_viewer.update_text('dim', '{0} x {1}'.format(self.img.shape[1], self.img.shape[0]))
        self.info_viewer.update_text('c_dim', '{0} x {1}'.format(self.c_dim, self.c_dim))

        ### CROPPED VIEW ###
        self.c_img = np.full((self.c_dim, self.c_dim), 255, dtype=np.uint8)
        disp_img = Image.fromarray(self.c_img)
        self.crop_view = CanvasImage(self.crop_frame, disp_img)
        self.crop_view.init_view()
        self.crop_view.grid(row=0, column=1, columnspan=5, sticky='nesw')

    def file_menu_open(self):
        """
        Opens a file open dialog to import an image.
        Assigns to 'img' and 'img_name' if successful open.
        """
        dlg = tkfd.Open(self, filetypes=[('Image', '.jpeg .jpg .png')])
        file_name = dlg.show()

        if file_name != '':
            self.img = imageio.imread(file_name)[:, :, 0]
            self.img_name = file_name[file_name.rfind('/')+1:]
            print('Opened ' + file_name)

            # Initialize view
            self.info_viewer.update_text('img_name', self.img_name)
            self._init_view()
        else:
            print('Open failed')

    def save_cropped(self):
        """
        Saves the cropped image in a .jpg file.
        :return:
        """
        img_num = self.img_name[self.img_name.find('US')+2:-4]
        file_name = tkfd.asksaveasfilename(defaultextension='.jpg',
                                           filetypes=[('JPG', '*.jpg')],
                                           initialfile='{0}-'.format(img_num))
        if file_name == '':
            print('Save path not specified - file not saved')
            return
        imageio.imwrite(file_name, self.c_img)

    ### CALLBACKS ###
    def c_move(self, e):
        """
        Event handler for a mouse motion on the image viewer in crop mode.
        Updates 'c_box' overlay.
        Args:
            e (Event): Mouse event state
        """
        x, y = self.img_view.canvas.canvasx(e.x), self.img_view.canvas.canvasy(e.y)
        self.img_view.canvas.delete(self.c_box)
        self.c_box = self.img_view.canvas.create_rectangle(x-self.c_dim//2, y-self.c_dim//2,
                                                           x+self.c_dim//2, y+self.c_dim//2,
                                                           outline='lime', width=3)

    def c_scroll(self, e):
        """
        Event handler for a scroll wheel action on the image viewer in crop mode.
        Updates 'c_box' size (up for bigger, down for smaller).
        Args:
            e (Event): Mouse event state
        """
        self.img_view.canvas.delete(self.c_box)
        x, y = self.img_view.canvas.canvasx(e.x), self.img_view.canvas.canvasy(e.y)
        if e.delta < 0:  # Scroll down - reduce crop box size
            self.c_dim = max(self.c_dim-2, MIN_CROP_DIM)
        else:  # Scroll up - increase crop box size
            self.c_dim += 2
        self.c_box = self.img_view.canvas.create_rectangle(x - self.c_dim//2, y - self.c_dim//2,
                                                           x + self.c_dim//2, y + self.c_dim//2,
                                                           outline='lime', width=3)
        self.info_viewer.update_text('c_dim', '{0} x {1}'.format(self.c_dim, self.c_dim))

    def c_lclick(self, e):
        """
        Event handler for a mouse left click on the image viewer in crop mode.
        Updates 'c_img' with cropped image and 'prev_box' with recent clicked area.
        Args:
            e (Event): Mouse event state
        """
        self.img_view.canvas.delete(self.prev_box)
        c_x, c_y = self.mouse_to_arr_coords(self.img_view, e.x, e.y)
        low_x, high_x = c_x - self.c_dim//2, c_x + self.c_dim//2
        low_y, high_y = c_y - self.c_dim//2, c_y + self.c_dim//2
        self.c_img = self.img[low_y:high_y+1, low_x:high_x+1]
        self.crop_view = CanvasImage(self.crop_frame, Image.fromarray(self.c_img))
        self.crop_view.init_view()
        self.crop_view.grid(row=0, column=1, columnspan=5, sticky='nesw')
        self.prev_box = self.img_view.canvas.create_rectangle(c_x - self.c_dim//2, c_y - self.c_dim//2,
                                                              c_x + self.c_dim//2, c_y + self.c_dim//2,
                                                              outline='firebrick', width=2)

    def c_rclick(self, e):
        """
        Event handler for a mouse right click on the image viewer in crop mode.
        Deletes 'prev_box' from the image viewer.
        Args:
            e (Event): Mouse event state
        """
        self.img_view.canvas.delete(self.prev_box)

    def switch_mode(self, mode):
        """
        Switches modes by re-binding and un-binding shortcuts on the canvases
        Args:
            mode (char): Mode key shortcut
        """
        self.img_view.switch_mode(mode)

        if mode == 'v':
            self.img_view.canvas.delete(self.c_box)
        elif mode == 'c':  # Contrast mode
            self.img_view.bind('<Motion>', self.c_move)  # Contrast
            self.img_view.bind('<MouseWheel>', self.c_scroll)
            self.img_view.bind('<ButtonPress-1>', self.c_lclick)
            self.img_view.bind('<ButtonPress-3>', self.c_rclick)

    @staticmethod
    def mouse_to_arr_coords(view, mouse_x, mouse_y):
        """
        Maps mouse coordinates on the current transformed view to array coordinates of the image
        Args:
            view (CanvasImage): Current view the mouse is hovering over
            mouse_x (int): Mouse x coordinate
            mouse_y (int): Mouse y coordinate
        Returns:
            arr_coords (int list): Mapped mouse coordinates to array index
        """
        arr_coords = [0, 0]

        # Get parameters required for mapping coordinates
        canvas_coords = (view.canvas.canvasx(mouse_x), view.canvas.canvasy(mouse_y))
        canvas_origin = view.get_coords()
        image_origin = view.img_origin

        if image_origin[0] < 0:  # Image is clipped on the left side
            arr_coords[0] = int((canvas_coords[0]-canvas_origin[0])/view.imscale - image_origin[0])
        else:  # Image is not clipped on the left side
            arr_coords[0] = int((mouse_x - image_origin[0])/view.imscale)
        if image_origin[1] < 0:  # Image is clipped on the top
            arr_coords[1] = int((canvas_coords[1]-canvas_origin[1])/view.imscale - image_origin[1])
        else:  # Image is not clipped on the top
            arr_coords[1] = int((mouse_y - image_origin[1])/view.imscale)
        return arr_coords


if __name__ == "__main__":
    root = tk.Tk()
    app = App()
    root.mainloop()
