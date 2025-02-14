from database import Database

class GameRepository:
    def __init__(self):
        self.db = Database.get_instance()
    
    def save_score(self, user_id: str, score: int, multiplier: int) -> tuple:
        """Сохраняет или обновляет счет игрока"""
        conn = self.db.get_connection()
        if not conn:
            raise Exception("Нет подключения к БД")
            
        with conn.cursor() as cursor:
            query = """
                INSERT INTO scores (user_id, score, multiplier) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    score = %s,
                    multiplier = %s
                RETURNING user_id, score, multiplier
            """
            cursor.execute(query, (str(user_id), score, multiplier, score, multiplier))
            result = cursor.fetchone()
            conn.commit()
            return result
    
    def get_user_score(self, user_id: str) -> tuple:
        """Получает счет игрока"""
        conn = self.db.get_connection()
        if not conn:
            return None
            
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT score, multiplier FROM scores WHERE user_id = %s",
                (str(user_id),)
            )
            return cursor.fetchone()
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """Получает таблицу лидеров"""
        conn = self.db.get_connection()
        if not conn:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, score, multiplier FROM scores ORDER BY score DESC LIMIT %s",
                (limit,)
            )
            return cursor.fetchall() 