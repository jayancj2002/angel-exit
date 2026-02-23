from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Angel Exit Server Running"


@app.route("/exit", methods=["POST"])
def exit_trade():
    try:
        from SmartApi import SmartConnect
        import pyotp

        API_KEY = os.environ.get("API_KEY")
        CLIENT_CODE = os.environ.get("CLIENT_CODE")
        PASSWORD = os.environ.get("PASSWORD")
        TOTP_KEY = os.environ.get("TOTP_KEY")

        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_KEY).now()
        obj.generateSession(CLIENT_CODE, PASSWORD, totp)

        positions = obj.position()["data"]

        if positions:
            for pos in positions:
                qty = int(pos["netqty"])

                if qty != 0:
                    obj.placeOrder({
                        "variety": "NORMAL",
                        "tradingsymbol": pos["tradingsymbol"],
                        "symboltoken": pos["symboltoken"],
                        "transactiontype": "SELL" if qty > 0 else "BUY",
                        "exchange": pos["exchange"],
                        "ordertype": "MARKET",
                        "producttype": pos["producttype"],
                        "duration": "DAY",
                        "quantity": abs(qty)
                    })

        return jsonify({"status": "EXIT DONE"})

    except Exception as e:
        return jsonify({"error": str(e)})
        if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
