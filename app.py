from flask import Flask, jsonify, request
import os
import time

app = Flask(__name__)

# ===== EXIT SAFETY LOCK =====
last_exit_time = 0
EXIT_COOLDOWN = 180   # 3 minutes protection


# ===============================
# HEALTH CHECK ROUTE
# ===============================
@app.route("/")
def home():
    return "Server Live ✅"


# ===============================
# AUTO EXIT WEBHOOK
# ===============================
@app.route("/exit", methods=["POST"])
def exit_trade():
    global last_exit_time

    now = time.time()

    # ---- Duplicate Exit Protection ----
    if now - last_exit_time < EXIT_COOLDOWN:
        return jsonify({"status": "EXIT BLOCKED (Cooldown Active)"})

    try:
        from SmartApi import SmartConnect
        import pyotp

        # ---- ENV VARIABLES ----
        API_KEY = os.getenv("API_KEY")
        CLIENT_CODE = os.getenv("CLIENT_CODE")
        PASSWORD = os.getenv("PASSWORD")
        TOTP_KEY = os.getenv("TOTP_KEY")

        # ---- LOGIN TO ANGEL ----
        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_KEY).now()

        session = obj.generateSession(
            CLIENT_CODE,
            PASSWORD,
            totp
        )

        # ---- FETCH POSITIONS ----
        positions = obj.position().get("data", [])

        exited = False

        for pos in positions:

            # Angel sometimes gives qty differently
            netqty = int(pos.get("netqty", 0))
            buyqty = int(pos.get("buyqty", 0))
            sellqty = int(pos.get("sellqty", 0))

            actual_qty = netqty if netqty != 0 else (buyqty - sellqty)

            if actual_qty != 0:

                transaction = "SELL" if actual_qty > 0 else "BUY"

                orderparams = {
    "variety": "NORMAL",
    "tradingsymbol": pos["tradingsymbol"],
    "symboltoken": pos["symboltoken"],
    "transactiontype": transaction,
    "exchange": pos["exchange"],
    "ordertype": "MARKET",
    "producttype": "INTRADAY",
    "duration": "DAY",
    "quantity": abs(actual_qty)
}
                    "duration": "DAY",
                    "quantity": abs(actual_qty)
                }

                obj.placeOrder(orderparams)
                exited = True

        # ---- Activate Cooldown ----
        last_exit_time = now

        if exited:
            return jsonify({"status": "EXIT EXECUTED ✅"})
        else:
            return jsonify({"status": "NO POSITION FOUND"})

    except Exception as e:
        return jsonify({"error": str(e)})
