import random
import threading


lock = threading.Lock()


game = {
    "running": False,
    "called": [],
    "players": {},
    "winners": []
}


def make_card():
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
        line = {
            row * 5 + column
            for column in range(5)
        }

        if line.issubset(marked):
            return True

    # Columns
    for column in range(5):
        line = {
            row * 5 + column
            for row in range(5)
        }

        if line.issubset(marked):
            return True

    # Diagonal 1
    if {0, 6, 12, 18, 24}.issubset(marked):
        return True

    # Diagonal 2
    if {4, 8, 12, 16, 20}.issubset(marked):
        return True

    return False
