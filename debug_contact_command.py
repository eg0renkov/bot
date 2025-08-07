#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Простой тест без эмодзи
import asyncio

async def test_contact_exclusion():
    test_command = "добавь контакт Анны +79186057593"
    text_lower = test_command.lower()
    
    print("Test command:", test_command)
    print("text_lower:", text_lower)
    
    contact_exclusions = ['контакт', 'номер', 'телефон', '+7', '+3', '+8', '+9']
    found_exclusions = [ex for ex in contact_exclusions if ex in text_lower]
    
    print("Contact exclusions:", contact_exclusions)
    print("Found exclusions:", found_exclusions)
    
    should_return_none = len(found_exclusions) > 0
    print("Should return None:", should_return_none)
    
    return should_return_none

if __name__ == "__main__":
    result = asyncio.run(test_contact_exclusion())
    print("FINAL RESULT:", result)