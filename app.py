from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return "Server Live ✅"


# =========================
# EXIT WEBHOOK (DEBUG MODE)
# =========================
@app.route("/exit", methods=["POST"])
def exit_trade():

    try:
        from SmartApi import SmartConnect
        import pyotp

        print("EXIT SIGNAL RECEIVED")

        API_KEY = os.getenv("API_KEY")
        CLIENT_CODE = os.getenv("CLIENT_CODE")
        PASSWORD = os.getenv("PASSWORD")
        TOTP_KEY = os.getenv("TOTP_KEY")

        # ---- LOGIN ----
        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_KEY).now()

        session = obj.generateSession(
            CLIENT_CODE,
            PASSWORD,
            totp
        )

        print("LOGIN SUCCESS")

        # ---- FETCH POSITIONS ----
        positions = obj.position().get("data", [])

        print("POSITIONS FOUND:", positions)

        exited = False

        for pos in positions:

            netqty = int(pos.get("netqty", 0))
            buyqty = int(pos.get("buyqty", 0))
            sellqty = int(pos.get("sellqty", 0))

            qty = netqty if netqty != 0 else (buyqty - sellqty)

            print("CHECKING POSITION:", pos["tradingsymbol"], qty)

            if qty != 0:

                transaction = "SELL" if qty > 0 else "BUY"

                orderparams = {
                    "variety": "NORMAL",
                    "tradingsymbol": pos["tradingsymbol"],
                    "symboltoken": pos["symboltoken"],
                    "transactiontype": transaction,
                    "exchange": pos["exchange"],
                    "ordertype": "MARKET",
                    "producttype": pos["producttype"],
                    "duration": "DAY",
                    "quantity": abs(qty)
                }

                print("PLACING ORDER:", orderparams)

                response = obj.placeOrder(orderparams)

                print("ORDER RESPONSE:", response)

                exited = True

        if exited:
            return jsonify({"status": "EXIT ORDER SENT"})
        else:
            return jsonify({"status": "NO POSITION FOUND"})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)})
