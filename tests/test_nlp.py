#!/usr/bin/env python3
"""Test the optimized NLP parser"""

import sys
sys.path.insert(0, 'src')
from nlp_parser import NLPParser

parser = NLPParser()
test_cases = [
    'create a task called shopping',
    'list my tasks',
    'add 50 dollars to food',
    'check my balance',
    'complete task 3',
    'hello',
    'goodbye',
    'i spent 25 dollars on entertainment',
    'mark task 2 as complete',
]

print("=" * 60)
print("OPTIMIZED NLP PARSER TEST")
print("=" * 60)

for test in test_cases:
    result = parser.parse(test)
    print(f"\nInput: '{test}'")
    print(f"Intent: {result['intent']} (confidence: {result['confidence']:.2%})")
    if result['entities']:
        print(f"Entities: {result['entities']}")
    print("-" * 60)

print("\nAll tests completed successfully!")
