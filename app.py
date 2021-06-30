import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin
from decimal import Decimal

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

### Sample request body for /

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30"
#     }
# }


@app.route("/", methods=["POST"])
@cross_origin()
def solve():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        res = {}

        for i in range(0, values.shape[0]):

            res[i] = {
                "date": values.iloc[i].name.strftime("%Y-%m-%d"),
                "open": values.iloc[i]["Open"],
                "high": values.iloc[i]["High"],
                "low": values.iloc[i]["Low"],
                "close": values.iloc[i]["Close"],
                "volume": values.iloc[i]["Volume"],
                "dividends": values.iloc[i]["Dividends"],
                "stock splits": values.iloc[i]["Stock Splits"],
            }

        data = {
            "length": values.shape[0],
            "data": res,
        }

        return jsonify(data)


### Sample request body for /getBBands

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "window": 20,
#         "sdfactor": 2
#     }
# }


@app.route("/getBBands", methods=["POST"])
@cross_origin()
def BBands():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        close = values["Close"]
        window = int(context["window"])
        sdfactor = float(context["sdfactor"])

        idx = 0
        price_sum = 0

        moving_average = []
        uband = []
        lband = []

        res = {}

        selling = False
        ordered_signals = []
        liquid_amount = int(context["investment"])
        invested_amount = 0
        num_shares = 0
        last_total = liquid_amount

        for price in close:

            price_sum += price
            sd_sum = 0

            if idx >= window:
                price_sum -= close[idx - window]
                avg = price_sum / window

                for i in range(idx - window, idx + 1):
                    sd_sum += (close[i] - avg) ** 2
                sd_sum /= window

                res[idx - window] = {
                    "close": close[idx - window],
                    "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                    "moving_average": avg,
                    "upper_band": avg + sdfactor * (sd_sum ** 0.5),
                    "lower_band": avg - sdfactor * (sd_sum ** 0.5),
                }

                if (close[idx - window] <= avg - sdfactor * (sd_sum ** 0.5)) and selling == False:
                    num_shares = liquid_amount // close[idx - window]
                    liquid_amount -= num_shares * close[idx - window]
                    invested_amount += num_shares * close[idx - window]
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append({
                        "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                        "signal": 1,
                        "price": close[idx - window],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    })
                    selling = True
                elif (close[idx - window] >= avg + sdfactor * (sd_sum ** 0.5)) and selling == True:
                    liquid_amount += num_shares * close[idx - window]
                    invested_amount = 0
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append({
                        "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                        "signal": -1,
                        "price": close[idx - window],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    })
                    selling = False



            idx += 1

        data = {
            "data": res, 
            "data_length": idx - window,
            "ordered_signals": ordered_signals,
            "ordered_signals_len": len(ordered_signals),
            }

        return jsonify(data)


### Sample request body for /getRSI

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "window": 30,
#         "upper_band" : 70,
#         "lower_band" : 30
#     }
# }


