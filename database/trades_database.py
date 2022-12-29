import sqlite3
import typing
from Trading.models import Trade


class TradesDatabase:
    def __init__(self):
        self._conn = sqlite3.connect('trades.db')
        self._conn.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self._cursor = self._conn.cursor()

        self._cursor.execute("CREATE TABLE IF NOT EXISTS trades (time TEXT, contract TEXT, strategy TEXT, side TEXT, "
                             "entryPrice TEXT, status TEXT, pnl TEXT, quantity TEXT, entryId TEXT)")
        self._conn.commit()  # Saves the changes

    def add_new_trade(self, trade: Trade):
        '''
        Add a new trade to the database
        :param trade:
        :return:
        '''

        self._cursor.execute(f'INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (str(trade.time),
                             trade.contract.symbol, str(trade.strategy), trade.side, str(trade.entry_price), trade.status,
                             str(trade.pnl), str(trade.quantity), str(trade.entry_id)))
        self._conn.commit()

    def get_trades(self):
        '''
        Get all the rows recorded for the table.
        :return:
        '''

        self._cursor.execute(f"SELECT * FROM trades")
        data = self._cursor.fetchall()
        return data

    def close(self):
        '''
        Close the database connection
        :return:
        '''
        self._conn.close()
