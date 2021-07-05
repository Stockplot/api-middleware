from flask import Blueprint
from flask_cors import CORS, cross_origin
from flask import request
import yfinance as yf
from flask import jsonify
from decimal import Decimal

RSI = Blueprint('RSI', __name__)

### Sample request body for /getRSI

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "window": 30,
#         "upper_band" : 70,
#         "lower_band" : 30,
#         "investment": 10000
#     }
# }


@RSI.route("/getRSI", methods=["POST"])
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