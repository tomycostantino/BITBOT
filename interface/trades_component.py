import tkinter as tk

from interface.styling import *
from interface.scrollable_frame import ScrollableFrame
from Trading.models import *


# display the current trades characteristics
# time  symbol  exchange  strategy  side  quantity  status  pnl
class TradesWatch(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body_widgets = dict()

        self._headers = ["time", "symbol", "exchange", "strategy", "side", "quantity", "status", "pnl"]

        self._table_frame = tk.Frame(self, height=20, width=950, bg=BG_COLOR)
        self._table_frame.grid_propagate(0)
        self._table_frame.pack(side=tk.TOP)

        header = tk.Label(self._table_frame, text="Trades", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT_2)
        header.pack(side=tk.TOP, fill=tk.X, expand=True)

        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        self._col_width = 11

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._headers_frame, text=h.capitalize(), bg=BG_COLOR,
                              fg=FG_COLOR, font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx, padx=10)

        header = tk.Label(self._headers_frame, text='', bg=BG_COLOR,
                          fg=FG_COLOR, font=GLOBAL_FONT, width=2)
        header.grid(row=0, column=len(self._headers))

        self._headers_frame.pack(side=tk.TOP, anchor='nw')

        self._body_frame = ScrollableFrame(self._table_frame, height=250, width=950, bg=BG_COLOR)
        self._body_frame.grid_propagate(0)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor='nw')

        self._headers_frame.pack(side=tk.TOP, anchor='nw')

        # self._body_frame = ScrollableFrame(self, bg=BG_COLOR, height=250)
        # self._body_frame.pack(side=tk.TOP, anchor='nw', fill=tk.X)

        for h in self._headers:
            self.body_widgets[h] = dict()
            if h in ["status", "pnl", "quantity"]:
                self.body_widgets[h + "_var"] = dict()

        self._body_index = 0

    # add the new trades to the watchlist
    def add_trade(self, trade: Trade):

        """
        Add a new trade row.
        :param trade:
        :return:
        """

        b_index = self._body_index

        t_index = trade.time  # This is the trade row identifier, Unix Timestamp in milliseconds, so should be unique.

        dt_str = datetime.datetime.fromtimestamp(trade.time / 1000).strftime("%b %d %H:%M")

        self.body_widgets['time'][t_index] = tk.Label(self._body_frame.sub_frame, text=dt_str, bg=BG_COLOR,
                                                      fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['time'][t_index].grid(row=b_index, column=0, padx=10)

        # Symbol

        self.body_widgets['symbol'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.contract.symbol,
                                                        bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                        width=self._col_width)
        self.body_widgets['symbol'][t_index].grid(row=b_index, column=1, padx=10)

        # Exchange

        self.body_widgets['exchange'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                          text=trade.contract.exchange.capitalize(),
                                                          bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                          width=self._col_width)
        self.body_widgets['exchange'][t_index].grid(row=b_index, column=2, padx=10)

        # Strategy

        self.body_widgets['strategy'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.strategy, bg=BG_COLOR,
                                                          fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['strategy'][t_index].grid(row=b_index, column=3, padx=10)

        # Side

        self.body_widgets['side'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.side.capitalize(),
                                                      bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                      width=self._col_width)
        self.body_widgets['side'][t_index].grid(row=b_index, column=4, padx=10)

        # Quantity

        self.body_widgets['quantity_var'][
            t_index] = tk.StringVar()  # Variable because the order is not always filled immediately
        self.body_widgets['quantity'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                          textvariable=self.body_widgets['quantity_var'][t_index],
                                                          bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                          width=self._col_width)
        self.body_widgets['quantity'][t_index].grid(row=b_index, column=5, padx=10)

        # Status

        self.body_widgets['status_var'][t_index] = tk.StringVar()
        self.body_widgets['status'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                        textvariable=self.body_widgets['status_var'][t_index],
                                                        bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                        width=self._col_width)
        self.body_widgets['status'][t_index].grid(row=b_index, column=6, padx=10)

        # PNL

        self.body_widgets['pnl_var'][t_index] = tk.StringVar()
        self.body_widgets['pnl'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['pnl_var'][t_index], bg=BG_COLOR,
                                                     fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['pnl'][t_index].grid(row=b_index, column=7, padx=10)

        self._body_index += 1

