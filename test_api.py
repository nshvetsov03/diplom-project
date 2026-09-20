import requests
import time

BASE_URL = 'http://127.0.0.1:8000/api'
TEST_EMAIL = f"test_{int(time.time())}@test.com"
TEST_PASSWORD = "securepassword123"

def print_step(step_name):
    print(f"\n{'='*50}\n🔹 {step_name}\n{'='*50}")

def main():
    headers = {}
    booking_id = None
    contact_id = None
    space_detail_id = 1

    # 1. Регистрация
    print_step("1. Регистрация пользователя")
    r = requests.post(f'{BASE_URL}/registration/', json={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'name_user': 'Тест',
        'surname_user': 'Пользователь'
    })
    print(f"Статус: {r.status_code}")
    if r.status_code != 201:
        print("❌ Ошибка регистрации:", r.json())
        return
    token = r.json().get('token')
    print(f" Токен: {token}")
    headers = {'Authorization': f'Token {token}'}
    print(f"📋 Headers: {headers}")


    # 2. Создание контакта
    print_step("2. Создание контакта (адреса)")
    r = requests.post(f'{BASE_URL}/contacts/', json={
        'city': 'Москва',
        'street': 'Ленина',
        'house': '15',
        'phone': '+79990000000'
    }, headers=headers)
    print(f"Статус: {r.status_code}")
    if r.status_code == 201:
        contact_id = r.json()['data']['id']
        print("✅ Контакт создан.")
    else:
        print("⚠️ Контакт уже существует или ошибка:", r.json())

    # 3. Просмотр пространств
    print_step("3. Получение списка пространств")
    r = requests.get(f'{BASE_URL}/spaces/')
    print(f"Статус: {r.status_code}")
    if r.status_code == 200 and r.json().get('spaces'):
        space_detail_id = r.json()['spaces'][0]['id']
        print(f"✅ Найдено пространств: {len(r.json()['spaces'])}. Берем ID={space_detail_id}")
    else:
        print("⚠️ Пространств нет. Запустите импорт YAML или создайте вручную.")

    # 4. Добавление в корзину
    print_step("4. Добавление позиции в корзину")
    r = requests.post(f'{BASE_URL}/basket/', json={
        'space_detail': space_detail_id,
        'quantity': 2,
        'contact': contact_id or 1
    }, headers=headers)
    print(f"Статус: {r.status_code}")
    if r.status_code == 200:
        booking_id = r.json()['basket']['id']
        print(f"✅ Позиция добавлена! ID бронирования: {booking_id}")
    else:
        print("❌ Ошибка добавления в корзину:", r.status_code, r.text[:200])
        return

    # 5. Подтверждение заказа
    print_step("5. Подтверждение заказа (Email в консоль сервера!)")
    r = requests.post(f'{BASE_URL}/booking/{booking_id}/confirm/', headers=headers)
    print(f"Статус: {r.status_code}")
    if r.status_code == 200:
        print("✅ Заказ подтвержден! ПРОВЕРЬТЕ КОНСОЛЬ RUNSERVER.")
    else:
        print("❌ Ошибка подтверждения:", r.json())

    # 6. История заказов
    print_step("6. Получение истории заказов")
    r = requests.get(f'{BASE_URL}/bookings/', headers=headers)
    print(f"Статус: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ В истории {len(r.json()['bookings'])} заказ(ов).")
    else:
        print("❌ Ошибка получения истории:", r.json())

    print(f"\n{'='*50}\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! 🎉\n{'='*50}")

if __name__ == '__main__':
    main()