@app.route("/getRSI", methods=["POST"])
@cross_origin()
def RSIndex():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        window = int(context["window"])
        upper_band = int(context["upper_band"])
        lower_band = int(context["lower_band"])
        liquid_amount = int(context["investment"])

        points_gain = []
        points_lost = []

        for i in range(0, values.shape[0] - 1):
            change = Decimal(values.iloc[i + 1]["Close"]) - Decimal(
                values.iloc[i]["Close"]
            )
            if change > 0:
                points_gain.append(change)
                points_lost.append(Decimal(0))
            else:
                points_lost.append(change)
                points_gain.append(Decimal(0))

        pl_avg_ar = []
        pg_avg_ar = []
        rs_ar = []
        rsi_ar = []
        date = []

        for i in range(0, values.shape[0] - window):
            pg_avg_ar.append(sum(points_gain[i : i + window]) / window)
            pl_avg_ar.append(sum(points_lost[i : i + window]) * Decimal(-1) / window)

        for i in range(0, len(pg_avg_ar)):
            rs_ar.append(str(pg_avg_ar[i] / pl_avg_ar[i]))
            rsi_ar.append(str(100 - (100 / (1 + Decimal(rs_ar[i])))))

        pg = {}
        pl = {}
        data_log = {}
        close_val = []
        date = []

        for i in range(window, values.shape[0]):
            date.append(values.iloc[i].name.strftime("%Y-%m-%d"))
            close_val.append(values.iloc[i]["Close"])

        for i in range(0, values.shape[0] - window):
            data_log[i] = {
                "date": date[i],
                "RS": rs_ar[i],
                "RSI": rsi_ar[i],
                "close": close_val[i],
            }

        signals = []
        ordered_signals = []
        selling = False

        invested_amount = 0
        num_shares = 0
        last_total = liquid_amount

        for i in range(0, len(data_log)):
            if Decimal(data_log[i]["RSI"]) > Decimal(0) and Decimal(
                data_log[i]["RSI"]
            ) < Decimal(lower_band):
                signals.append(
                    {
                        "date": data_log[i]["date"],
                        "signal": "1",
                        "close": data_log[i]["close"],
                        "rsi": data_log[i]["RSI"],
                    }
                )
            if Decimal(data_log[i]["RSI"]) > Decimal(upper_band) and Decimal(
                data_log[i]["RSI"]
            ) < Decimal(100):
                signals.append(
                    {
                        "date": data_log[i]["date"],
                        "signal": "-1",
                        "close": data_log[i]["close"],
                        "rsi": data_log[i]["RSI"],
                    }
                )
            else:
                pass

        for i in range(0, len(signals)):
            if signals[i]["signal"] == "1" and selling == False:
                num_shares = liquid_amount // signals[i]["close"]
                liquid_amount -= num_shares * signals[i]["close"]
                invested_amount += num_shares * signals[i]["close"]
                total_amount = liquid_amount + invested_amount
                pnl = total_amount - last_total
                last_total = total_amount
                ordered_signals.append(
                    {
                        "date": signals[i]["date"],
                        "signal": signals[i]["signal"],
                        "price": signals[i]["close"],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    }
                )
                selling = True
            elif signals[i]["signal"] == "-1" and selling == True:
                liquid_amount += num_shares * signals[i]["close"]
                invested_amount = 0
                total_amount = liquid_amount + invested_amount
                pnl = total_amount - last_total
                last_total = total_amount
                ordered_signals.append(
                    {
                        "date": signals[i]["date"],
                        "signal": signals[i]["signal"],
                        "price": signals[i]["close"],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    }
                )
                selling = False

        data = {
            "data": data_log,
            "data_len": len(data_log),
            # "signal": signals,
            "orderd_signals": ordered_signals,
            "ordered_signals_len": len(ordered_signals),
        }

        return jsonify(data)


### Sample request body for /getMACD
# Note - make sure gap b/w start -end > 27 days
# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
##        "upper_band" : 26,
#         "lower_band" : 12,
#         "buy_lim"  : 10,
#         "sell_lim" : -10
#     }
# }


