import os
import random
import threading
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path=""
)

lock = threading.Lock()

game = {
    "running": False,
    "called": [],
    "players": {},
    "winners": []
}


def make_card():
    """
    Create a standard 5x5 Bingo card.

    B: 1-15
    I: 16-30
    N: 31-45
    G: 46-60
    O: 61-75
    """

    columns = [
        random.sample(range(1, 16), 5),
        random.sample(range(16, 31), 5),
        random.sample(range(31, 46), 5),
        random.sample(range(46, 61), 5),
        random.sample(range(61, 76), 5)
    ]

    card = []

    for row in range(5):
        for column in range(5):
            card.append(columns[column][row])

    # Free center
    card[12] = 0

    return card


def check_bingo(card, called):
    called_numbers = set(called)

    marked = set()

    for index, number in enumerate(card):
        if index == 12:
            marked.add(index)
        elif number in called_numbers:
            marked.add(index)

    # Rows
    for row in range(5):
        line = {row * 5 + column for column in range(5)}

        if line.issubset(marked):
            return True

    # Columns
    for column in range(5):
        line = {row * 5 + column for row in range(5)}

        if line.issubset(marked):
            return True

    # Diagonal 1
    if {0, 6, 12, 18, 24}.issubset(marked):
        return True

    # Diagonal 2
    if {4, 8, 12, 16, 20}.issubset(marked):
        return True

    return False


@app.get("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Rudivoller Bingo</title>
        <style>
            body {
                background: #10131a;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px 20px;
            }

            h1 {
                font-size: 36px;
            }

            .status {
                margin-top: 20px;
                padding: 20px;
                background: #1d2430;
                border-radius: 15px;
            }
        </style>
    </head>

    <body>
        <h1>🎯 Rudivoller Bingo</h1>

        <div class="status">
            <h2>Telegram Bingo Server</h2>
            <p>Server is running successfully.</p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Rudivoller Bingo",
        "status": "online"
    })


@app.get("/api/state")
def get_state():
    with lock:
        return jsonify({
            "running": game["running"],
            "called": game["called"],
            "players": len(game["players"]),
            "winners": game["winners"]
        })


@app.post("/api/join")
def join_game():
    data = request.get_json(silent=True) or {}

    user_id = str(data.get("user_id", "")).strip()
    name = str(data.get("name", "Player")).strip()

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


@app.post("/api/admin/stop")
def stop_game():
    with lock:

        game["running"] = False

        return jsonify({
            "ok": True,
            "message": "Bingo game stopped."
        })


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
                "message": "All numbers have been called."
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


@app.post("/api/claim")
def claim_bingo():
    data = request.get_json(silent=True) or {}

    user_id = str(data.get("user_id", "")).strip()

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

        if check_bingo(player["card"], game["called"]):

            if user_id not in game["winners"]:
                game["winners"].append(user_id)

            return jsonify({
                "ok": True,
                "bingo": True,
                "message": f"🎉 BINGO! Congratulations {player['name']}!"
            })

        return jsonify({
            "ok": True,
            "bingo": False,
            "message": "No Bingo yet."
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port
    )
