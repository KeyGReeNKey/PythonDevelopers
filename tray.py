# tray.py
import pystray
from PIL import Image, ImageDraw
import threading
import tkinter as tk

def create_icon_image():
    """Создаём простую иконку программно (круг с буквой R)"""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (40, 40, 40))
    draw = ImageDraw.Draw(image)
    # Рисуем круг
    draw.ellipse((4, 4, width-4, height-4), fill=(70, 130, 200), outline=(255,255,255), width=2)
    # Рисуем букву "R"
    draw.text((20, 14), "R", fill="white", font=None)  # можно указать шрифт
    return image

class TrayIcon:
    def __init__(self, app_window):
        self.app_window = app_window
        self.icon = pystray.Icon("life_rpg", create_icon_image(), "Life RPG")
        # Меню трея
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Показать окно", self.show_window),
            pystray.MenuItem("Выход", self.quit_app)
        )
        # Запускаем иконку в отдельном потоке
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def show_window(self, icon=None, item=None):
        # Восстанавливаем окно
        self.app_window.deiconify()
        self.app_window.lift()
        self.app_window.focus_force()

    def quit_app(self, icon=None, item=None):
        self.icon.stop()
        self.app_window.quit()  # завершаем Tkinter
