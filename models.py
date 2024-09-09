from flask_login import UserMixin
from extensions import db

# Модель пользователя <Response [200]>
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    robot_count = db.Column(db.Integer, default=0)  # Количество роботов