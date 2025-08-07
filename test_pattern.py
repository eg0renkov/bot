#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест регулярных выражений для email
"""
import re

def test_patterns():
    text = "напиши письмо леониду с просьбой о встрече"
    
    patterns = [
        # НОВЫЕ ПАТТЕРНЫ ДЛЯ ИМЕН (БЕЗ EMAIL)
        r"напиш[иь].*письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
        r"отправ[ьи].*письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
        r"письмо\s+([а-яёА-ЯЁa-zA-Z]+(?:у)?)\s+с\s+(.+)",
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"Testing pattern {i+1}: {pattern}")
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Pattern {i+1} MATCHED!")
            recipient = match.group(1).strip()
            subject = match.group(2).strip()
            print(f"Recipient: '{recipient}'")
            print(f"Subject: '{subject}'")
            print()
        else:
            print(f"Pattern {i+1} NO MATCH")
            print()

if __name__ == "__main__":
    test_patterns()