from database import Database

class GameRepository:
    def __init__(self):
        self.db = Database.get_instance()
    
    def save_score(self, user_id: str, score: int, multiplier: int, first_name: str = None, photo_url: str = None) -> tuple:
        """Сохраняет или обновляет счет и данные игрока"""
        conn = self.db.get_connection()
        if not conn:
            raise Exception("Нет подключения к БД")
            
        with conn.cursor() as cursor:
            query = """
                INSERT INTO scores (user_id, score, multiplier, first_name, photo_url) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    score = %s,
                    multiplier = %s,
                    first_name = COALESCE(%s, scores.first_name),
                    photo_url = COALESCE(%s, scores.photo_url),
                    last_updated = CURRENT_TIMESTAMP
                RETURNING user_id, score, multiplier, first_name, photo_url
            """
            cursor.execute(query, (
                str(user_id), score, multiplier, first_name, photo_url,
                score, multiplier, first_name, photo_url
            ))
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
    
    def get_leaderboard(self, limit: int = None) -> list:
        """Получает таблицу лидеров"""
        conn = self.db.get_connection()
        if not conn:
            return []
            
        with conn.cursor() as cursor:
            query = """
                SELECT user_id, score, multiplier, first_name, photo_url 
                FROM scores 
                ORDER BY score DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            return cursor.fetchall() 