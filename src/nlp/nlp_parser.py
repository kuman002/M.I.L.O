"""
Natural Language Processing Parser for MILO
Offline command understanding and intent recognition - OPTIMIZED
"""

import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta


class NLPParser:
    """Optimized offline NLP parser for understanding user commands"""
    
    def __init__(self):
        """Initialize NLP parser with intent patterns and keywords"""
        self.intent_patterns = self._load_patterns()
        self.keyword_weights = self._load_keyword_weights()
        self.entity_extractors = self._load_entity_extractors()
    
    def _load_keyword_weights(self) -> Dict[str, Dict[str, float]]:
        """Load keyword weights for better intent matching"""
        return {
            'create_task': {
                'create': 1.0, 'add': 0.9, 'new': 0.8, 'make': 0.7, 'schedule': 0.9, 'set': 0.8,
                'task': 1.0, 'todo': 1.0
            },
            'add_reminder': {
                'remind': 1.0, 'reminder': 1.0, 'remember': 0.9, 'notify': 0.8, 'alert': 0.8,
                'set': 0.7, 'schedule': 0.7
            },
            'list_tasks': {
                'show': 0.9, 'list': 1.0, 'display': 0.8, 'get': 0.7, 'tell': 0.6,
                'task': 0.8, 'todo': 0.8, 'reminders': 0.9, 'what are': 0.8
            },
            'complete_task': {
                'complete': 1.0, 'finish': 0.9, 'done': 0.8, 'mark': 0.85, 'check off': 0.9,
                'task': 0.8, 'todo': 0.8
            },
            'delete_task': {
                'delete': 1.0, 'remove': 0.95, 'cancel': 0.9, 'task': 0.8, 'todo': 0.8
            },
            'add_expense': {
                'expense': 1.0, 'spent': 0.95, 'spend': 0.9, 'cost': 0.85, 'paid': 0.8,
                'money': 0.7, 'dollar': 0.8, 'rupee': 0.8, 'rs': 0.7, 'add': 0.6
            },
            'add_income': {
                'income': 1.0, 'earned': 0.95, 'earn': 0.9, 'salary': 0.95, 'money': 0.7, 'received': 0.8
            },
            'check_balance': {
                'balance': 1.0, 'money': 0.8, 'finance': 0.9, 'budget': 0.85,
                'how much': 0.8, 'check': 0.7, 'show': 0.7, 'total': 0.7
            },
            'add_habit': {
                'habit': 1.0, 'create': 0.9, 'add': 0.9, 'new': 0.8, 'track': 0.85, 'start': 0.7
            },
            'log_habit': {
                'habit': 0.9, 'log': 0.95, 'mark': 0.85, 'complete': 0.8, 'did': 0.7
            },
            'greeting': {
                'hello': 1.0, 'hi': 1.0, 'hey': 0.95, 'good morning': 0.9, 'morning': 0.7
            },
            'goodbye': {
                'goodbye': 1.0, 'bye': 0.95, 'exit': 0.9, 'quit': 0.9, 'close': 0.7
            },
            'help': {
                'help': 1.0, 'commands': 0.9, 'what can': 0.8, 'how to': 0.8
            },
            'open_app': {
                'open': 1.0, 'launch': 0.95, 'start': 0.9, 'run': 0.85,
                'app': 0.8, 'application': 0.8, 'program': 0.8
            },
            'open_file': {
                'open': 1.0, 'file': 0.9, 'document': 0.85, 'show': 0.7
            },
            'open_folder': {
                'open': 1.0, 'folder': 1.0, 'directory': 0.95, 'path': 0.8
            },
            'open_url': {
                'open': 1.0, 'url': 1.0, 'website': 0.95, 'browse': 0.9,
                'visit': 0.85, 'go to': 0.8, 'link': 0.8
            },
        }
    
    def _load_entity_extractors(self) -> Dict[str, callable]:
        """Load entity extraction functions"""
        return {
            'amount': self._extract_amount,
            'category': self._extract_category,
            'priority': self._extract_priority,
            'date': self._extract_date,
            'task_id': self._extract_task_id,
            'title': self._extract_title,
        }
    
    def _load_patterns(self) -> Dict[str, List[Tuple[re.Pattern, float]]]:
        """Load regex patterns with confidence weights for different intents"""
        return {
            'create_task': [
                (re.compile(r'\b(?:create|add|new|make)\s+(?:a\s+)?(?:task|todo|reminder)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:task|todo|reminder)\b.*\b(?:create|add|new|make)\b', re.IGNORECASE), 0.95),
                (re.compile(r'\b(?:schedule|set)\s+(?:a\s+)?(?:task|reminder|alarm)\b', re.IGNORECASE), 0.9),
                (re.compile(r'\bcreate\b.*?\b(?:do|task|work)\b', re.IGNORECASE), 0.7),
            ],
            'add_reminder': [
                (re.compile(r'\bremind\s+me\b', re.IGNORECASE), 1.0),
                (re.compile(r'\bset\s+(?:a\s+)?reminder\b', re.IGNORECASE), 0.95),
                (re.compile(r'\breminder\b.*\b(?:to|about)\b', re.IGNORECASE), 0.9),
            ],
            'list_tasks': [
                (re.compile(r'\b(?:show|list|display|get|tell me|what are)\b.*\b(?:tasks|todos|reminders)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:my\s+)?(?:tasks|todos|reminders)\b', re.IGNORECASE), 0.85),
                (re.compile(r'\blist\b', re.IGNORECASE), 0.6),
            ],
            'complete_task': [
                (re.compile(r'\b(?:complete|finish|done|mark|check off)\b.*\b(?:task|todo)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:task|todo)\b.*\b(?:complete|finish|done)\b', re.IGNORECASE), 0.95),
                (re.compile(r'\bdone\b.*?\b(?:task|work)\b', re.IGNORECASE), 0.7),
            ],
            'delete_task': [
                (re.compile(r'\b(?:delete|remove|cancel)\b.*\b(?:task|todo|reminder)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:task|todo)\b.*\b(?:delete|remove)\b', re.IGNORECASE), 0.95),
            ],
            'add_expense': [
                (re.compile(r'\b(?:add|spent|spent|cost|paid)\b.*\b(?:expense|money)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:expense|spent|spend)\b.*\d+', re.IGNORECASE), 0.95),
                (re.compile(r'\bi\s+(?:spent|spend|paid)\b', re.IGNORECASE), 0.85),
            ],
            'add_income': [
                (re.compile(r'\b(?:add|earned|earn|got|received)\b.*\b(?:income|money|salary)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:income|earned|salary)\b', re.IGNORECASE), 0.95),
            ],
            'check_balance': [
                (re.compile(r'\b(?:check|show|what\s+is|tell\s+me)\b.*\b(?:balance|money|total)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:balance|total|how\s+much)\b', re.IGNORECASE), 0.8),
            ],
            'add_habit': [
                (re.compile(r'\b(?:add|create|new|track)\b.*\b(?:habit)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:habit)\b.*\b(?:add|create|new)\b', re.IGNORECASE), 0.95),
            ],
            'log_habit': [
                (re.compile(r'\b(?:log|mark|complete|track)\b.*\b(?:habit)\b', re.IGNORECASE), 1.0),
            ],
            'greeting': [
                (re.compile(r'\b(?:hello|hi|hey)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:good\s+(?:morning|afternoon|evening))\b', re.IGNORECASE), 0.95),
            ],
            'goodbye': [
                (re.compile(r'\b(?:goodbye|bye|exit|quit)\b', re.IGNORECASE), 1.0),
            ],
            'help': [
                (re.compile(r'\b(?:help|commands?)\b', re.IGNORECASE), 1.0),
            ],
            'open_app': [
                (re.compile(r'\b(?:open|launch|start|run)\b.*\b(?:app|application|program)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\b(?:open|launch|start|run)\b\s+(\w+)', re.IGNORECASE), 0.85),
            ],
            'open_file': [
                (re.compile(r'\b(?:open|show)\b.*\b(?:file|document)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\bopen\b.*\.(\w+)', re.IGNORECASE), 0.9),
            ],
            'open_folder': [
                (re.compile(r'\b(?:open|show)\b.*\b(?:folder|directory)\b', re.IGNORECASE), 1.0),
                (re.compile(r'\bopen\b.*\\[^\\]*$', re.IGNORECASE), 0.85),
            ],
            'open_url': [
                (re.compile(r'\b(?:open|visit|go to|browse)\b.*\b(?:url|website|link|https?://)', re.IGNORECASE), 1.0),
                (re.compile(r'https?://[\w./]+', re.IGNORECASE), 0.95),
            ],
        }
    
    def parse(self, text: str) -> Dict[str, any]:
        """
        Parse user input and extract intent and entities with optimized matching
        
        Returns:
            Dictionary with 'intent', 'entities', 'confidence', and 'original_text'
        """
        text = text.strip()
        text_lower = text.lower()
        
        # Find matching intent with confidence scoring
        intent_scores = {}
        
        # Phase 1: Pattern matching
        for intent, patterns in self.intent_patterns.items():
            best_pattern_score = 0.0
            
            for pattern, base_confidence in patterns:
                match = pattern.search(text_lower)
                if match:
                    # Calculate enhanced confidence
                    match_length = len(match.group(0))
                    text_length = len(text_lower)
                    pattern_confidence = (match_length / max(text_length, 1)) * base_confidence
                    
                    if pattern_confidence > best_pattern_score:
                        best_pattern_score = pattern_confidence
            
            if best_pattern_score > 0:
                intent_scores[intent] = best_pattern_score
        
        # Phase 2: Keyword-based scoring (fallback/supplement)
        if not intent_scores or max(intent_scores.values()) < 0.3:
            keyword_scores = self._calculate_keyword_scores(text_lower)
            # Merge keyword scores (lower weight than pattern matching)
            for intent, score in keyword_scores.items():
                intent_scores[intent] = intent_scores.get(intent, 0) + (score * 0.5)
        
        # Phase 3: Determine best intent and confidence
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            best_confidence = min(intent_scores[best_intent], 1.0)
        else:
            best_intent = 'unknown'
            best_confidence = 0.0
        
        # Extract entities based on intent
        entities = self._extract_entities(text, text_lower, best_intent)
        
        return {
            'intent': best_intent,
            'entities': entities,
            'confidence': best_confidence,
            'original_text': text,
            'intent_scores': intent_scores  # For debugging
        }
    
    def _calculate_keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate intent scores based on keyword matching"""
        scores = {}
        
        for intent, keywords in self.keyword_weights.items():
            total_weight = 0.0
            matched_count = 0
            
            for keyword, weight in keywords.items():
                if keyword in text:
                    total_weight += weight
                    matched_count += 1
            
            if matched_count > 0:
                # Normalize score
                scores[intent] = min(total_weight / 10.0, 1.0)
        
        return scores
    
    def _extract_entities(self, text: str, text_lower: str, intent: str) -> Dict[str, any]:
        """Extract entities from text based on intent - OPTIMIZED"""
        entities = {}
        
        for entity_type, extractor in self.entity_extractors.items():
            try:
                value = extractor(text, text_lower, intent)
                if value is not None:
                    entities[entity_type] = value
            except Exception as e:
                pass  # Skip entity extraction errors
        
        return entities
    
    def _extract_title(self, text: str, text_lower: str, intent: str) -> Optional[str]:
        """Extract title, app name, file path, or URL based on intent"""
        if intent in ['create_task', 'add_reminder', 'add_habit']:
            # Remove common command prefixes and intent-specific keywords
            title = re.sub(
                r'\b(?:remind\s+me\s+to|remind\s+me|set\s+reminder|create|add|new|make|a|an|the|task|todo|reminder|alarm|schedule|set|habit|to|please|start|track)\b',
                '', text_lower, flags=re.IGNORECASE
            )
            # Remove time indicators (basic approach)
            title = re.sub(r'\b(?:in|at|on|today|tomorrow|next|seconds?|mins?|minutes?|hours?|days?|am|pm)\b.*', '', title).strip()
            
            title = re.sub(r'\s+', ' ', title).strip()
            if len(title) > 0:
                return title
            return "Reminder" if intent == 'add_reminder' else "New Habit" if intent == 'add_habit' else "Untitled Task"
        
        elif intent == 'open_app':
            # Extract app name after open/launch/start/run
            app_match = re.search(r'\b(?:open|launch|start|run)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', text_lower, re.IGNORECASE)
            if app_match:
                app_name = app_match.group(1).strip()
                # Remove trailing articles or words
                app_name = re.sub(r'\b(?:app|application|program|please)\s*$', '', app_name).strip()
                if len(app_name) > 0:
                    return app_name
            return None
        
        elif intent in ['open_file', 'open_folder']:
            # Extract file/folder path - usually after open command
            path_match = re.search(r'\b(?:open|show)\s+(?:the\s+)?(?:file|folder|directory)?\s*["\']?([^"\']+?)["\']?\s*(?:$|please|now)', text_lower, re.IGNORECASE)
            if path_match:
                path = path_match.group(1).strip()
                if len(path) > 2:
                    return path
            # Try to find file path without specific keywords
            path_match = re.search(r'([A-Za-z]:\\[^"\s]+|/[^\s"]+)', text)
            if path_match:
                return path_match.group(1).strip()
            return None
        
        elif intent == 'open_url':
            # Extract URL
            url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
            if url_match:
                return url_match.group(1).strip()
            # Try pattern after "open" or "visit"
            url_match = re.search(r'\b(?:open|visit|go to|browse)\s+(?:the\s+)?(\S+)', text_lower, re.IGNORECASE)
            if url_match:
                url = url_match.group(1).strip()
                if len(url) > 3:
                    return url
            return None
        
        return None
    
    def _extract_amount(self, text: str, text_lower: str, intent: str) -> Optional[float]:
        """Extract monetary amount"""
        if intent not in ['add_expense', 'add_income']:
            return None
        
        # Match numbers with optional currency symbols; avoid time/date tokens
        amount_match = re.search(r'(?<!:)(\d+(?:\.\d{1,2})?)\s*(?:dollar|dollars|rupee|rupees|rs|₹|\$)?', text_lower)
        if amount_match:
            return float(amount_match.group(1))
        return None
    
    def _extract_category(self, text: str, text_lower: str, intent: str) -> Optional[str]:
        """Extract expense/income category"""
        categories = ['food', 'transport', 'shopping', 'entertainment', 'bills', 'health', 'education', 'salary', 'freelance', 'investment', 'other']
        
        for category in categories:
            if category in text_lower:
                return category

        # Try to extract category after common prepositions
        if intent in ['add_expense', 'add_income']:
            match = re.search(r'\b(?:for|on|from)\s+([a-zA-Z ]+)', text_lower)
            if match:
                candidate = match.group(1).strip().split(' ')[0]
                if candidate:
                    return candidate
        
        return None
    
    def _extract_priority(self, text: str, text_lower: str, intent: str) -> str:
        """Extract task priority"""
        if 'high' in text_lower or 'urgent' in text_lower or 'important' in text_lower or 'asap' in text_lower:
            return 'high'
        elif 'low' in text_lower:
            return 'low'
        else:
            return 'medium'
    
    def _extract_date(self, text: str, text_lower: str, intent: str) -> Optional[str]:
        """Extract date and time references with improved precision"""
        now = datetime.now()
        
        # 1. Handle explicit times (e.g., "at 5pm", "at 17:00")
        time_match = re.search(r'\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text_lower)
        target_time = None
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            
            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
            
            target_time = (hour, minute)

        # 2. Handle relative offsets (e.g., "in 2 hours", "in 10 seconds")
        rel_match = re.search(r'\bin\s+(\d+)\s+(second|sec|hour|min|minute|day)s?\b', text_lower)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            if 'hour' in unit:
                return (now + timedelta(hours=amount)).strftime('%Y-%m-%d %H:%M:%S')
            elif 'min' in unit:
                return (now + timedelta(minutes=amount)).strftime('%Y-%m-%d %H:%M:%S')
            elif 'day' in unit:
                return (now + timedelta(days=amount)).strftime('%Y-%m-%d %H:%M:%S')
            elif 'second' in unit or 'sec' in unit:
                return (now + timedelta(seconds=amount)).strftime('%Y-%m-%d %H:%M:%S')

        # 3. Handle specific days
        base_date = now
        if 'tomorrow' in text_lower:
            base_date = now + timedelta(days=1)
        elif 'next week' in text_lower:
            base_date = now + timedelta(weeks=1)
        elif 'today' in text_lower:
            base_date = now
        else:
            # Check for date patterns like YYYY-MM-DD
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text_lower)
            if date_match:
                try:
                    base_date = datetime.strptime(date_match.group(0), '%Y-%m-%d')
                except: pass

        # Combine date and time
        if target_time:
            final_dt = base_date.replace(hour=target_time[0], minute=target_time[1], second=0)
            return final_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # If no specific time was mentioned, default to 9 AM if it's tomorrow/next week
        if 'tomorrow' in text_lower or 'next week' in text_lower or 'today' not in text_lower:
            return base_date.replace(hour=9, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')

        return base_date.strftime('%Y-%m-%d %H:%M:%S')
    
    def _extract_task_id(self, text: str, text_lower: str, intent: str) -> Optional[int]:
        """Extract task ID or number"""
        if intent not in ['complete_task', 'delete_task', 'log_habit']:
            return None
        
        # Look for a number, preferably after keywords like "task" or just the first number
        number_match = re.search(r'\b(?:task|item|number)?\s*#?(\d+)\b', text_lower)
        if number_match:
            return int(number_match.group(1))
        
        return None
    
    def get_response_template(self, intent: str) -> str:
        """Get a response template for an intent"""
        templates = {
            'create_task': "Task '{title}' has been created.",
            'list_tasks': "Here are your tasks:",
            'complete_task': "Task {task_id} marked as complete.",
            'delete_task': "Task {task_id} has been deleted.",
            'add_expense': "Expense of ${amount} added to {category}.",
            'add_income': "Income of ${amount} added.",
            'check_balance': "Your current balance is ${balance}.",
            'greeting': "Hello! I'm MILO, your offline assistant. How can I help you?",
            'goodbye': "Goodbye! Have a great day!",
            'help': "I can help you with tasks, finances, and habits. Try saying 'create a task' or 'check balance'.",
            'unknown': "I'm not sure I understand. Can you rephrase that?",
        }
        return templates.get(intent, "I'm processing that for you.")
    
    def get_intent_description(self, intent: str) -> str:
        """Get a human-readable description of an intent"""
        descriptions = {
            'create_task': 'Creating a new task',
            'list_tasks': 'Listing all tasks',
            'complete_task': 'Marking task as complete',
            'delete_task': 'Deleting a task',
            'add_expense': 'Adding an expense',
            'add_income': 'Adding income',
            'check_balance': 'Checking account balance',
            'add_habit': 'Adding a new habit',
            'log_habit': 'Logging habit completion',
            'greeting': 'Greeting',
            'goodbye': 'Farewell',
            'help': 'Requesting help',
            'unknown': 'Unknown command',
        }
        return descriptions.get(intent, 'Processing command')
