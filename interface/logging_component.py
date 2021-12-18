import tkinter as tk
from interface.styling import *
from datetime import datetime


class Logging(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._logging_text = tk.Text(self, height=10, width=60, state=tk.DISABLED, bg=BG_COLOR_2, fg=FG_COLOR,
                                     font=GLOBAL_FONT)
        self._logging_text.pack(side=tk.TOP)

    def add_log(self, message: str):
        self._logging_text.configure(state=tk.NORMAL)

        self._logging_text.insert('1.0', datetime.utcnow().strftime('%a %H:%M:%S ::' + message + '\n'))

        self._logging_text.configure(state=tk.DISABLED)
