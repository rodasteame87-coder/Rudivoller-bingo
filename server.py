import os
import random
from flask import Flask, jsonify, request, send_from_directory

from game_state import game, lock, make_card, check_bingo
from bot import start_bot_thread


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path=""
)


# Start Telegram bot
start_bot_thread()


# ==================================================
# MINI APP
# ==================================================

@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Rudivoller Bingo",
        "status": "online"
    })


# ==================================================
# GAME STATE
# ==================================================

@app.get("/api/state")
def get_state():

    with lock:
        return jsonify({
            "running": game["running"],
            "called": list(game["called"]),
            "players": len(game["players"]),
            "winners": list(game["winners"])
        })


# ==================================================
# JOIN GAME
# ==================================================

@app.post("/api/join")
def join_game():

    data = request.get_json(silent=True) or {}

    user_id = str(
        data.get("user_id", "")
    ).strip()

    name = str(
        data.get("name", "Player")
    ).strip()

    if not user_id:
        return jsonify({
            "ok": False,
            "error": "user_id is required"
        }), 400

    with lock:

        if user_id not in game["players"]:

            game["players"][user_id] = {
                "name": name,
                "card": make_card()
            }

        player = game["players"][user_id]

        return jsonify({
            "ok": True,
            "name": player["name"],
            "card": player["card"]
        })


# ==================================================
# ADMIN START GAME
# ==================================================

@app.post("/api/admin/start")
def start_game():

    with lock:

        game["running"] = True
        game["called"] = []
        game["winners"] = []

        return jsonify({
            "ok": True,
            "message": "Bingo game started."
        })


# ==================================================
# ADMIN STOP GAME
# ==================================================

@app.post("/api/admin/stop")
def stop_game():

    with lock:

        game["running"] = False

        return jsonify({
            "ok": True,
            "message": "Bingo game stopped."
        })


# ==================================================
# ADMIN CALL NUMBER
# ==================================================

@app.post("/api/admin/call")
def call_number():

    with lock:

        if not game["running"]:
            return jsonify({
                "ok": False,
                "error": "Game is not running."
            }), 400

        available = [
            number
            for number in range(1, 76)
            if number not in game["called"]
        ]

        if not available:

            game["running"] = False

            return jsonify({
                "ok": True,
                "finished": True,
                "message": "All 75 numbers have been called."
            })

        number = random.choice(available)

        game["called"].append(number)

        if number <= 15:
            letter = "B"
        elif number <= 30:
            letter = "I"
        elif number <= 45:
            letter = "N"
        elif number <= 60:
            letter = "G"
        else:
            letter = "O"

        return jsonify({
            "ok": True,
            "number": number,
            "letter": letter,
            "display": f"{letter}-{number}"
        })


# ==================================================
# BINGO CLAIM
# ==================================================

@app.post("/api/claim")
def claim_bingo():

    data = request.get_json(silent=True) or {}

    user_id = str(
        data.get("user_id", "")
    ).strip()

    if not user_id:
        return jsonify({
            "ok": False,
            "error": "user_id is required"
        }), 400

    with lock:

        player = game["players"].get(user_id)

        if not player:
            return jsonify({
                "ok": False,
                "message": "Player has not joined the game."
            }), 400

        if not game["running"]:
            return jsonify({
                "ok": False,
                "message": "The game is not running."
            }), 400

        if check_bingo(
            player["card"],
            game["called"]
        ):

            if user_id not in game["winners"]:
                game["winners"].append(user_id)

            return jsonify({
                "ok": True,
                "bingo": True,
                "message": (
                    f"🎉 BINGO! "
                    f"Congratulations {player['name']}!"
                )
            })

        return jsonify({
            "ok": True,
            "bingo": False,
            "message": "No Bingo yet."
        })
        @app.get("/api/debug")
def debug():
    with lock:
        return jsonify({
            "players": game["players"],
            "player_count": len(game["players"]),
            "running": game["running"],
            "called": game["called"]
        })


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
