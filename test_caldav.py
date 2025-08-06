#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест подключения к Яндекс.Календарю через CalDAV
"""

import caldav
from datetime import datetime

def test_caldav_connection():
    """Тест подключения CalDAV"""
    print("=== ТЕСТ ПОДКЛЮЧЕНИЯ К ЯНДЕКС.КАЛЕНДАРЮ ===")
    print()
    
    # Тестовые данные (замените на реальные)
    username = "alexesley01@yandex.ru"  # Ваш email
    token = "y0_AgAAAABqcurqAAxxxxx"  # OAuth токен (первые символы)
    
    try:
        print(f"Подключаемся к CalDAV...")
        print(f"URL: https://caldav.yandex.ru")
        print(f"Username: {username}")
        print(f"Token: {token[:20]}...")
        
        client = caldav.DAVClient(
            url="https://caldav.yandex.ru",
            username=username,
            password=token
        )
        
        print("Получаем principal...")
        principal = client.principal()
        print(f"Principal: {principal}")
        
        print("Получаем календари...")
        calendars = principal.calendars()
        print(f"Найдено календарей: {len(calendars)}")
        
        if calendars:
            for i, cal in enumerate(calendars):
                print(f"Календарь {i+1}: {cal}")
            
            # Тестируем получение событий
            default_calendar = calendars[0]
            today = datetime.now()
            
            print(f"\nИщем события на {today.strftime('%Y-%m-%d')}")
            events = default_calendar.date_search(
                start=today.replace(hour=0, minute=0, second=0),
                end=today.replace(hour=23, minute=59, second=59)
            )
            
            print(f"Найдено событий: {len(events)}")
            
            for event in events:
                print(f"Событие: {event}")
        
        print("\n✅ Подключение к CalDAV успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка подключения CalDAV: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_caldav_connection()