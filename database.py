import sqlite3
import typing


class WorkspaceData:
    def __init__(self):
        self.conn = sqlite3.connect("database.db")
        self.conn.row_factory = sqlite3.Row  # Makes the data retrieved from the database accessible by their column name
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")

        self._strat_cols = ['strategy_type', 'contract', 'timeframe', 'balance_pct',
                            'take_profit', 'stop_loss', 'extra_params']
        # for strat in self._strat_cols:
        # addColumn = 'ALTER TABLE strategies ADD COLUMN' + self._strat_cols[0]
        # self.cursor.execute(addColumn)
        # self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT, "
        #                     "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT"
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self.conn.commit()  # Saves the changes

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
            table_data = self.cursor.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO watchlist ({', '.join(columns)}) VALUES ({', '.join(['?'] * 2)})"
            self.cursor.executemany(sql_statement, data)

        elif table == 'strategies':
            self.cursor.execute(f"DELETE FROM strategies")
            table_data = self.cursor.execute(f"SELECT * FROM strategies")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            self.conn.executemany(f'INSERT INTO strategies ({", ".join(columns)}) VALUES ({", ".join(["?"] * 2)})', data)

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
