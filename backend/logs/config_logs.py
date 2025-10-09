import logging
from logging.handlers import RotatingFileHandler
import os

# Создаём директорию для логов, если она не существует
os.makedirs("logs", exist_ok=True)

def setup_logging():
    """
    Настраивает логирование для приложения.
    Использует ротацию файлов для управления размером логов и их количеством.
    """
    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования на INFO

    # Проверяем, есть ли уже обработчик RotatingFileHandler
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        # Создаём обработчик с ротацией файлов
        handler = RotatingFileHandler(
            "logs/logs/logs.log",  # Путь к файлу логов
            maxBytes=5_000_000,  # Максимальный размер файла (5 МБ)
            backupCount=5,  # Количество резервных копий
            encoding="utf-8"  # Кодировка файла
        )
        # Формат логов
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)  # Применяем формат к обработчику
        root_logger.addHandler(handler)  # Добавляем обработчик к корневому логгеру

        # Устанавливаем уровень логирования для сторонних библиотек
        logging.getLogger("httpx").setLevel(logging.WARNING)  # Снижаем уровень логов для httpx
        logging.getLogger("httpcore").setLevel(logging.WARNING)  # Снижаем уровень логов для httpcore
