# db.py
import sqlite3
from config import DB_PATH, PLAYER_NAME
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._init_player()
        self._migrate_quests()

    def _create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY,
                name TEXT,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                strength INTEGER DEFAULT 10,
                intelligence INTEGER DEFAULT 10,
                energy INTEGER DEFAULT 100
            );
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                type TEXT CHECK(type IN ('body', 'brain')),
                difficulty INTEGER,
                reward_exp INTEGER,
                reward_strength INTEGER DEFAULT 0,
                reward_intelligence INTEGER DEFAULT 0,
                penalty_exp INTEGER DEFAULT 0,
                penalty_energy INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                recurring INTEGER DEFAULT 0,
                recurrence_rule TEXT DEFAULT '',
                last_completed TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS penalties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                penalty_exp INTEGER DEFAULT 0,
                penalty_energy INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT,
                quest_id INTEGER,
                penalty_id INTEGER,
                details TEXT
            );
        """)
        self.conn.commit()

    def _init_player(self):
        self.cursor.execute("SELECT * FROM player LIMIT 1")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO player (name) VALUES (?)", (PLAYER_NAME,)
            )
            self.conn.commit()

    def _migrate_quests(self):
        self.cursor.execute("PRAGMA table_info(quests)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'recurring' not in columns:
            self.cursor.execute("ALTER TABLE quests ADD COLUMN recurring INTEGER DEFAULT 0")
        if 'recurrence_rule' not in columns:
            self.cursor.execute("ALTER TABLE quests ADD COLUMN recurrence_rule TEXT DEFAULT ''")
        if 'last_completed' not in columns:
            self.cursor.execute("ALTER TABLE quests ADD COLUMN last_completed TEXT DEFAULT ''")
        self.conn.commit()

    def get_player(self):
        self.cursor.execute("SELECT * FROM player LIMIT 1")
        row = self.cursor.fetchone()
        return {
            'id': row[0], 'name': row[1], 'level': row[2],
            'experience': row[3], 'strength': row[4],
            'intelligence': row[5], 'energy': row[6]
        }

    def update_player(self, **kwargs):
        set_clause = ', '.join([f"{k}=?" for k in kwargs])
        values = list(kwargs.values())
        self.cursor.execute(f"UPDATE player SET {set_clause} WHERE id=1", values)
        self.conn.commit()

    def get_active_quests(self):
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute("SELECT * FROM quests WHERE is_active=1")
        all_quests = self.cursor.fetchall()
        result = []
        for row in all_quests:
            q = dict(zip(['id','title','description','type','difficulty',
                          'reward_exp','reward_strength','reward_intelligence',
                          'penalty_exp','penalty_energy','is_active',
                          'recurring','recurrence_rule','last_completed'], row))
            if q['recurring']:
                if self._is_quest_available_today(q):
                    result.append(q)
            else:
                result.append(q)
        return result

    def _is_quest_available_today(self, quest):
        today = datetime.now().date()
        last = datetime.strptime(quest['last_completed'], '%Y-%m-%d').date() if quest['last_completed'] else None
        rule = quest['recurrence_rule']
        if not rule:
            rule = 'daily'
        if rule == 'daily':
            return last != today
        elif rule.startswith('weekly:'):
            days = [int(x.strip()) for x in rule.split(':')[1].split(',') if x.strip().isdigit()]
            if not days:
                return False
            if today.isoweekday() in days:
                return last != today
            else:
                return False
        elif rule.startswith('monthly:'):
            day_num = int(rule.split(':')[1])
            if day_num == today.day:
                return last != today
            else:
                return False
        else:
            return False

    def add_quest(self, title, desc, qtype, difficulty, reward_exp,
                  reward_strength=0, reward_intelligence=0,
                  penalty_exp=0, penalty_energy=0,
                  recurring=0, recurrence_rule=''):
        self.cursor.execute("""
            INSERT INTO quests
            (title, description, type, difficulty, reward_exp,
             reward_strength, reward_intelligence, penalty_exp, penalty_energy,
             recurring, recurrence_rule)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (title, desc, qtype, difficulty, reward_exp,
              reward_strength, reward_intelligence, penalty_exp, penalty_energy,
              recurring, recurrence_rule))
        self.conn.commit()

    def deactivate_quest(self, quest_id):
        self.cursor.execute("SELECT recurring FROM quests WHERE id=?", (quest_id,))
        row = self.cursor.fetchone()
        if row and row[0] == 1:
            today = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute("UPDATE quests SET last_completed=? WHERE id=?", (today, quest_id))
        else:
            self.cursor.execute("UPDATE quests SET is_active=0 WHERE id=?", (quest_id,))
        self.conn.commit()

    def get_quest(self, quest_id):
        self.cursor.execute("SELECT * FROM quests WHERE id=?", (quest_id,))
        row = self.cursor.fetchone()
        if row:
            return dict(zip(['id','title','description','type','difficulty',
                             'reward_exp','reward_strength','reward_intelligence',
                             'penalty_exp','penalty_energy','is_active',
                             'recurring','recurrence_rule','last_completed'], row))
        return None

    def delete_quest(self, quest_id):
        """Полностью удалить квест"""
        self.cursor.execute("DELETE FROM quests WHERE id=?", (quest_id,))
        self.conn.commit()

    def get_penalties(self):
        self.cursor.execute("SELECT * FROM penalties")
        return [dict(zip(['id','name','description','penalty_exp','penalty_energy'], row))
                for row in self.cursor.fetchall()]

    def add_penalty(self, name, desc, penalty_exp=0, penalty_energy=0):
        self.cursor.execute("""
            INSERT INTO penalties (name, description, penalty_exp, penalty_energy)
            VALUES (?,?,?,?)
        """, (name, desc, penalty_exp, penalty_energy))
        self.conn.commit()

    def get_penalty(self, penalty_id):
        self.cursor.execute("SELECT * FROM penalties WHERE id=?", (penalty_id,))
        row = self.cursor.fetchone()
        if row:
            return dict(zip(['id','name','description','penalty_exp','penalty_energy'], row))
        return None

    def add_history(self, action_type, quest_id=None, penalty_id=None, details=""):
        self.cursor.execute("""
            INSERT INTO history (action_type, quest_id, penalty_id, details)
            VALUES (?,?,?,?)
        """, (action_type, quest_id, penalty_id, details))
        self.conn.commit()

    def get_history(self, limit=50):
        self.cursor.execute("""
            SELECT timestamp, action_type, details
            FROM history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
