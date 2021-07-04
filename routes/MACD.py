from flask import Blueprint
from flask_cors import CORS, cross_origin
from flask import request
import yfinance as yf
from flask import jsonify
from decimal import Decimal


MACD = Blueprint('MACD', __name__)

### Sample request body for /getMACD
# Note - make sure gap b/w start -end > 27 days
# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "upper_band" : 26,
#         "lower_band" : 12,
#         "buy_lim"  : 10,
#         "sell_lim" : -10,
#         "investment": 10000
#     }
# }


@MACD.route("/getMACD", methods=["POST"])
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

            for i in range(0, values.shape[0] - upper_band):
                upper_lim_ma.append(sum(daily_close[i : i + upper_band]) / upper_band)

            for i in range(0, len(upper_lim_ma)):
                macd_val.append(
                    lower_lim_ma[i + (upper_band - lower_band)] - upper_lim_ma[i]
                )

            for i in range(upper_band - lower_band, values.shape[0]):
                date.append(values.iloc[i].name.strftime("%Y-%m-%d"))
                close_val.append(values.iloc[i]["Close"])

            for i in range(0, len(macd_val)):
                mv[i] = {
                    "macd": str(macd_val[i]),
                    "date": date[i],
                    "close": close_val[i]
                }

            for i in range(0, len(mv)):
                if Decimal(mv[i]["macd"]) > Decimal(buy_lim):
                    signals.append(
                        {
                            "date": mv[i]["date"],
                            "signal": "1",
                            "close": mv[i]["close"],
                            "macd" : mv[i]["macd"],

                        }
                    )
                if Decimal(mv[i]["macd"]) < Decimal(sell_lim):
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
