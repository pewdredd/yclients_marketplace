from flask import redirect, url_for, flash, request, current_app
from models import User
from extensions import db
from payment import send_payment_webhook

import os
import requests
import base64
import hmac
import hashlib
import json


PARTNER_TOKEN = os.getenv('PARTNER_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

# активации интеграции после регистрации/авторизации
def activate_integration(salon_ids):
    if salon_ids:
        # Отправляем запрос на активацию интеграции в API YCLIENTS
        response = activate_integration_for_salon(salon_ids)
        if response['status'] == 'success':
            return "Интеграция успешно активирована", 200
        else:
            return f"Ошибка активации: {response['message']}", 400
    else:
        return "Ошибка: salon_id не найден", 400

# Функция отправки API-запроса для активации интеграции в YCLIENTS
def activate_integration_for_salon(salon_ids):
    url = "https://api.yclients.com/marketplace/partner/callback"
    headers = {
        "Authorization": f"Bearer {PARTNER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.api.v2+json"
    }
    result = {}
    
    for salon_id in salon_ids:
        data = {
        "salon_id": salon_id,
        "application_id": 10756,
        "webhook_urls": ["https://ec58-2-134-110-77.ngrok-free.app"]
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            result["status"] = "success"
        else:
            result["status"] = "error"
            result["message"] = response.text

    return result



def verify_signature(user_data_decoded, user_data_sign):
    # Функция для проверки подписи HMAC-SHA256
    calculated_sign = hmac.new(
        PARTNER_TOKEN.encode(), 
        user_data_decoded.encode(), 
        hashlib.sha256
    ).hexdigest()

    return calculated_sign == user_data_sign


def auto_register_user():
    # Функция для автоматической регистрации пользователя
    # Получаем параметры из запроса
    user_data_encoded = request.args.get('user_data')
    user_data_sign = request.args.get('user_data_sign')

    # Если данных нет, возвращаем None
    if not user_data_encoded or not user_data_sign:
        return None

    # Декодируем base64-строку
    try:
        user_data_decoded = base64.b64decode(user_data_encoded).decode('utf-8')
        user_data = json.loads(user_data_decoded)
    except (ValueError, json.JSONDecodeError):
        flash('Некорректные данные для регистрации!', 'danger')
        return None

    # Проверяем подпись
    if not verify_signature(user_data_decoded, user_data_sign):
        flash('Некорректная подпись данных!', 'danger')
        return None

    # Извлекаем данные пользователя
    username = user_data.get('name') 
    email = user_data.get('email')
    phone = user_data.get('phone')
    password = 12345678  # можно задать случайный пароль или другой механизм
    print(username)

    # Проверяем, существует ли уже пользователь с таким username
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return redirect(url_for('login'))

    # Создаем пользователя и сохраняем в базу данных
    user = current_app.create_user(username, password)

    flash('Пользователь успешно зарегистрирован через интеграцию!', 'success')
    return user