import sqlite3
import typing


class LoginDatabase:
    def __init__(self):
        self._conn = sqlite3.connect('login_database.db')
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self._cursor.execute("CREATE TABLE IF NOT EXISTS users (userID INT, username TEXT NOT NULL, "
                             "password TEXT NOT NULL, PRIMARY KEY(userID AUTOINCREMENT))")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS keys (keyID INT, key_type TEXT NOT NULL, "
                             "api_key TEXT NOT NULL, api_secret TEXT NOT NULL, PRIMARY KEY(keyID AUTOINCREMENT))")

        self._cursor.execute("CREATE TABLE IF NOT EXISTS login (loginID INT, userID INT, keyID INT, "
                             "PRIMARY KEY(loginID AUTOINCREMENT), FOREIGN KEY(userID) REFERENCES users(userID), "
                             "FOREIGN KEY(keyID) REFERENCES keys(keyID))")

        self._conn.commit()

    def _save_user(self, username: str, password: str):
        self._cursor.execute(f"INSERT INTO users VALUES (NULL, ?, ?)", (username, password))
        self._conn.commit()

    def _save_keys(self, api_key: str, api_secret: str):
        self._cursor.execute(f"INSERT INTO keys VALUES (NULL, ?, ?)", (api_key, api_secret))
        self._conn.commit()

    def create_new_login(self, username: str, password: str, api_key: str, api_secret: str):
        self._save_user(username, password)
        self._save_keys(api_key, api_secret)
        self._cursor.execute(f"INSERT INTO login VALUES (NULL, ?, ?)", (username, password, api_key, api_secret))
        self._conn.commit()

    def get_keys_by_user(self):
        pass
