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
        self._login = Login()

        self.master.withdraw()

    def _create_widgets(self):

        create_new_user = tkmac.Button(self, text="Create new user", command=self._create_new_user_UI)
        create_new_user.pack()

        login = tkmac.Button(self, text="Login", command=self._login_interface)
        login.pack()

    def _create_new_user_UI(self):
        self._popup_create_user = tk.Toplevel(self)
        self._popup_create_user.wm_title('Create new user')

        username_label = tk.Label(self._popup_create_user, text="Insert username", fg='black', pady=10, padx=10)
        username_label.pack()

        username = tk.Entry(self._popup_create_user)
        username.pack()

        password_label = tk.Label(self._popup_create_user, text="Insert password", fg='black', pady=10, padx=10)
        password_label.pack()

        password = tk.Entry(self._popup_create_user)
        password.pack()

        label_api_key = tk.Label(self._popup_create_user, text="API Key", fg='black', pady=10, padx=10)
        label_api_key.pack()

        api_key = tk.Entry(self._popup_create_user)
        api_key.pack()

        label_api_secret = tk.Label(self._popup_create_user, text="API Secret", fg='black', pady=10, padx=10)
        label_api_secret.pack()

        api_secret = tk.Entry(self._popup_create_user)
        api_secret.pack()

        testnet_confirmation = tk.Label(self._popup_create_user, text="Testnet?", fg='black')
        testnet_confirmation.pack()
        testnet_switch_var = tk.BooleanVar()
        testnet_switch_button = tk.Checkbutton(self._popup_create_user, variable=testnet_switch_var)
        testnet_switch_button.pack()

        futures_confirmation = tk.Label(self._popup_create_user, text="Futures?", fg='black')
        futures_confirmation.pack()
        futures_switch_var = tk.BooleanVar()
        futures_switch_button = tk.Checkbutton(self._popup_create_user, variable=futures_switch_var)
        futures_switch_button.pack()

        submit = tkmac.Button(self._popup_create_user, text='Create user',
                              command=lambda: self._create_user(username.get(), password.get(),
                                                                self.get_switch_state(testnet_switch_var),
                                                                self.get_switch_state(futures_switch_var),
                                                                api_key.get(), api_secret.get()))
        submit.pack()

    def get_switch_state(self, switch):
        return switch.get()

    def _create_user(self, username: str, password: str, testnet: bool, futures: bool, api_key: str, api_secret: str):
        if self._login.create_user(username, password, testnet, futures, api_key, api_secret):
            self._inform_user_created()
            self._do_login(username, password)
        else:
            self._inform_user_exists()

    def _inform_user_created(self):
        popup = tk.Toplevel(self)
        popup.wm_title('CAUTION')
        warning = tk.Label(popup, text='User created')
        warning.pack()

    def _inform_user_exists(self):
        popup = tk.Toplevel(self._popup_create_user)
        popup.wm_title('CAUTION')
        warning = tk.Label(popup, text='Username already exists')
        warning.pack()

    def _login_interface(self):
        self._popup_login = tk.Toplevel(self)
        self._popup_login.wm_title('Create new user')

        username_label = tk.Label(self._popup_login, text="Insert username", fg='black', pady=10, padx=10)
        username_label.pack()

        username = tk.Entry(self._popup_login)
        username.pack()

        password_label = tk.Label(self._popup_login, text="Insert password", fg='black', pady=10, padx=10)
        password_label.pack()

        password = tk.Entry(self._popup_login)
        password.pack()

        login_button = tkmac.Button(self._popup_login, text='Login',
                                    command=lambda: self._do_login(username.get(), password.get()))
        login_button.pack()

    def _do_login(self, username: str, password: str):

        try:
            self._login.login(username, password)
        except:
            print("Wrong API key")

        self._logged = True
        self.master.deiconify()
        self.destroy()

    def is_logged(self):
        return self._logged

    def get_client(self):
        return self._login.return_client()
