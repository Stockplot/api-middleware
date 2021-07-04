from flask import Blueprint
from flask_cors import CORS, cross_origin
from flask import request
import yfinance as yf
from flask import jsonify
from decimal import Decimal
import pandas as pd
import numpy as np

GC = Blueprint('GC', __name__)

### Sample request body for /getGoldenCross
# Note - make sure gap b/w start -end > long_window; long_window > short_window
# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "short_window" : 20,
#         "long_window" : 50,
#         "moving_avg"  : "SMA",
#         "investment": 10000
#     }
# }


@GC.route("/getGoldenCross", methods=["POST"])
@cross_origin()
def get_GoldenCross():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        values = values['Close']
        stock_df = pd.DataFrame(values) # convert Series object to dataframe 
        stock_df.columns = {'Close Price'} # assign new colun name
        stock_df.dropna(axis = 0, inplace = True) # remove any null rows 

        #short_window, long_window, moving_avg
        short_window = int(context["short_window"])
        long_window = int(context["long_window"])
        moving_avg = str(context["moving_avg"]) #SMA/EMA

        # column names for long and short moving average columns
        short_window_col = str(short_window) + '_' + moving_avg
        long_window_col = str(long_window) + '_' + moving_avg  
    
        if moving_avg == 'SMA':
            # Create a short simple moving average column
            stock_df[short_window_col] = stock_df['Close Price'].rolling(window = short_window, min_periods = 1).mean()

            # Create a long simple moving average column
            stock_df[long_window_col] = stock_df['Close Price'].rolling(window = long_window, min_periods = 1).mean()

        elif moving_avg == 'EMA':
            # Create short exponential moving average column
            stock_df[short_window_col] = stock_df['Close Price'].ewm(span = short_window, adjust = False).mean()

            # Create a long exponential moving average column
            stock_df[long_window_col] = stock_df['Close Price'].ewm(span = long_window, adjust = False).mean()

        # create a new column 'Signal' such that if faster moving average is greater than slower moving average 
        # then set Signal as 1 else 0.
        stock_df['Signal'] = 0.0  
        stock_df['Signal'] = np.where(stock_df[short_window_col] > stock_df[long_window_col], 1.0, 0.0) 

        # create a new column 'Position' which is a day-to-day difference of the 'Signal' column. 
        stock_df['Position'] = stock_df['Signal'].diff()

        df_pos = stock_df[(stock_df['Position'] == 1) | (stock_df['Position'] == -1)]
        #df_pos['Position'] = df_pos['Position'].apply(lambda x: 'Buy' if x == 1 else 'Sell')
        res = []
        for i in stock_df.index:
            dic = {}
            dic['close'] = stock_df.loc[i, 'Close Price']
            dic['date'] = i.date()
            dic['short'] = stock_df.loc[i, short_window_col]
            dic['long'] = stock_df.loc[i, long_window_col]
            res.append(dic)

        data_length = len(stock_df)

        liquid_amount = int(context["investment"])
        invested_amount = 0
        total_amount = liquid_amount
        num_shares = 0

        ordered_signals = []
        for i in df_pos.index:
            dic = {}
            dic['date'] = i.date()
            dic['signal'] = df_pos.loc[i, 'Position']

            close = df_pos.loc[i, 'Close Price']

            if dic['signal'] == 1.0:
                num_shares = liquid_amount // close
                liquid_amount -= num_shares * close
                invested_amount += num_shares * close
            else:
                liquid_amount += num_shares * close
                invested_amount = 0

            dic['liquid_amount'] = liquid_amount
            dic['invested_amount'] = invested_amount
            dic['pnl'] = liquid_amount + invested_amount - total_amount
            total_amount = liquid_amount + invested_amount
            dic['total_amount'] = total_amount

            ordered_signals.append(dic)

        ordered_signals_len = len(df_pos)        
        

        data = {
            "data": res, 
            "data_length": data_length,
            "ordered_signals": ordered_signals,
            "ordered_signals_len": ordered_signals_len,
            }

        return jsonify(data)