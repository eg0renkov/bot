"""Скрипт для очистки дублирующих обработчиков в menu_handlers.py"""

def clean_handlers():
    # Читаем файл
    with open('handlers/menu_handlers.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Найдем строки с мусорным кодом (строки 794-876)
    start_line = 794 - 1  # индексы с 0
    end_line = 876 - 1    # до строки с await callback.answer()
    
    print(f"Удаляем строки {start_line+1}-{end_line+1}")
    print("Содержимое:")
    for i in range(start_line, min(end_line+1, len(lines))):
        print(f"{i+1}: {lines[i].rstrip()}")
    
    # Удаляем мусорные строки
    new_lines = lines[:start_line] + lines[end_line+1:]
    
    # Записываем обратно
    with open('handlers/menu_handlers.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\nУдалено {end_line-start_line+1} строк")
    print("Файл очищен!")

if __name__ == "__main__":
    clean_handlers()