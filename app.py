from flask import Flask, request, jsonify
from SmartApi import SmartConnect
import pyotp
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
CLIENT_CODE = os.environ.get("CLIENT_CODE")
PASSWORD = os.environ.get("PASSWORD")
TOTP_KEY = os.environ.get("TOTP_KEY")

def angel_login():
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_KEY).now()
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
    return obj

@app.route('/exit', methods=['POST'])
def exit_trade():
    try:
        angel = angel_login()
        positions = angel.position()['data']

        for pos in positions:
            qty = int(pos['netqty'])

            if qty != 0:
                angel.placeOrder({
                    "variety": "NORMAL",
                    "tradingsymbol": pos['tradingsymbol'],
                    "symboltoken": pos['symboltoken'],
                    "transactiontype": "SELL" if qty > 0 else "BUY",
                    "exchange": pos['exchange'],
                    "ordertype": "MARKET",
                    "producttype": pos['producttype'],
                    "duration": "DAY",
                    "quantity": abs(qty)
                })

        return jsonify({"status":"All positions squared off"})

    except Exception as e:
        return jsonify({"error":str(e)})

@app.route('/')
def home():
    return "Angel Exit Server Running"
