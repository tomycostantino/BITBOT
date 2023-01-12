import sqlite3
import typing


class LoginDatabase:
    def __init__(self):
        self._conn = sqlite3.connect('login_database.db')
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self._cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT NOT NULL, password TEXT NOT NULL, "
                             "PRIMARY KEY(username))")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS keys (username TEXT NOT NULL, testnet BOOL, futures BOOL, "
                             "api_key TEXT NOT NULL, api_secret TEXT NOT NULL, FOREIGN KEY(username) REFERENCES "
                             "users(username))")

        self._conn.commit()

    def _save_user(self, username: str, password: str):
        self._cursor.execute(f"INSERT INTO users VALUES (?, ?)", (username, password))
        self._conn.commit()

    def _save_keys(self, username: str, testnet: bool, futures: bool, api_key: str, api_secret: str):
        # self._cursor.execute(f"INSERT INTO keys VALUES (?, ?, ?, ?)", ('testnet', api_key, api_secret, 'tomi'))
        '''
        self._cursor.execute(f"INSERT OR IGNORE INTO keys (key_type, api_key, api_secret, user) VALUES (?, ?, ?, ?)",
                             ('testnet', api_key, api_secret, 'tomi'))
        '''
        self._cursor.execute(f"INSERT INTO keys (username, testnet, futures, api_key, api_secret) VALUES (?, ?, ?, ?, "
                             f"?)", (username, testnet, futures, api_key, api_secret))
        self._conn.commit()

    def create_user(self, username: str, password: str, testnet: bool, futures: bool, api_key: str, api_secret: str):
        self._save_user(username, password)
        self._save_keys(username, testnet, futures, api_key, api_secret)

    def get_keys_by_user(self):
        pass

    def user_exists(self, username: str):
        self._cursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
        result = self._cursor.fetchone()
        if result[0] == 1:
            return True
        return False
