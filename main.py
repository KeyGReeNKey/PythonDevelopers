# main.py
import sys
from PyQt5.QtWidgets import QApplication
from db import Database
from game import Game
from gui_qt import App

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    game = Game(db)
    window = App(game)
    window.show()
    sys.exit(app.exec_())
