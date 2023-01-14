import tkinter as tk

from interface.styling import *
from datetime import datetime


# logging frame on the left of the GUI that display what is going on
# while using the program
class Logging(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        header = tk.Label(self, text='Event logging', bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT_2)
        header.pack(side=tk.TOP, fill=tk.X, expand=True, ipady=5)

        # create the text display
        self._logging_text = tk.Text(self, width=60, state=tk.DISABLED, bg=BG_COLOR_2, fg=FG_COLOR,
                                     font=GLOBAL_FONT, highlightthickness=False, bd=0)
        self._logging_text.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

    # function that adds the new logs to the screen
    def add_log(self, message: str):
        self._logging_text.configure(state=tk.NORMAL)

        self._logging_text.insert('1.0', datetime.utcnow().strftime('%a %H:%M:%S ::' + message + '\n'))

        self._logging_text.configure(state=tk.DISABLED)
