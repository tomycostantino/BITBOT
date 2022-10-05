import sqlite3
import typing
from models import Trade


class WorkspaceData:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.conn.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT, "
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self.conn.commit()  # Saves the changes

    def open_file(self, filename):
        self.conn = sqlite3.connect(filename)

    def save(self, table: str, data: typing.List[typing.Tuple]):

        """
        Erase the previous table content and record new data to it.
        :param table: The table name
        :param data: A list of tuples, the tuples elements must be ordered like the table columns
        :return:
        """

        # Creates the SQL insert statement dynamically
        if table == 'watchlist':
            self.cursor.execute(f"DELETE FROM watchlist")
            table_data = self.cursor.execute("SELECT * FROM watchlist")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO watchlist ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
            self.cursor.executemany(sql_statement, data)

        elif table == 'strategies':
            self.cursor.execute(f"DELETE FROM strategies")
            table_data = self.cursor.execute("SELECT * FROM strategies")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO strategies ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))});"
            self.conn.executemany(sql_statement, data)

        self.conn.commit()

    def get(self, table: str) -> typing.List[sqlite3.Row]:

        """
        Get all the rows recorded for the table.
        :param table: The table name to get the rows from. e.g: strategies, watchlist
        :return: A list of sqlite3.Rows accessible like Python dictionaries.
        """
        self.cursor.execute(f"SELECT * FROM {table}")
        data = self.cursor.fetchall()

        return data


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
        self._cursor.execute(f'INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (trade.time,
                             trade.contract.symbol, trade.strategy, trade.side, str(trade.entry_price), trade.status,
                             str(trade.pnl), trade.quantity, trade.entry_id))

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
