import tkinter as tk
import tkmacosx as tkmac
from Trading.login import Login


class LoginComponent(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._logged = False

        self.title("Login")
        self.geometry("300x200")
        self.resizable(False, False)
        self._create_widgets()

        self._client = None

        self.master.withdraw()

    def _create_widgets(self):
        self._create_entries()
        self._create_button()

    def _create_entries(self):
        label_api_key = tk.Label(self, text="API key", fg='black')
        label_api_key.pack()

        self._api_key = tk.Entry(self)
        self._api_key.pack()

        label_api_secret = tk.Label(self, text="API secret", fg='black')
        label_api_secret.pack()

        self._api_secret = tk.Entry(self)
        self._api_secret.pack()

    def _create_button(self):
        self._button = tkmac.Button(self, text="Login", command=self._login)
        self._button.pack()

    def _login(self):

        try:
            self._success_login = Login(self._api_key.get(), self._api_secret.get(), True, True)
        except:
            print("Wrong API key")

        self._client = self._success_login.return_client()

        self._logged = True
        self.master.deiconify()
        self.destroy()

    def is_logged(self):
        return self._logged

    def get_client(self):
        return self._client

    def get_api_key(self):
        return self._api_key
