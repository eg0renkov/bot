"""Финальная очистка handlers"""
import os

# Читаем файл построчно
with open('handlers/menu_handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем проблемный блок между строками
lines = content.split('\n')

# Найдем индексы
search_start = -1
search_end = -1

for i, line in enumerate(lines):
    if '# Правильный обработчик search_toggle_ находится ниже' in line:
        search_start = i + 2  # Пропускаем пустую строку
    elif search_start != -1 and '@router.callback_query(F.data.startswith("search_toggle_"))' in line and 'async def search_toggle_callback' in lines[i+1]:
        search_end = i - 1
        break

if search_start != -1 and search_end != -1:
    print(f"Найден мусорный блок: строки {search_start+1} - {search_end+1}")
    
    # Удаляем мусорные строки
    new_lines = lines[:search_start] + lines[search_end+1:]
    
    # Записываем обратно
    with open('handlers/menu_handlers.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("Файл исправлен!")
else:
    print("Проблемный блок не найден")
    print(f"search_start: {search_start}, search_end: {search_end}")