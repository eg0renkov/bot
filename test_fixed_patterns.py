#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

def test_fixed_patterns():
    patterns = [
        # Fixed patterns with "об?" to match both "о" and "об"
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[-–—]\s*об?\s+(.+)",
        r"напиш[иь].*письмо\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+об?\s+(.+)",
    ]
    
    test_texts = [
        "напиши письмо alexlesley01@yandex.ru о подорожании сыра",
        "напиши письмо alexlesley01@yandex.ru об подорожании сыра",
        "напиши письмо alexlesley01@yandex.ru - об подорожании сыра",
    ]
    
    for test_text in test_texts:
        print(f"Testing: '{test_text}'")
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                print(f"  Pattern {i+1}: MATCH! Email: {match.group(1)}, Subject: {match.group(2)}")
            else:
                print(f"  Pattern {i+1}: NO MATCH")
        print()

if __name__ == "__main__":
    test_fixed_patterns()