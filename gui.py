# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class App:
    def __init__(self, game):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Life RPG")
        self.root.geometry("900x600")

        # Верхняя панель статистики
        self.stats_frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        self.stats_label = tk.Label(self.stats_frame, font=('Arial', 12))
        self.stats_label.pack(pady=5)

        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка "Квесты"
        self.quests_tab = tk.Frame(self.notebook)
        self.notebook.add(self.quests_tab, text="Квесты")
        self.build_quests_tab()

        # Вкладка "Наказания"
        self.penalties_tab = tk.Frame(self.notebook)
        self.notebook.add(self.penalties_tab, text="Наказания")
        self.build_penalties_tab()

        # Вкладка "История"
        self.history_tab = tk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="История")
        self.build_history_tab()

        self.update_all()
        self.root.mainloop()

    def update_stats(self):
        p = self.game.player
        text = (f"Уровень: {p['level']}  |  Опыт: {p['experience']}  |  "
                f"Сила: {p['strength']}  |  Интеллект: {p['intelligence']}  |  "
                f"Энергия: {p['energy']}")
        self.stats_label.config(text=text)

    def update_all(self):
        self.game.refresh_player()
        self.update_stats()
        self.update_quests_list()
        self.update_penalties_list()
        self.update_history_list()

    # ---- Квесты ----
    def build_quests_tab(self):
        # Кнопка добавления
        btn_add = tk.Button(self.quests_tab, text="Добавить квест",
                            command=self.add_quest_dialog)
        btn_add.pack(pady=5)

        # Таблица квестов
        columns = ('ID','Название','Тип','Сложность','Награда (опыт)','Штраф (опыт)')
        self.quests_tree = ttk.Treeview(self.quests_tab, columns=columns, show='headings')
        for col in columns:
            self.quests_tree.heading(col, text=col)
        self.quests_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Кнопки действий
        btn_frame = tk.Frame(self.quests_tab)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Выполнить", command=self.complete_quest).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Провалить", command=self.fail_quest).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=self.update_quests_list).pack(side=tk.LEFT, padx=5)

    def update_quests_list(self):
        for item in self.quests_tree.get_children():
            self.quests_tree.delete(item)
        quests = self.game.db.get_active_quests()
        for q in quests:
            self.quests_tree.insert('', tk.END, values=(
                q['id'], q['title'], q['type'], q['difficulty'],
                q['reward_exp'], q['penalty_exp']
            ))

    def add_quest_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый квест")
        dialog.geometry("400x400")
        fields = {}
        labels = [
            ('Название', 'title'),
            ('Описание', 'desc'),
            ('Тип (body/brain)', 'type'),
            ('Сложность (1-10)', 'difficulty'),
            ('Награда опыт', 'reward_exp'),
            ('Награда сила', 'reward_strength'),
            ('Награда интеллект', 'reward_intelligence'),
            ('Штраф опыт', 'penalty_exp'),
            ('Штраф энергия', 'penalty_energy')
        ]
        for i, (label, key) in enumerate(labels):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=2)
            fields[key] = entry

        def save():
            try:
                data = {k: int(v.get()) if k not in ('title','desc','type') else v.get()
                        for k, v in fields.items()}
                # базовая валидация
                if data['type'] not in ('body','brain'):
                    messagebox.showerror("Ошибка", "Тип должен быть 'body' или 'brain'")
                    return
                self.game.db.add_quest(
                    data['title'], data['desc'], data['type'], data['difficulty'],
                    data['reward_exp'], data['reward_strength'], data['reward_intelligence'],
                    data['penalty_exp'], data['penalty_energy']
                )
                self.update_all()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные числа")

        tk.Button(dialog, text="Сохранить", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def get_selected_quest_id(self):
        selection = self.quests_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите квест")
            return None
        values = self.quests_tree.item(selection[0])['values']
        return int(values[0])

    def complete_quest(self):
        qid = self.get_selected_quest_id()
        if qid is None:
            return
        success, msg = self.game.complete_quest(qid)
        if success:
            if msg:  # level up
                messagebox.showinfo("Уровень повышен!", f"Поздравляем! Вы достигли {self.game.player['level']} уровня!")
            self.update_all()
        else:
            messagebox.showerror("Ошибка", msg)

    def fail_quest(self):
        qid = self.get_selected_quest_id()
        if qid is None:
            return
        success, msg = self.game.fail_quest(qid)
        if success:
            self.update_all()
            messagebox.showinfo("Штраф", msg)
        else:
            messagebox.showerror("Ошибка", msg)

    # ---- Наказания ----
    def build_penalties_tab(self):
        btn_add = tk.Button(self.penalties_tab, text="Добавить наказание",
                            command=self.add_penalty_dialog)
        btn_add.pack(pady=5)

        columns = ('ID','Название','Штраф опыт','Штраф энергия')
        self.penalties_tree = ttk.Treeview(self.penalties_tab, columns=columns, show='headings')
        for col in columns:
            self.penalties_tree.heading(col, text=col)
        self.penalties_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self.penalties_tab)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Применить", command=self.apply_penalty).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=self.update_penalties_list).pack(side=tk.LEFT, padx=5)

    def update_penalties_list(self):
        for item in self.penalties_tree.get_children():
            self.penalties_tree.delete(item)
        penalties = self.game.db.get_penalties()
        for p in penalties:
            self.penalties_tree.insert('', tk.END, values=(
                p['id'], p['name'], p['penalty_exp'], p['penalty_energy']
            ))

    def add_penalty_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новое наказание")
        dialog.geometry("300x250")
        fields = {}
        labels = [
            ('Название', 'name'),
            ('Описание', 'desc'),
            ('Штраф опыт', 'penalty_exp'),
            ('Штраф энергия', 'penalty_energy')
        ]
        for i, (label, key) in enumerate(labels):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=2)
            fields[key] = entry

        def save():
            try:
                data = {k: int(v.get()) if k.startswith('penalty_') else v.get()
                        for k, v in fields.items()}
                self.game.db.add_penalty(data['name'], data['desc'],
                                         data['penalty_exp'], data['penalty_energy'])
                self.update_all()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные числа")

        tk.Button(dialog, text="Сохранить", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def get_selected_penalty_id(self):
        selection = self.penalties_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите наказание")
            return None
        values = self.penalties_tree.item(selection[0])['values']
        return int(values[0])

    def apply_penalty(self):
        pid = self.get_selected_penalty_id()
        if pid is None:
            return
        success, msg = self.game.apply_penalty(pid)
        if success:
            self.update_all()
            messagebox.showinfo("Наказание", msg)
        else:
            messagebox.showerror("Ошибка", msg)

    # ---- История ----
    def build_history_tab(self):
        columns = ('Время', 'Действие', 'Детали')
        self.history_tree = ttk.Treeview(self.history_tab, columns=columns, show='headings')
        for col in columns:
            self.history_tree.heading(col, text=col)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self.history_tab)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Обновить", command=self.update_history_list).pack()

    def update_history_list(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        history = self.game.db.get_history(limit=100)
        for ts, action, details in history:
            self.history_tree.insert('', tk.END, values=(ts, action, details))