@app.route("/getMACD", methods=["POST"])
@cross_origin()
def get_MACD():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        upper_band = int(context["upper_band"])
        lower_band = int(context["lower_band"])
        buy_lim = int(context["buy_lim"])
        sell_lim = int(context["sell_lim"])
        liquid_amount = int(context["investment"])

        daily_close = []

        for i in range(0, values.shape[0]):
            daily_close.append(
                Decimal(values.iloc[i]["Close"]),
            )

        lower_lim_ma = []
        upper_lim_ma = []
        date = []

        macd_val = []
        mv = {}
        signals = []
        selling = False
        ordered_signals = []
        close_val =[]

        data = {}

        try:
            for i in range(0, values.shape[0] - lower_band):
                lower_lim_ma.append(sum(daily_close[i : i + lower_band]) / lower_band)

            # print("step1")

            for i in range(0, values.shape[0] - upper_band):
                upper_lim_ma.append(sum(daily_close[i : i + upper_band]) / upper_band)

            for i in range(0, len(upper_lim_ma)):
                macd_val.append(
                    lower_lim_ma[i + (upper_band - lower_band)] - upper_lim_ma[i]
                )
            # print("step2")

            for i in range(upper_band - lower_band, values.shape[0]):
                date.append(values.iloc[i].name.strftime("%Y-%m-%d"))
                close_val.append(values.iloc[i]["Close"])

                

            # print("stepdate")
            for i in range(0, len(macd_val)):
                mv[i] = {
                    "macd": str(macd_val[i]),
                    "date": date[i],
                    "close": close_val[i]
                }


            # print("step4")

            for i in range(0, len(mv)):
                print("hi")
                if Decimal(mv[i]["macd"]) > Decimal(buy_lim):
                    print("first case")
                    signals.append(
                        {
                            "date": mv[i]["date"],
                            "signal": "1",
                            "close": mv[i]["close"],
                            "macd" : mv[i]["macd"],

                        }
                    )
                if Decimal(mv[i]["macd"]) < Decimal(sell_lim):
                    print("second case")
                    signals.append(
                        {
                            "date": mv[i]["date"],
                            "signal": "-1",
                            "close": mv[i]["close"],
                            "macd" : mv[i]["macd"],
                        }
                    )
                else:
                    pass
            print("step4pass")
            invested_amount = 0
            num_shares = 0
            last_total = liquid_amount



            for i in range(0, len(signals)):
                if signals[i]["signal"] == "1" and selling == False:
                    num_shares = liquid_amount // signals[i]["close"]
                    liquid_amount -= num_shares * signals[i]["close"]
                    invested_amount += num_shares * signals[i]["close"]
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append(
                        {
                            "date": signals[i]["date"],
                            "signal": signals[i]["signal"],
                            "price": signals[i]["close"],
                            "invested_amount": invested_amount,
                            "liquid_amount": liquid_amount,
                            "total_amount": total_amount,
                            "pnl": pnl,
                        }
                    )
                    selling = True
                elif signals[i]["signal"] == "-1" and selling == True:
                    liquid_amount += num_shares * signals[i]["close"]
                    invested_amount = 0
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append(
                        {
                            "date": signals[i]["date"],
                            "signal": signals[i]["signal"],
                            "price": signals[i]["close"],
                            "invested_amount": invested_amount,
                            "liquid_amount": liquid_amount,
                            "total_amount": total_amount,
                            "pnl": pnl,
                        }
                    )
                    selling = False

            data = {
                "data": mv,
                "data_len": len(mv),
                "ordered_signal": ordered_signals,
                "ordered_ signals_len": len(ordered_signals),
            }

            return jsonify(data)

        except:
            print("Date range less than 1 month")
            data = {"Error": "no Data"}
            return data



### Sample request body for /getGoldenCross
# Note - make sure gap b/w start -end > long_window; long_window > short_window
# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
##        "short_window" : 20,
#         "long_window" : 50,
#         "moving_avg"  : SMA
#     }
# }


@app.route("/getGoldenCross", methods=["POST"])
@cross_origin()
def get_GoldenCross():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        stock_df = values['Close']
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

        ordered_signals = []
        for i in df_pos.index:
            dic = {}
            dic['date'] = i.date()
            dic['signal'] = df_pos.loc[i, 'Position']
            ordered_signals.append(dic)

        ordered_signals_len = len(df_pos)        
        

        data = {
            "data": res, 
            "data_length": data_length,
            "ordered_signals": ordered_signals,
            "ordered_signals_len": ordered_signals_len,
            }

        return jsonify(data)


if __name__ == "__main__":
    app.run()
