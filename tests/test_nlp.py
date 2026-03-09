import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    from src.nlp.nlp_parser import NLPParser
except Exception:
    from nlp.nlp_parser import NLPParser

def run_conversational_tests():
    print("="*60)
    print("      🧠 M.I.L.O. CONVERSATIONAL NLP DIAGNOSTICS      ")
    print("="*60)
    
    parser = NLPParser()

    test_cases = [
        "My wallet is crying, I just spent 45 dollars on an uber.",
        "Yo Milo, I'm super tired. Wake me up with an alarm in exactly one hour.",
        "Hey buddy, how is your day going?",
        "Fire up visual studio code for me, I need to work.",
        "I have to submit my python assignment by tomorrow evening, put that on my list and make it urgent."
    ]

    for phrase in test_cases:
        print(f"\n🗣️ User:  \"{phrase}\"")
        
        result = parser.parse(phrase)
        
        print(f"🎯 Intent: {result['intent']}")
        if result['entities']:
            print("📦 Entities:")
            for k, v in result['entities'].items():
                print(f"   - {k}: {v}")
        else:
            print("📦 Entities: None")
        print("-" * 60)

if __name__ == "__main__":
    run_conversational_tests()