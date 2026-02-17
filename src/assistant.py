"""
MILO Assistant - Main command handler
Integrates all modules and handles user commands
"""

from typing import Dict, Callable, Optional
from datetime import datetime, timedelta
from database import Database
from managers.task_manager import TaskManager
from managers.finance_manager import FinanceManager
from managers.habit_manager import HabitManager
from managers.app_launcher import AppLauncher
from nlp.nlp_parser import NLPParser
from voice.text_to_speech import TextToSpeech


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
            
            elif intent == 'goodbye':
                response['message'] = "Goodbye! Have a great day!"
                response['success'] = True
            
            elif intent == 'help':
                help_text = """I can help you with:
- Tasks: Create, list, complete, or delete tasks
- Finances: Add expenses/income, check balance
- Habits: Track habits and view statistics
- Applications: Open apps, files, folders, or websites
- Say 'create a task' or 'check balance' to get started"""
                response['message'] = help_text
                response['success'] = True
            
            elif intent == 'open_app':
                app_name = entities.get('title', '')
                if app_name:
                    result = self.app_launcher.open_app(app_name)
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
            
            else:
                response['message'] = "I'm not sure I understand. Try saying 'help' for available commands."
                response['success'] = False
        
        except Exception as e:
            response['message'] = f"Sorry, I encountered an error: {str(e)}"
            response['success'] = False
        
        # Trigger callback if set
        if self.on_response_callback:
            self.on_response_callback(response['message'])
        
        # Speak response if TTS is available
        if self.tts.is_available() and response['message']:
            self.tts.speak(response['message'])
        
        return response
    
    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard display"""
        pending_tasks = self.task_manager.get_pending_tasks()
        upcoming_tasks = self.task_manager.get_upcoming_tasks(7)
        finance_summary = self.finance_manager.get_summary()
        habits = self.habit_manager.get_all_habit_stats()
        patterns = self.habit_manager.analyze_patterns()
        
        return {
            'pending_tasks_count': len(pending_tasks),
            'upcoming_tasks': upcoming_tasks[:5],
            'balance': finance_summary['balance'],
            'total_expenses': finance_summary['total_expenses'],
            'habits': habits,
            'suggestions': patterns.get('suggestions', [])
        }
