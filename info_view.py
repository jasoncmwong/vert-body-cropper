import tkinter as tk

INFO_ROWS = 195


class InfoView:
    def __init__(self, frame):
        self.info_frame = tk.Frame(frame, bg='black', highlightthickness=0, bd=0)

        for row in range(INFO_ROWS):
            self.info_frame.rowconfigure(row, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=2)
        self.info_frame.grid_columnconfigure(1, weight=10)
        self.info_frame.grid_columnconfigure(2, weight=83)
        self.info_frame.grid_columnconfigure(3, weight=10)
        self.info_frame.grid_columnconfigure(4, weight=83)
        self.info_frame.grid_columnconfigure(5, weight=10)
        self.info_frame.grid_columnconfigure(6, weight=2)

        self.label_dict = {}
        self.row_num = 0  # Current row number

    def add_label(self, text, key=None):
        """
        Adds an entry into the info viewer and displays it on the GUI along with a modifiable label if a key is given.
        Updates 'row_num' along with 'label_dict' if a key is given.
        Args:
            text (str): Text to be displayed
            key (str): Key used to reference the modifiable entry in 'label_dict'
        """
        if key is None:
            temp_label = tk.Label(self.info_frame, text=text, anchor=tk.CENTER)
            temp_label.grid(row=self.row_num, column=1, sticky='new')
        else:
            temp_label = tk.Label(self.info_frame, text=text + ':', anchor='w')
            temp_label.grid(row=self.row_num, column=1, sticky='new')
            self.label_dict[key] = tk.Label(self.info_frame, text='-', anchor='w')  # Default value until modification
            self.label_dict[key].grid(row=self.row_num, column=2, columnspan=2, sticky='new')
        self.row_num += 1

    def update_text(self, key, text):
        """
        Modifies text in an entry in the label dictionary.
        Updates 'label_dict' entry text.
        Args:
            key (str): Key used to reference the modifiable entry in 'label_dict'
            text (str): Text used to replace the referenced entry
        """
        self.label_dict[key]['text'] = text

    def grid(self, **kw):
        """
        Used to place the info viewer in the desired place on the GUI.
        """
        self.info_frame.grid(**kw)
        self.info_frame.grid(sticky='nesw')
        self.info_frame.rowconfigure(0, weight=1)  # make canvas expandable
        self.info_frame.columnconfigure(0, weight=1)
