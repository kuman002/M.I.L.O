"""
MILO Assistant - Main command handler
Integrates all modules and handles user commands
"""

from typing import Dict, Callable, Optional
from datetime import datetime, timedelta
from database.database import Database
from managers.task_manager import TaskManager
from managers.finance_manager import FinanceManager
from managers.habit_manager import HabitManager
from managers.app_launcher import AppLauncher
from managers.suggestion_engine import MiloSuggestionEngine
from nlp.nlp_parser import NLPParser
from voice.text_to_speech import TextToSpeech
from automation.rpa_service import RPAService
from integrations.google_service import GoogleService


class MILOAssistant:
    """Main assistant class that handles commands and coordinates modules"""
    
    def __init__(self, database: Database, tts: Optional[TextToSpeech] = None):
        """
        Initialize MILO assistant

        Args:
            database: Shared Database instance
            tts: Optional shared TextToSpeech instance. If not provided,
                 a new one will be created.
        """
        self.db = database
        self.task_manager = TaskManager(database)
        self.finance_manager = FinanceManager(database)
        self.habit_manager = HabitManager(database)
        self.app_launcher = AppLauncher()
        self.parser = NLPParser()
        # Use shared TTS instance so only one pyttsx3 engine is active
        self.tts = tts or TextToSpeech()
        
        # New automation services
        self.rpa = RPAService()
        self.google = GoogleService()
        self.suggestion_engine = MiloSuggestionEngine()
        
        self.last_action = 'none'
        self.on_response_callback: Optional[Callable[[str], None]] = None
    
    def process_command(self, text: str) -> Dict:
        """
        Process user command and return response
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with response information
        """
        # Parse the command
        parsed = self.parser.parse(text)
        intent = parsed['intent']
        entities = parsed['entities']
        
        # Track last action for ML context
        if intent not in ['unknown', 'chitchat', 'greeting', 'help']:
            self.last_action = intent
        
        response = {
            'intent': intent,
            'message': '',
            'data': None,
            'success': False
        }
        
        try:
            # Handle different intents
            if intent == 'create_task':
                title = entities.get('title', 'Untitled Task')
                priority = entities.get('priority', 'medium')
                due_date = entities.get('date')

                # Defensive clarification loop: do not save when a critical entity is ambiguous.
                if entities.get('missing_entity') == 'meridiem':
                    response['message'] = entities.get('clarification_prompt') or "Did you mean AM or PM for that time?"
                    response['success'] = False
                    response['data'] = {
                        'requires_clarification': True,
                        'missing_entity': 'meridiem',
                        'title': title,
                        'priority': priority,
                        'proposed_date': due_date,
                    }
                    return response
                
                result = self.task_manager.create_task(
                    title=title,
                    due_date=due_date,
                    priority=priority
                )
                
                if result['success']:
                    date_info = f" for {due_date}" if due_date else ""
                    response['message'] = f"OK, I've added '{title}'{date_info} to your tasks."
                else:
                    response['message'] = result['message']
                    
                response['success'] = result['success']
                response['data'] = result
            
            elif intent == 'list_tasks':
                tasks = self.task_manager.get_pending_tasks()
                if tasks:
                    task_list = "\n".join([
                        f"{i+1}. {task['title']} (Priority: {task['priority']})"
                        for i, task in enumerate(tasks[:10])
                    ])
                    response['message'] = f"Here are your tasks:\n{task_list}"
                else:
                    response['message'] = "You have no pending tasks."
                response['success'] = True
                response['data'] = tasks
            
            elif intent == 'complete_task':
                task_id = entities.get('task_id')
                if task_id:
                    result = self.task_manager.complete_task(task_id)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify which task to complete (e.g., 'complete task 1')."
                    response['success'] = False
            
            elif intent == 'delete_task':
                task_id = entities.get('task_id')
                if task_id:
                    result = self.task_manager.delete_task(task_id)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify which task to delete (e.g., 'delete task 1')."
                    response['success'] = False
            
            elif intent == 'add_expense':
                amount = entities.get('amount')
                category = entities.get('category', 'other')
                
                if amount:
                    result = self.finance_manager.add_expense(category, amount)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the amount (e.g., 'add expense 50 dollars')."
                    response['success'] = False
            
            elif intent == 'add_income':
                amount = entities.get('amount')
                category = entities.get('category', 'income')
                
                if amount:
                    result = self.finance_manager.add_income(category, amount)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the amount (e.g., 'add income 1000 dollars')."
                    response['success'] = False
            
            elif intent == 'check_balance':
                balance = self.finance_manager.get_balance()
                summary = self.finance_manager.get_summary()
                response['message'] = f"Current balance: {balance:.2f}\nTotal income: {summary['total_income']:.2f}\nTotal expenses: {summary['total_expenses']:.2f}"
                response['success'] = True
                response['data'] = summary
            
            elif intent == 'add_habit':
                name = entities.get('title', text)
                if name:
                    name = name.strip()
                    if not name:
                        name = 'New Habit'
                    
                    result = self.habit_manager.add_habit(name)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the habit name."
                    response['success'] = False
            
            elif intent == 'log_habit':
                # Get first habit for now (can be improved)
                habits = self.habit_manager.get_habits()
                if habits:
                    result = self.habit_manager.log_habit_completion(habits[0]['id'])
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "No habits found. Please add a habit first."
                    response['success'] = False
            
            elif intent == 'add_reminder':
                message = entities.get('title', '').strip() or "Reminder"
                reminder_dt = entities.get('date')
                if not reminder_dt:
                    reminder_dt = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30)
                    reminder_dt = reminder_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Ensure reminders table exists and insert
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message TEXT NOT NULL,
                        datetime TEXT NOT NULL,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                cursor.execute(
                    "INSERT INTO reminders (message, datetime, status) VALUES (?, ?, ?)",
                    (message, reminder_dt, 'pending')
                )
                self.db.conn.commit()
                response['message'] = f"Reminder set: {message}"
                response['success'] = True
            
            elif intent == 'greeting':
                response['message'] = "Hello! I'm MILO, your offline assistant. How can I help you today?"
                response['success'] = True
            
            elif intent == 'time_query':
                from datetime import datetime
                current_time = datetime.now().strftime("%I:%M %p")
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                response['message'] = f"The current time is {current_time} on {current_date}."
                response['success'] = True
            
            elif intent == 'goodbye':
                response['message'] = "Goodbye! Have a great day!"
                response['success'] = True
            
            elif intent == 'help':
                help_text = """I can help you with:
- Tasks: Create, list, complete, or delete tasks
- Finances: Add expenses/income, check balance
- Habits: Track habits and view statistics
- Applications: Open apps, files, folders, or websites
- Computer Use: Type text, search in active browser, click text on screen
- Say 'create a task' or 'check balance' to get started"""
                response['message'] = help_text
                response['success'] = True
            
            elif intent == 'open_app':
                app_name = entities.get('app_name', '')
                print(f"[Assistant] Opening app: '{app_name}'")  # Debug log
                if app_name:
                    result = self.app_launcher.open_app(app_name)
                    print(f"[AppLauncher] Result: {result}")  # Debug log
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    apps = ', '.join(self.app_launcher.get_common_apps()[:8])
                    response['message'] = f"Available apps: {apps}..."
                    response['success'] = False
            
            elif intent == 'open_file':
                file_path = entities.get('title', '')
                if file_path:
                    result = self.app_launcher.open_file(file_path)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the file path."
                    response['success'] = False
            
            elif intent == 'open_folder':
                folder_path = entities.get('title', '')
                if folder_path:
                    result = self.app_launcher.open_folder(folder_path)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the folder path."
                    response['success'] = False
            
            elif intent == 'open_url':
                url = entities.get('title', '')
                if url:
                    result = self.app_launcher.open_url(url)
                    response['message'] = result['message']
                    response['success'] = result['success']
                else:
                    response['message'] = "Please specify the website."
                    response['success'] = False
            
            elif intent == 'google_search':
                query = entities.get('query', '')
                if query:
                    import webbrowser
                    import urllib.parse
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                    webbrowser.open(search_url)
                    response['message'] = f"Searching Google for: {query}"
                    response['success'] = True
                else:
                    response['message'] = "What would you like me to search for?"
                    response['success'] = False

            elif intent == 'computer_type':
                typed_text = entities.get('text', '').strip()
                if typed_text:
                    result = self.rpa.type_text(typed_text)
                    response['message'] = result.get('message', 'Typing completed.')
                    response['success'] = bool(result.get('success'))
                    response['data'] = result
                else:
                    response['message'] = "Please tell me what to type."
                    response['success'] = False

            elif intent == 'computer_search':
                query = entities.get('query', '').strip()
                if query:
                    result = self.rpa.search_in_browser_context(query)
                    response['message'] = result.get('message', 'Search completed.')
                    response['success'] = bool(result.get('success'))
                    response['data'] = result
                else:
                    response['message'] = "Please tell me what to search for."
                    response['success'] = False

            elif intent == 'computer_click_text':
                target_text = entities.get('target_text', '').strip()
                if target_text:
                    result = self.rpa.click_text(target_text)
                    response['message'] = result.get('message', 'Click action completed.')
                    response['success'] = bool(result.get('success'))
                    response['data'] = result
                else:
                    response['message'] = "Please tell me which text to click."
                    response['success'] = False

            elif intent == 'setup_env':
                msg = self.rpa.setup_coding_environment()
                response['message'] = msg
                response['success'] = True

            elif intent == 'play_music':
                msg = self.rpa.play_spotify_lofi()
                response['message'] = msg
                response['success'] = True

            elif intent == 'read_emails':
                result = self.google.get_unread_emails_summary()
                response['message'] = result['message']
                response['success'] = result['success']
                response['data'] = result.get('emails', [])

            elif intent == 'next_slide':
                msg = self.rpa.next_slide()
                response['message'] = msg
                response['success'] = True

            elif intent == 'prev_slide':
                msg = self.rpa.prev_slide()
                response['message'] = msg
                response['success'] = True
            
            elif intent == 'chitchat':
                # Friendly responses for casual conversation
                chitchat_responses = [
                    "I'm doing well, thanks for asking! How can I assist you?",
                    "I'm here and ready to help!",
                    "Not much, just waiting to help you with tasks, finances, or habits!",
                    "I'm MILO (Managing Information & Lifestyle Optimizer), your assistant. What would you like to do?"
                ]
                import random
                response['message'] = random.choice(chitchat_responses)
                response['success'] = True
            
            elif intent == 'unknown':
                response['message'] = "I heard you, but I'm not sure what you want me to do. Try commands like:\n• 'Add task'\n• 'Check balance'\n• 'Add expense'\n• Say 'help' for more options."
                response['success'] = False
            
            else:
                response['message'] = "I'm not sure I understand. Try saying 'help' for available commands."
                response['success'] = False
        
        except Exception as e:
            response['message'] = f"Sorry, I encountered an error: {str(e)}"
            response['success'] = False
        
        # Trigger callback if set
        if self.on_response_callback:
            self.on_response_callback(response['message'])
        
        # Speak response (TextToSpeech handles worker auto-recovery internally)
        if self.tts and response['message']:
            try:
                self.tts.speak(response['message'])
            except Exception as e:
                print(f"[TTS] Speak failed: {e}")
        
        return response
    
    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard display"""
        pending_tasks = self.task_manager.get_pending_tasks()
        upcoming_tasks = self.task_manager.get_upcoming_tasks(7)
        finance_summary = self.finance_manager.get_summary()
        habits = self.habit_manager.get_all_habit_stats()
        patterns = self.habit_manager.analyze_patterns()
        
        # Get ML recommendation
        recommendation = self.suggestion_engine.get_smart_suggestion(
            current_pending_tasks=len(pending_tasks),
            last_action_str=self.last_action
        )
        
        return {
            'pending_tasks_count': len(pending_tasks),
            'upcoming_tasks': upcoming_tasks[:5],
            'balance': finance_summary['balance'],
            'total_expenses': finance_summary['total_expenses'],
            'habits': habits,
            'suggestions': patterns.get('suggestions', []),
            'ml_recommendation': recommendation
        }
