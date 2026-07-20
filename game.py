# game.py
from config import EXP_PER_LEVEL

class Game:
    def __init__(self, db):
        self.db = db
        self.player = self.db.get_player()

    def _save_player(self):
        self.db.update_player(**self.player)

    def complete_quest(self, quest_id):
        quest = self.db.get_quest(quest_id)
        if not quest:
            return False, "Квест не найден"
        if not quest['is_active']:
            return False, "Квест уже неактивен"

        # Начисляем награду
        self.player['experience'] += quest['reward_exp']
        self.player['strength'] += quest['reward_strength']
        self.player['intelligence'] += quest['reward_intelligence']

        # Проверка повышения уровня
        level_up = False
        while self.player['experience'] >= self.player['level'] * EXP_PER_LEVEL:
            self.player['level'] += 1
            level_up = True

        # Для повторяющихся – обновляем last_completed, для обычных – деактивируем
        self.db.deactivate_quest(quest_id)

        self.db.add_history('quest_complete', quest_id=quest_id,
                            details=f"{quest['title']} выполнен")
        self._save_player()
        return True, level_up

    def fail_quest(self, quest_id):
        quest = self.db.get_quest(quest_id)
        if not quest:
            return False, "Квест не найден"
        if not quest['is_active']:
            return False, "Квест уже неактивен"

        # Применяем штраф
        self.player['experience'] = max(0, self.player['experience'] - quest['penalty_exp'])
        self.player['energy'] = max(0, self.player['energy'] - quest['penalty_energy'])

        # Для повторяющихся – обновляем last_completed (чтобы нельзя было провалить дважды за день)
        # Для обычных – деактивируем
        self.db.deactivate_quest(quest_id)

        self.db.add_history('quest_fail', quest_id=quest_id,
                            details=f"{quest['title']} провален")
        self._save_player()
        return True, "Штраф применён"

    def apply_penalty(self, penalty_id):
        penalty = self.db.get_penalty(penalty_id)
        if not penalty:
            return False, "Наказание не найдено"

        self.player['experience'] = max(0, self.player['experience'] - penalty['penalty_exp'])
        self.player['energy'] = max(0, self.player['energy'] - penalty['penalty_energy'])

        self.db.add_history('penalty_applied', penalty_id=penalty_id,
                            details=f"Применено наказание: {penalty['name']}")
        self._save_player()
        return True, "Наказание применено"

    def refresh_player(self):
        self.player = self.db.get_player()
