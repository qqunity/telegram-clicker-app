import os
from database import Database
from datetime import datetime
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Migrations:
    def __init__(self):
        self.db = Database.get_instance()
        logger.info("Инициализация системы миграций")
        self.init_migrations_table()
    
    def init_migrations_table(self):
        """Создает таблицу для отслеживания миграций"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("Не удалось получить подключение к БД")
            return
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id SERIAL PRIMARY KEY,
                        version TEXT NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Таблица миграций успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы миграций: {e}")
    
    def get_applied_migrations(self) -> set:
        """Получает список примененных миграций"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("Не удалось получить подключение к БД при получении списка миграций")
            return set()
            
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version FROM migrations")
                migrations = {row[0] for row in cursor.fetchall()}
                logger.info(f"Получен список применённых миграций: {migrations}")
                return migrations
        except Exception as e:
            logger.error(f"Ошибка при получении списка миграций: {e}")
            return set()
    
    def apply_migration(self, version: str, sql: str):
        """Применяет миграцию"""
        conn = self.db.get_connection()
        if not conn:
            logger.error(f"Не удалось получить подключение к БД при применении миграции {version}")
            return
            
        try:
            with conn.cursor() as cursor:
                logger.info(f"Начало применения миграции {version}")
                logger.debug(f"SQL миграции {version}: {sql}")
                
                # Выполняем SQL миграции
                cursor.execute(sql)
                
                # Записываем информацию о выполненной миграции
                cursor.execute(
                    "INSERT INTO migrations (version) VALUES (%s)",
                    (version,)
                )
                conn.commit()
                logger.info(f"✅ Миграция {version} успешно применена")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка при применении миграции {version}: {e}")
    
    def run_migrations(self):
        """Запускает все непримененные миграции"""
        logger.info("Начало проверки миграций")
        applied = self.get_applied_migrations()
        
        # Список всех миграций
        migrations = [
            ("001_initial_schema", """
                CREATE TABLE IF NOT EXISTS scores (
                    user_id TEXT PRIMARY KEY,
                    score INTEGER DEFAULT 0,
                    multiplier INTEGER DEFAULT 1,
                    first_name TEXT,
                    photo_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            
            # Будущие миграции будут добавляться сюда
            # ("002_some_changes", """
            #     ALTER TABLE scores ...
            # """),
        ]
        
        # Применяем только новые миграции
        pending_migrations = [m for m, _ in migrations if m not in applied]
        if not pending_migrations:
            logger.info("✨ Все миграции уже применены")
            return

        logger.info(f"Найдены новые миграции для применения: {pending_migrations}")
        
        for version, sql in migrations:
            if version not in applied:
                logger.info(f"⚙️ Применяем миграцию {version}...")
                self.apply_migration(version, sql)
        
        logger.info("✨ Все миграции успешно применены")

def run_migrations():
    """Функция для запуска миграций"""
    logger.info("=== Запуск системы миграций ===")
    migrations = Migrations()
    migrations.run_migrations()
    logger.info("=== Система миграций завершила работу ===")

if __name__ == "__main__":
    run_migrations() 