from dotenv import load_dotenv
import os

os.environ.pop('SQLALCHEMY_URL')
URL = os.getenv('SQLALCHEMY_URL')
print("Raw env URL:", os.getenv('SQLALCHEMY_URL'))  # Отладочный вывод
print("Database URL:", URL)  # Отладочный вывод

for _ in os.environ:
    print(_)
URL = os.getenv('SQLALCHEMY_URL')
print("Raw env URL:", os.getenv('SQLALCHEMY_URL'))  # Отладочный вывод
print("Database URL:", URL)  # Отладочный вывод