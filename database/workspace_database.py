import sqlite3


class WorkspaceDatabase:
    def __init__(self):
        self.conn = sqlite3.connect("workspace.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol text, exchange text)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT, "
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")
        self.conn.commit()

    def save_workspace_data(self, table: str, data):
        # Convert the data parameter to a list of tuples if it's not already
        if not isinstance(data, list) or not all(isinstance(x, tuple) for x in data):
            data = [(x,) for x in data]

        if table == 'watchlist':
            # Clear the watchlist table
            self.cursor.execute("DELETE FROM watchlist")

            # Insert the new rows
            for row in data:
                self.cursor.execute("INSERT INTO watchlist (symbol, exchange) VALUES (?, ?)", row)

        elif table == 'strategies':
            # Clear the strategies table
            self.cursor.execute("DELETE FROM strategies")

            # Insert the new rows
            self.cursor.execute(f"DELETE FROM strategies")
            table_data = self.cursor.execute("SELECT * FROM strategies")
            columns = [description[0] for description in table_data.description]  # Lists the columns of the table
            sql_statement = f"INSERT INTO strategies ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))});"
            self.conn.executemany(sql_statement, data)

        self.conn.commit()

    def get_workspace_data(self, table: str):
        if table == 'watchlist':
            self.cursor.execute("SELECT * FROM watchlist")
        elif table == 'strategies':
            self.cursor.execute("SELECT * FROM strategies")
        return self.cursor.fetchall()
