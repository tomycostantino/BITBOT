import sqlite3
import typing
from Trading.models import Trade


class Database:
    def __init__(self):
        self._conn = sqlite3.connect('new_database.db')
        self._conn.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self._cursor = self._conn.cursor()

        self._cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT, "
                             "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS trades (time TEXT, contract TEXT, strategy TEXT, side TEXT, "
                             "entryPrice TEXT, status TEXT, pnl TEXT, quantity TEXT, entryId TEXT)")
        self._conn.commit()  # Saves the changes
        # self._conn.close() # Close connection

    def save_workspace_data(self, table: str, data: typing.List[typing.Tuple]):
        '''
        Erase the previous table content and record new data to it.
        :param table:
        :param data:
        :return:
        '''

        if table == 'watchlist':
            self._cursor.execute(f"DELETE FROM watchlist")
            table_data = self._cursor.execute("SELECT * FROM watchlist")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO watchlist ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
            self._cursor.executemany(sql_statement, data)

        elif table == 'strategies':
            self._cursor.execute(f"DELETE FROM strategies")
            table_data = self._cursor.execute("SELECT * FROM strategies")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO strategies ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))});"
            self._conn.executemany(sql_statement, data)

        self._conn.commit()

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

    def get_workspace_data(self, table: str):
        '''
        Get all the rows recorded for the table.
        :param table:
        :return:
        '''

        self._cursor.execute(f"SELECT * FROM {table}")
        data = self._cursor.fetchall()
        return data

    def get_trades_data(self):
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
