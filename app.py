from flask import Flask, jsonify, request
import os
import time

app = Flask(__name__)

# ===== EXIT SAFETY LOCK =====
last_exit_time = 0
EXIT_COOLDOWN = 180   # seconds (3 minutes)

# ---- HEALTH CHECK ----
@app.route("/")
def home():
    return "Server Live ✅"


# ---- EXIT WEBHOOK ----
@app.route("/exit", methods=["POST"])
def exit_trade():
    global last_exit_time

    now = time.time()

    # ✅ Prevent duplicate exits
    if now - last_exit_time < EXIT_COOLDOWN:
        return jsonify({"status": "EXIT BLOCKED (Cooldown Active)"})

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

        # ✅ Activate lock
        last_exit_time = now

        return jsonify({"status": "EXIT EXECUTED ✅"})

    except Exception as e:
        return jsonify({"error": str(e)})
