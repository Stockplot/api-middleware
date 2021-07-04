import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin
from decimal import Decimal

from routes.OHLC import OHLC 
from routes.BollingerBands import BB 
from routes.RSI import RSI 
from routes.MACD import MACD 
from routes.GoldenCross import GC 

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

app.register_blueprint(OHLC)
app.register_blueprint(BB)
app.register_blueprint(RSI)
app.register_blueprint(MACD)
app.register_blueprint(GC)

if __name__ == "__main__":
    app.run()
