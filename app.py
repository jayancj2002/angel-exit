from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

last_exit_time = 0
EXIT_COOLDOWN = 180


@app.route("/")
def home():
    return "Server Live ✅"


@app.route("/exit", methods=["POST"])
def exit_trade():
    global last_exit_time

    now = time.time()

    if now - last_exit_time < EXIT_COOLDOWN:
        return jsonify({"status": "Cooldown Active"})

    try:
        from SmartApi import SmartConnect
        import pyotp

        API_KEY = os.getenv("API_KEY")
        CLIENT_CODE = os.getenv("CLIENT_CODE")
        PASSWORD = os.getenv("PASSWORD")
        TOTP_KEY = os.getenv("TOTP_KEY")

        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_KEY).now()

        obj.generateSession(CLIENT_CODE, PASSWORD, totp)

        positions = obj.position().get("data", [])

        exited = False

        for pos in positions:

            netqty = int(pos.get("netqty", 0))
            buyqty = int(pos.get("buyqty", 0))
            sellqty = int(pos.get("sellqty", 0))

            qty = netqty if netqty != 0 else (buyqty - sellqty)

            if qty != 0:

                transaction = "SELL" if qty > 0 else "BUY"

                orderparams = {
                    "variety": "NORMAL",
                    "tradingsymbol": pos["tradingsymbol"],
                    "symboltoken": pos["symboltoken"],
                    "transactiontype": transaction,
                    "exchange": pos["exchange"],
                    "ordertype": "MARKET",
                    "producttype": "INTRADAY",
                    "duration": "DAY",
                    "quantity": abs(qty)
                }

                obj.placeOrder(orderparams)
                exited = True

        last_exit_time = now

        if exited:
            return jsonify({"status": "EXIT EXECUTED"})
        else:
            return jsonify({"status": "NO POSITION FOUND"})

    except Exception as e:
        return jsonify({"error": str(e)})
