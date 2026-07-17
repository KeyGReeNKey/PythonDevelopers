
# main.py
from db import Database
from game import Game
from gui import App

if __name__ == "__main__":
    db = Database()
    game = Game(db)
    app = App(game)
    db.close()
