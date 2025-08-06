#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

def test_simple():
    patterns = [
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об\s+(.+)",
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об\s+(.+)",
    ]
    
    test_text = "напиши письмо alexlesley01@yandex.ru о подорожании сыра"
    print(f"Text: '{test_text}'")
    
    for i, pattern in enumerate(patterns):
        print(f"Pattern {i+1}: {pattern}")
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"MATCH! Email: {match.group(1)}, Subject: {match.group(2)}")
        else:
            print("NO MATCH")
        print()

if __name__ == "__main__":
    test_simple()