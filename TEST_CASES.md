# MILO Test Cases

## Test Suite Overview
This project currently has two categories of test scripts:

- **Automated unit/integration tests** (run by `pytest`):
  - `tests/test_automation_modules.py`
  - `tests/test_voice_recognition_module.py`
  - `tests/test_nlp_parser_module.py`
- **Manual diagnostics scripts** (not executed as pytest test cases):
  - `tests/test_voice.py`
  - `tests/test_nlp.py`

Latest automated run (in `milo_stable`):
- Command: `conda run -n milo_stable python -m pytest -q`
- Result: `11 passed, 2 warnings`

---

## A) Automated Test Cases (Pytest)

## 1. `tests/test_automation_modules.py`

| Test Case ID | Test Method | Objective | Expected Result |
|---|---|---|---|
| TC-AUTO-01 | `test_context_engine_returns_string` | Verify active context provider returns a valid context string | Value is `str` and one of: `unknown`, `notepad`, `browser`, `vscode`, `terminal` |
| TC-AUTO-02 | `test_hands_availability_flag` | Verify automation hand-control capability check returns boolean status | Return type is `bool` |
| TC-AUTO-03 | `test_rpa_context_wrapper` | Verify RPA service context wrapper returns a context string | Value is `str` |
| TC-AUTO-04 | `test_rpa_search_empty_query_is_rejected` | Validate guard-rail for empty browser search query | Returns dict with `success=False` and error message containing `empty` |
| TC-AUTO-05 | `test_eyes_availability_flag` | Verify computer-vision availability flag is well-defined | Return type is `bool` |

## 2. `tests/test_voice_recognition_module.py`

| Test Case ID | Test Method | Objective | Expected Result |
|---|---|---|---|
| TC-VOICE-01 | `test_normalize_phonetic_task_and_time` | Validate Tanglish/phonetic normalization for task and time tokens | Normalized output contains `task` and `pm` |
| TC-VOICE-02 | `test_normalize_notepad_mishear` | Validate correction of common STT mishearing (`north bad`) | Normalized output contains `notepad` |
| TC-VOICE-03 | `test_detect_command_wake_word` | Verify wake-word command detection mapping | Command detected and intent equals `WAKE_WORD` |
| TC-VOICE-04 | `test_parse_relative_reminder` | Verify reminder parser extracts relative-time reminders correctly | Non-null result with `seconds=300` and includes `datetime` |

## 3. `tests/test_nlp_parser_module.py`

| Test Case ID | Test Method | Objective | Expected Result |
|---|---|---|---|
| TC-NLP-01 | `test_order_agnostic_expense_phrase` | Validate expense intent extraction with flexible word order (`for food add a 50`) | Intent is `add_expense`, amount is `50.0`, category is `food` |
| TC-NLP-02 | `test_task_phrase_with_bare_hour_keeps_clean_title` | Validate task extraction for phrase with ambiguous hour (`tomorrow 4`) | Intent is `create_task`, title is `create ui`, and `date` is present |

---

## B) Manual Diagnostic Test Scenarios
These scripts are useful for demonstration and exploratory validation, but are not part of the automated pytest count.

## 1. `tests/test_voice.py`

| Scenario ID | Scenario | How to Run | Expected Outcome |
|---|---|---|---|
| SC-VOICE-01 | Command mapping diagnostics | `python tests/test_voice.py` | Prints mapped intents for sample phrases |
| SC-VOICE-02 | Live microphone single-shot STT | `python tests/test_voice.py` | Captures one utterance and prints transcription if successful |
| SC-VOICE-03 | Background continuous listening | `python tests/test_voice.py` | Background callback prints heard text until stop keyword/interrupt |

## 2. `tests/test_nlp.py`

| Scenario ID | Scenario | How to Run | Expected Outcome |
|---|---|---|---|
| SC-NLP-01 | Conversational intent extraction | `python tests/test_nlp.py` | Prints parsed intent and entities for each conversational prompt |

---

## Traceability Note
- Total automated test cases currently tracked by pytest: **11**.
- If new modules are added, extend this file with new `TC-*` rows to keep test documentation aligned with implementation.