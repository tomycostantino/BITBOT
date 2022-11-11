import tkinter as tk
import tkmacosx as tkmac


class Login(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Login")
        self.geometry("300x200")
        self.resizable(False, False)
        self._create_widgets()

    def _create_widgets(self):
        self._create_entry()
        self._create_button()

    def _create_entry(self):
        self._entry = tk.Entry(self)
        self._entry.pack()

    def _create_button(self):
        self._button = tkmac.Button(self, text="Login", command=self._login)
        self._button.pack()

    def _login(self):
        self._api_key = self._entry.get()
        self.destroy()

    def get_api_key(self):
        return self._api_key
