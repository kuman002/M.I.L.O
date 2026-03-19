import json
import re
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Tuple
import dateparser

try:
    from word2number import w2n
    WORD2NUMBER_AVAILABLE = True
except Exception:
    w2n = None
    WORD2NUMBER_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except Exception:
    TfidfVectorizer = None
    LogisticRegression = None
    SKLEARN_AVAILABLE = False

class NLPParser:
    """
    Advanced Conversational NLU for M.I.L.O.
    Uses Local Llama 3 to semantically understand intent and extract entities.
    """
    
    def __init__(self):
        print("🧠 Initializing Conversational NLP (Llama 3)...")

        self.llm = None
        self._llm_disabled = False
        self._warned_unavailable = False
        self._app_catalog: List[str] = [
            "notepad", "calculator", "paint", "word", "excel", "powerpoint",
            "chrome", "firefox", "edge", "brave", "opera", "browser",
            "code", "vscode", "visual studio", "terminal", "cmd", "powershell",
            "slack", "discord", "spotify", "file explorer", "settings"
        ]
        self._app_aliases: Dict[str, str] = {
            "note pad": "notepad",
            "not pad": "notepad",
            "notebad": "notepad",
            "not bad": "notepad",
            "north bad": "notepad",
            "noth bad": "notepad",
            "noths bad": "notepad",
            "north pad": "notepad",
            "open note": "notepad",
            "vs code": "vscode",
            "visual studio code": "vscode",
            "ms word": "word",
            "power point": "powerpoint",
            "google chrome": "chrome",
            "microsoft edge": "edge"
        }
        self._init_llm()
        self._init_intent_classifier()

    def _init_intent_classifier(self):
        """Initialize a lightweight local intent classifier as a defensive fallback."""
        self._intent_vectorizer = None
        self._intent_clf = None
        if not SKLEARN_AVAILABLE:
            return

        samples: List[Tuple[str, str]] = [
            ("add task to finish report tomorrow", "create_task"),
            ("create a task for interview", "create_task"),
            ("put this on my list", "create_task"),
            ("show my tasks", "list_tasks"),
            ("list pending tasks", "list_tasks"),
            ("add expense 500 for food", "add_expense"),
            ("for food add a 50", "add_expense"),
            ("log kharcha 120", "add_expense"),
            ("add income 2500", "add_income"),
            ("check my balance", "check_balance"),
            ("what is my balance", "check_balance"),
            ("remind me in 10 minutes", "add_reminder"),
            ("set reminder at 5 pm", "add_reminder"),
            ("open brave browser", "open_app"),
            ("launch notepad", "open_app"),
            ("hello milo", "greeting"),
            ("help me", "help"),
            ("what time is it", "time_query"),
        ]

        try:
            texts = [s[0] for s in samples]
            labels = [s[1] for s in samples]
            self._intent_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            X = self._intent_vectorizer.fit_transform(texts)
            self._intent_clf = LogisticRegression(max_iter=500, class_weight="balanced")
            self._intent_clf.fit(X, labels)
        except Exception:
            self._intent_vectorizer = None
            self._intent_clf = None

    def _predict_intent_local(self, text_lower: str) -> Tuple[Optional[str], float]:
        if not self._intent_vectorizer or not self._intent_clf:
            return None, 0.0
        try:
            X = self._intent_vectorizer.transform([text_lower])
            probs = self._intent_clf.predict_proba(X)[0]
            idx = int(probs.argmax())
            return self._intent_clf.classes_[idx], float(probs[idx])
        except Exception:
            return None, 0.0

    def _has_ambiguous_time_reference(self, text_lower: str) -> bool:
        """Detect phrases where hour is present but AM/PM is missing (e.g., 'tomorrow 4', 'at 5')."""
        if re.search(r"\b\d{1,2}(?::\d{2})?\s*(am|pm)\b", text_lower):
            return False
        return bool(
            re.search(r"\b(?:today|tomorrow|tonight)\s+\d{1,2}(?::\d{2})?\b", text_lower)
            or re.search(r"\bat\s+\d{1,2}(?::\d{2})?\b", text_lower)
        )

    def _init_llm(self):
        try:
            from langchain_ollama import OllamaLLM
            try:
                self.llm = OllamaLLM(model="llama3", format="json", temperature=0.0)
            except TypeError:
                self.llm = OllamaLLM(model="llama3", temperature=0.0)
            return
        except Exception:
            pass

        try:
            from langchain_community.llms import Ollama
            self.llm = Ollama(model="llama3", format="json", temperature=0.0)
        except Exception:
            self.llm = None
        
    def _get_system_prompt(self) -> str:
        """The strict instruction set for the LLM."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
        You are the Intent Routing Engine for M.I.L.O., a context-aware assistant.
        Strictly categorize requests as either a TASK or a REMINDER based on the psychological difference between Effort and Time.

        1. THE TASK (Effort-Based):
           - Purpose: Actions requiring focus, sustained effort, or multi-step work.
           - Triggers: "finish", "build", "study", "code", "prepare", "write", "debug", "start".
           - Lifecycle: Something that sits on a list until "Done".
           - Output Intent: "create_task"

        2. THE REMINDER (Time-Based Alarm):
           - Purpose: Low-effort, instantaneous triggers or memory cues.
           - Triggers: "remind me", "ping me", "alert me", "notify me", "alarm".
           - Exactness: Relies strictly on an exact time or countdown.
           - Output Intent: "add_reminder"

        3. OTHER INTENTS:
           - "add_expense": If currency ($, rupees, bucks) or "spent/cost" is mentioned.
           - "open_app": If user wants to launch software (browser, code, etc).
           - "list_tasks": If user wants to see their current workload.
           - "greeting": Casual hellos.

        Current system time: {current_time}
        You MUST respond ONLY with a valid JSON object.
        
        Task Example: {{"intent": "create_task", "entities": {{"title": "Code dashboard UI", "priority": "high", "date": "2026-03-05 09:00:00"}}}}
        Reminder Example: {{"intent": "add_reminder", "entities": {{"title": "Call Mom", "date": "18:00:00"}}}}
        """

    def parse(self, text: str) -> dict:
        """Parse user text via Ollama when available, fallback to local rules otherwise."""
        if not text:
            return {"intent": "unknown", "entities": {}, "original_text": text, "confidence": 0.0}

        print(f"[NLP] Parsing: '{text}'")  # Debug log

        if self.llm is None or self._llm_disabled:
            result = self._fallback_parse(text)
            print(f"[NLP] Fallback result - Intent: {result['intent']}, Confidence: {result.get('confidence', 0.0)}")
            return result

        prompt = f"{self._get_system_prompt()}\n\nUser: \"{text}\"\nOutput:"
        try:
            response = self.llm.invoke(prompt)
            parsed_data = json.loads(response)

            if "intent" not in parsed_data:
                parsed_data["intent"] = "unknown"
            if "entities" not in parsed_data:
                parsed_data["entities"] = {}

            # Defensive post-processing for ambiguous time references in tasks.
            if parsed_data.get("intent") == "create_task" and self._has_ambiguous_time_reference(text.lower()):
                parsed_data["entities"].setdefault("missing_entity", "meridiem")
                parsed_data["entities"].setdefault("clarification_prompt", "Did you mean AM or PM for that time?")

            parsed_data["original_text"] = text
            parsed_data["confidence"] = 0.99
            print(f"[NLP] LLM result - Intent: {parsed_data['intent']}, Confidence: {parsed_data['confidence']}")
            return parsed_data
        except Exception as e:
            self._llm_disabled = True
            if not self._warned_unavailable:
                print(f"⚠️ Ollama unavailable, switching to offline NLP fallback: {e}")
                self._warned_unavailable = True
            result = self._fallback_parse(text)
            print(f"[NLP] Fallback result - Intent: {result['intent']}, Confidence: {result.get('confidence', 0.0)}")
            return result

    def _normalize_text(self, text: str) -> str:
        """Heavily normalize text for more consistent parsing"""
        t = text.lower().strip()
        # Normalize time markers
        t = t.replace("p.m.", "pm").replace("a.m.", "am").replace("pm.", "pm").replace("am.", "am")
        t = t.replace("b.m.", "pm").replace("b.m", "pm").replace("b m", "pm")
        # Phonetic corrections
        t = t.replace("wapan", "open").replace("warp", "open")
        t = t.replace("toss", "task").replace("add a toss", "add task")
        t = t.replace("had it asked", "add task").replace("i ask for", "add task for")
        t = t.replace("foot", "food")
        # Common typos
        t = t.replace("5p", "5 pm").replace("5am", "5 am").replace("5pm", "5 pm")
        t = t.replace("power point", "powerpoint").replace("our point", "powerpoint")
        # Tanglish specific phonetic fixes
        t = t.replace("later", "slide").replace("layer", "slide").replace("ball", "podu").replace("bow", "podu")

        # Voice mis-hearing fixes for app launches (especially notepad)
        t = re.sub(r"\b(note\s*pad|not\s*pad|notebad|not\s*bad|north\s*bad|noth\s*bad|noths\s*bad|north\s*pad)\b", "notepad", t)

        # Normalize punctuation noise from speech-to-text
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _app_similarity(self, left: str, right: str) -> float:
        return SequenceMatcher(None, left, right).ratio()

    def _generate_ngrams(self, words: List[str], max_n: int = 3) -> List[str]:
        phrases: List[str] = []
        if not words:
            return phrases
        max_size = min(max_n, len(words))
        for size in range(1, max_size + 1):
            for index in range(0, len(words) - size + 1):
                phrases.append(" ".join(words[index:index + size]))
        return phrases

    def _extract_open_app_name(self, text_lower: str) -> Optional[str]:
        # Keep only the command segment when user says multiple clauses.
        open_markers = ["open", "launch", "start", "run", "kholo", "pannu"]
        marker_positions = [(marker, text_lower.find(marker)) for marker in open_markers if marker in text_lower]
        if not marker_positions:
            return None

        marker, marker_pos = min(marker_positions, key=lambda item: item[1])
        phrase = text_lower[marker_pos + len(marker):].strip()
        if not phrase:
            return None

        phrase = re.split(r"\b(and|then|after that|for me|please)\b", phrase)[0].strip()
        phrase = re.sub(r"\s+", " ", phrase)

        if phrase in self._app_aliases:
            return self._app_aliases[phrase]

        # Substring checks against canonical app names and aliases
        for app in self._app_catalog:
            if app in phrase:
                return app
        for alias, app in self._app_aliases.items():
            if alias in phrase:
                return app

        words = phrase.split()
        candidates = self._generate_ngrams(words, max_n=3)
        if not candidates:
            return None

        best_match: Optional[Tuple[str, float]] = None
        for candidate in candidates:
            for app in self._app_catalog:
                score = self._app_similarity(candidate, app)
                if best_match is None or score > best_match[1]:
                    best_match = (app, score)
            for alias, app in self._app_aliases.items():
                score = self._app_similarity(candidate, alias)
                if best_match is None or score > best_match[1]:
                    best_match = (app, score)

        if best_match and best_match[1] >= 0.72:
            return best_match[0]
        return None

    def _extract_quoted_or_tail(self, text_lower: str, lead_pattern: str) -> str:
        working = re.sub(lead_pattern, "", text_lower, count=1).strip(" .,!?")
        quoted_match = re.search(r"['\"]([^'\"]+)['\"]", working)
        if quoted_match:
            return quoted_match.group(1).strip()
        return working.strip()

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """
        Advanced rule-based fallback when the LLM is unavailable.
        Uses a combination of keyword matching, regex, and dateparser.
        """
        raw_text = text
        text_lower = self._normalize_text(text)
        
        # 1. Pre-process numbers (e.g., "five" -> "5")
        text_with_digits = self._convert_words_to_numbers(text_lower)
        
        entities: Dict[str, Any] = {}
        confidence = 0.75

        # 2. Priority: Special Commands (Short Circuits)
        if any(word in text_lower for word in ["hello", "hi", "hey", "vanakkam", "namaskaram"]):
            return {"intent": "greeting", "entities": {}, "original_text": raw_text, "confidence": 0.95}
        
        if "help" in text_lower:
            return {"intent": "help", "entities": {}, "original_text": raw_text, "confidence": 0.95}

        # 3. Intent Detection: Presentation Control (Very Specific)
        if any(phrase in text_lower for phrase in ["next slide", "advance slide", "next page", "adutha slide"]):
            return {"intent": "next_slide", "entities": {}, "original_text": raw_text, "confidence": 0.98}
        if any(phrase in text_lower for phrase in ["previous slide", "prev slide", "go back slide", "paya slide"]):
            return {"intent": "prev_slide", "entities": {}, "original_text": raw_text, "confidence": 0.98}

        # 3.5 Local classifier hint (defensive fallback when LLM is unavailable)
        predicted_intent, predicted_conf = self._predict_intent_local(text_lower)

        # 4. Intent Detection: Expenses (Triggered by currency or spent keywords)
        expense_keywords = ["spent", "paid", "cost", "dropped", "bought", "selavu", "expense", "recorded", "kharcha", "spend", "spent"]
        currency_keywords = ["rupees", "rs", "bucks", "dollars", "$", "inr"]
        expense_category_hints = [
            "food", "lunch", "dinner", "coffee", "tea", "restaurant", "transport", "uber", "taxi",
            "bus", "train", "auto", "petrol", "fuel", "shopping", "grocery", "medicine", "doctor",
            "rent", "recharge", "bill", "internet", "electricity", "movie"
        ]
        
        amount_match = re.search(r"(\d+(?:\.\d{1,2})?)", text_with_digits)
        has_expense_keyword = any(kw in text_lower for kw in expense_keywords)
        has_currency = any(cur in text_lower for cur in currency_keywords)
        has_category_hint = any(cat in text_lower for cat in expense_category_hints)
        has_add_like = any(kw in text_lower for kw in ["add", "log", "record", "put", "spent", "pay", "paid"])
        looks_like_task_or_reminder = any(kw in text_lower for kw in ["task", "todo", "remind", "reminder", "alarm"])

        # Order-agnostic expense detection:
        # examples: "for food add 50", "add 250 for taxi", "spent 120 tea"
        is_likely_expense = bool(amount_match) and (
            has_expense_keyword
            or has_currency
            or ((has_add_like or "for" in text_lower) and has_category_hint and not looks_like_task_or_reminder)
        )

        if is_likely_expense or (predicted_intent == "add_expense" and predicted_conf >= 0.72 and amount_match):
            if amount_match:
                entities["amount"] = float(amount_match.group(1))
                # Extract category
                cat_map = {
                    "food": ["food", "lunch", "dinner", "burger", "coffee", "restaurant", "sapadu"],
                    "transport": ["uber", "taxi", "bus", "train", "auto", "petrol"],
                    "shopping": ["amazon", "clothes", "shopping", "gift"],
                    "health": ["medicine", "doctor", "gym", "health"]
                }
                entities["category"] = "other"
                for cat, keywords in cat_map.items():
                    if any(kw in text_lower for kw in keywords):
                        entities["category"] = cat
                        break
                return {"intent": "add_expense", "entities": entities, "original_text": raw_text, "confidence": 0.9}

        # 5. Intent Detection: Reminders & Tasks (Natural Language Date Extraction)
        # Apply Psychological Rules: Effort vs Time
        
        # EFFORT triggers (Tasks)
        effort_words = ["finish", "code", "build", "study", "prepare", "debug", "write", "work", "assignment", "report", "create", "creating", "design", "make", "update", "ui", "dashboard"]
        # TIME triggers (Reminders)
        time_words = ["remind", "alarm", "ping", "alert", "notify", "ping", "call", "check oven", "drink water"]
        
        is_explicit_reminder = any(kw in text_lower for kw in ["remind", "alarm", "ping", "alert"])
        is_high_effort = any(kw in text_lower for kw in effort_words)
        
        # Heuristic: If it has an exact time but NO effort words, it's a reminder.
        # If it has effort words, it's a task, even if it has a due date.
        is_task = is_high_effort or (any(kw in text_lower for kw in ["task", "todo", "list", "vela"]) and not is_explicit_reminder)
        is_reminder = is_explicit_reminder or (not is_task and any(kw in text_lower for kw in ["at", "in", "am", "pm"]) and any(kw in text_lower for kw in time_words))
        
        if is_reminder or is_task:
            # Try to extract date/time using dateparser
            extracted_dt = self._extract_date_with_parser(text_with_digits)
            if extracted_dt:
                entities["date"] = extracted_dt.strftime('%Y-%m-%d %H:%M:%S')
                if self._has_ambiguous_time_reference(text_lower):
                    entities["missing_entity"] = "meridiem"
                    entities["clarification_prompt"] = "Did you mean AM or PM for that time?"
            
            # Clean title extraction
            entities["title"] = self._surgical_title_extraction(text_lower, is_task=is_task)
            
            if is_reminder and not is_high_effort:
                return {"intent": "add_reminder", "entities": entities, "original_text": raw_text, "confidence": 0.88}
            else:
                # Handle list tasks vs create task
                if any(w in text_lower for w in ["show", "list", "display", "what are"]):
                    return {"intent": "list_tasks", "entities": {}, "original_text": raw_text, "confidence": 0.9}
                
                # Check for priority
                if any(w in text_lower for w in ["urgent", "important", "high priority", "mukkiyam"]):
                    entities["priority"] = "high"
                else:
                    entities["priority"] = "medium"
                return {"intent": "create_task", "entities": entities, "original_text": raw_text, "confidence": 0.85}

        # Classifier-based simple routes for intents that do not require heavy entity extraction.
        if predicted_conf >= 0.78 and predicted_intent in {"check_balance", "list_tasks", "time_query", "greeting", "help"}:
            return {"intent": predicted_intent, "entities": {}, "original_text": raw_text, "confidence": predicted_conf}

        # 6. Intent Detection: Apps / Search (More Robust)
        # Context-aware computer-use intents
        if re.match(r"^(milo[\s,]+)?(type|write|enter)\b", text_lower):
            typed_text = self._extract_quoted_or_tail(text_lower, r"^(milo[\s,]+)?(type|write|enter)\b")
            if typed_text:
                entities["text"] = typed_text
                return {"intent": "computer_type", "entities": entities, "original_text": raw_text, "confidence": 0.94}

        if re.search(r"\b(click|tap)\b", text_lower) and re.search(r"\b(on|link|button|text)\b", text_lower):
            target = text_lower
            target = re.sub(r"\b(click|tap)\b", "", target)
            target = re.sub(r"\b(on|the|link|button|text|for|please)\b", " ", target)
            target = re.sub(r"\s+", " ", target).strip(" .,!?")
            quoted_match = re.search(r"['\"]([^'\"]+)['\"]", text_lower)
            if quoted_match:
                target = quoted_match.group(1).strip()
            if target:
                entities["target_text"] = target
                return {"intent": "computer_click_text", "entities": entities, "original_text": raw_text, "confidence": 0.9}

        if re.search(r"\b(search|find)\b", text_lower) and re.search(r"\b(for|in browser|in chrome|in brave|in edge|in firefox|here)\b", text_lower):
            query = text_lower
            query = re.sub(r"\b(search|find)\b", "", query, count=1)
            query = re.sub(r"\b(for|in browser|in chrome|in brave|in edge|in firefox|here|please)\b", " ", query)
            query = re.sub(r"\s+", " ", query).strip(" .,!?")
            if query:
                entities["query"] = query
                return {"intent": "computer_search", "entities": entities, "original_text": raw_text, "confidence": 0.92}

        # Check Search first to allow "open browser and search..."
        if any(kw in text_lower for kw in ["search", "google", "find", "thedu", "sollu"]):
            query = text_lower
            for kw in ["search for", "search what is", "search about", "search", "google", "find", "thedu", "sollu"]:
                query = query.replace(kw, "")
            query = query.strip(" ?.")
            if query:
                entities["query"] = query
                return {"intent": "google_search", "entities": entities, "original_text": raw_text, "confidence": 0.9}

        if any(kw in text_lower for kw in ["open", "launch", "start", "run", "kholo", "pannu"]):
            app_name = self._extract_open_app_name(text_lower)
            if app_name:
                entities["app_name"] = app_name
                return {"intent": "open_app", "entities": entities, "original_text": raw_text, "confidence": 0.95}

        # 7. Fallback to Chitchat
        return {"intent": "chitchat", "entities": {}, "original_text": raw_text, "confidence": 0.5}

    def _convert_words_to_numbers(self, text: str) -> str:
        """Convert 'five' to '5', etc. using word2number"""
        fallback_numbers = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }

        def _word_to_number(token: str):
            if WORD2NUMBER_AVAILABLE and w2n is not None:
                return w2n.word_to_num(token)
            return fallback_numbers.get(token)

        words = text.split()
        new_words = []
        i = 0
        while i < len(words):
            # Try to find sequences of number words
            try:
                # This is a bit simplified; w2n.word_to_num can be aggressive
                # We only want to convert if it's clearly a number
                potential_num = words[i]
                if potential_num in ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]:
                    converted = _word_to_number(potential_num)
                    new_words.append(str(converted) if converted is not None else potential_num)
                else:
                    new_words.append(potential_num)
            except:
                new_words.append(words[i])
            i += 1
        return " ".join(new_words)

    def _extract_date_with_parser(self, text: str) -> Optional[datetime]:
        """Use dateparser to find dates in text."""
        lower_text = text.lower().strip()

        # Handle bare-hour schedule phrases explicitly (e.g., "tomorrow 4", "today 9").
        bare_hour = re.search(r"\b(today|tomorrow|tonight)\s+(\d{1,2})(?::(\d{2}))?\b", lower_text)
        if bare_hour:
            day_word = bare_hour.group(1)
            hour = int(bare_hour.group(2))
            minute = int(bare_hour.group(3) or "0")

            now = datetime.now()
            day_offset = 1 if day_word == "tomorrow" else 0

            # Prefer PM for ambiguous spoken hour in common task planning.
            if 1 <= hour <= 7:
                hour += 12

            target = (now + timedelta(days=day_offset)).replace(
                hour=hour % 24,
                minute=minute,
                second=0,
                microsecond=0,
            )
            if day_word in ("today", "tonight") and target <= now:
                target += timedelta(days=1)
            return target

        # Find time-related keywords to narrow down the search
        time_keywords = ["tomorrow", "today", "tonight", "next", "in", "at", "am", "pm", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        # Check if any time keyword exists
        if not any(kw in text.lower() for kw in time_keywords):
            return None

        # Surgical cleaning of the date string to help dateparser
        # We try to extract phrases starting with 'at', 'in', 'on', or specific time words
        settings = {'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()}
        
        # Try full text first
        dt = dateparser.parse(text, settings=settings)
        if dt:
            return dt
            
        return None

    def _surgical_title_extraction(self, text: str, is_task: bool = False) -> str:
        """
        Surgically removes command words and time markers to leave only the core title.
        Fixes bugs like 'interview pmm' from 'interview at 5pm'.
        """
        source_text = text.lower()
        t = source_text
        
        # 1. Remove obvious command prefixes
        prefixes = [
            r"\badd task to\b", r"\badd task for\b", r"\bcreate task for\b", r"\bset reminder for\b",
            r"\bi need to\b", r"\bi have to\b", r"\bremind me to\b", r"\bput\b", r"\badd\b", r"\btask\b",
            r"\bvela\b", r"\bpannu\b", r"\bpodu\b"
        ]
        for p in prefixes:
            t = re.sub(p, "", t)
            
        # 2. Remove time/date markers surgically
        # Remove "at X pm", "at X:XX", "tomorrow", "today", etc.
        t = re.sub(r"\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", t)
        t = re.sub(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", "", t)
        t = re.sub(r"\bin\s+(?:\d+|a|an)\s+(?:minute|hour|day)s?\b", "", t)
        t = re.sub(r"\b(tomorrow|today|tonight|next week|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday)\b", "", t)

        # Handle bare-hour forms like "tomorrow 4" / "today 9" where hour has no am/pm.
        if re.search(r"\b(tomorrow|today|tonight|next)\b", source_text):
            t = re.sub(r"\b\d{1,2}(?::\d{2})?\b", "", t)
        
        # 3. Final cleanup
        t = re.sub(r"\b(for|to|at|on|with|my|a|an|the)\b", "", t)
        t = re.sub(r"\s+", " ", t).strip(" ,.-")
        
        # Bug fix: if "interview" became "interview pmm", it means "pm" wasn't removed correctly
        # We specifically check for dangling 'pm' or 'am' at the end of words
        t = re.sub(r"(\w+)(pm|am)\b", r"\1", t)
        
        return t or "Untitled"

    def _extract_title_for_reminder(self, text_lower: str) -> str:
        title = text_lower
        title = re.sub(r"\b(remind me to|remind me|set reminder|add reminder|wake me up with an alarm|alarm)\b", "", title)
        # Remove time patterns like "in 5 minutes", "at 5pm"
        title = re.sub(r"\bin\s+\d+\s*(?:minute|minutes|hour|hours|day|days)\b", "", title)
        title = re.sub(r"\bat\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", title)
        title = re.sub(r"\s+", " ", title).strip(" ,.-")
        return title or "reminder"

    def _extract_title_for_task(self, text_lower: str) -> str:
        title = text_lower
        # 1. Remove task command phrases
        title = re.sub(r"\b(i have to|i need to|please|milo|hey|put that on my list|add to my list|add task|create task|new task|task|todo|to do|to-do|make it|set a task|set task|vela|panu|podu|next|previous|first|last)\b", "", title)
        # 2. Remove specific date/time markers
        title = re.sub(r"\bin\s+\d+\s*(?:minute|minutes|hour|hours|day|days)\b", "", title)
        title = re.sub(r"\b(today|tomorrow|tonight)\b", "", title)
        title = re.sub(r"\bon\s+\d{4}-\d{2}-\d{2}\b", "", title)
        # Enhanced time removal (handles "5pm", "5:30", "at 5")
        title = re.sub(r"\bat\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", title)
        title = re.sub(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", "", title)
        # 3. Cleanup particles
        title = re.sub(r"\b(a|an|the)\b", "", title)
        title = re.sub(r"\b(to|for)\b", "", title, count=1)
        title = re.sub(r"\b(urgent|asap|important|high priority|low priority|zaroori)\b", "", title)
        title = re.sub(r"\s+", " ", title).strip(" ,.-")
        return title or "untitled task"

    def _extract_task_datetime(self, text_lower: str) -> str:
        now = datetime.now()

        # Relative durations: "in 2 hours"
        relative = self._extract_relative_datetime(text_lower)
        if relative:
            return relative

        # Explicit date: "on 2026-03-01"
        date_match = re.search(r"\bon\s*(\d{4}-\d{2}-\d{2})\b", text_lower)
        # Flexible time match: "at 5", "at 5pm", "5:30pm", "at 5:30"
        time_match = re.search(r"(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text_lower)
        if not time_match:
            # Fallback for "at 5" without am/pm
            time_match = re.search(r"\bat\s*(\d{1,2})(?::(\d{2}))?\b", text_lower)
        if not time_match:
            # Fallback for bare-hour with day marker: "tomorrow 4", "today 9"
            time_match = re.search(r"\b(?:today|tomorrow|tonight)\s+(\d{1,2})(?::(\d{2}))?\b", text_lower)

        if date_match:
            date_str = date_match.group(1)
            hour, minute = 9, 0
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or "0")
                meridiem = time_match.group(3) if len(time_match.groups()) >= 3 else None
                if meridiem == "pm" and hour < 12: hour += 12
                if meridiem == "am" and hour == 12: hour = 0
            try:
                target = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S")
                return target.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError: return ""

        # Today/Tomorrow/Tonight
        day_offset = 0
        if "tomorrow" in text_lower: day_offset = 1
        elif "today" in text_lower or "tonight" in text_lower: day_offset = 0
        elif not time_match: return ""

        hour, minute = 9, 0
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or "0")
            meridiem = time_match.group(3) if len(time_match.groups()) >= 3 else None
            if meridiem == "pm" and hour < 12: hour += 12
            if meridiem == "am" and hour == 12: hour = 0
            if meridiem is None:
                # Prefer evening interpretation for ambiguous spoken schedules like "tomorrow 4".
                if 1 <= hour <= 7:
                    hour += 12

        target = (now + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        # If time passed today and no specific day mentioned, assume tomorrow
        if day_offset == 0 and time_match and target <= now and "today" not in text_lower:
            target += timedelta(days=1)

        return target.strftime('%Y-%m-%d %H:%M:%S')

    def _extract_relative_datetime(self, text_lower: str) -> str:
        now = datetime.now()
        if "one hour" in text_lower:
            return (now + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        match = re.search(r"in\s+(\d+)\s+(minute|minutes|hour|hours|day|days)", text_lower)
        if not match: return ""

        value, unit = int(match.group(1)), match.group(2)
        if "minute" in unit: target = now + timedelta(minutes=value)
        elif "hour" in unit: target = now + timedelta(hours=value)
        else: target = now + timedelta(days=value)
        return target.strftime('%Y-%m-%d %H:%M:%S')
