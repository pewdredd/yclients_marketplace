import os
import requests
import json
import datetime

from flask import jsonify
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

PARTNER_TOKEN = os.getenv('PARTNER_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

def send_payment_webhook(salon_id):
    # Данные, которые вы хотите отправить
    webhook_url = "https://api.yclients.com/marketplace/partner/payment"
    bearer_token = PARTNER_TOKEN
    
    # Тело запроса
    data = {
        "salon_id": salon_id,               # идентификатор филиала
        "application_id": APPLICATION_ID,          # идентификатор приложения
        "payment_sum": 100.00,            # суммa платежа
        "currency_iso": "RUB",             # валютa платежа
        "payment_date": "2024-09-07 10:10:00",
        "period_from": "2024-09-07 11:10:00",
        "period_to": "2024-10-07 11:10:00"    
        }

    # Заголовки для авторизации
    headers = {
        'Authorization': f'Bearer {PARTNER_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.api.v2+json'
    }

    try:
        # Выполняем POST-запрос "id":956415
        response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
        print(response.content.data)

        # Проверяем статус ответа
        if response.status_code == 200:
            
            content = response.content  
            content_str = content.decode('utf-8')
            data = json.loads(content_str)
            id_value = data['data']['id'] # Достаем значение id

            print(f'Пэймент id: {id_value}')  # Выводим значение id

            print("Webhook sent successfully")
            print("Response дата:", response.data)
            return jsonify({"success": True, "message": "Webhook sent successfully"}), 200
        else:
            print(f"Error sending webhook: {response.json()}")
            return jsonify({"success": False, "message": response.json()}), response.status_code

    except Exception as e:
        print(f"Error sending webhook: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    

def refund_request(payment_id):
    url = f"https://api.yclients.com/marketplace/partner/payment/refund/{payment_id}"  

    # Заголовки авторизации
    headers  = {
        "Authorization": f"Bearer {PARTNER_TOKEN}",  # Замените на ваш токен
        "Content-Type": "application/json",
        "Accept": "application/vnd.api.v2+json"
    }

    # Выполнение запроса
    response = requests.post(url, headers=headers)

    # Обработка ответа
    if response.status_code == 200:
        print('Возврат зафиксирован')
        return 'Response:', response.json
    elif response.status_code == 401:
        return 'Ошибка: Unauthorized'
    else:
        return f'Ошибка: {response.status_code}'
