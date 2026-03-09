import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import logging

class MiloSuggestionEngine:
    def __init__(self, model_path="data/milo_ml_model.pkl"):
        self.logger = logging.getLogger("MILO.ML")
        self.model_path = model_path
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.action_encoder = LabelEncoder()
        self.is_trained = False
        
        # Mapping for LastAction string to code
        self.action_mapping = {
            'none': 0,
            'wake_up': 1,
            'email_check': 2,
            'lunch': 3,
            'meeting': 4,
            'dinner': 5,
            'movie': 6,
            'work': 7,
            'exercise': 8
        }
        
    def generate_training_data(self):
        """
        Simulate historical routine. In a future update, this will pull from 
        the MILO database activity logs.
        """
        # [Hour, DayOfWeek, PendingTasks, LastAction, ChosenAction]
        data = [
            # Mornings (Mon-Fri) - Deep Work
            [8, 0, 5, 'wake_up', 'Deep Work'],
            [9, 1, 4, 'email_check', 'Deep Work'],
            [8, 2, 6, 'wake_up', 'Deep Work'],
            [9, 3, 3, 'email_check', 'Deep Work'],
            [8, 4, 7, 'wake_up', 'Deep Work'],
            
            # Weekends - Relaxation/Reading
            [8, 5, 2, 'wake_up', 'Reading'],
            [9, 6, 1, 'wake_up', 'Yoga'],
            
            # Afternoons - Admin/Emails
            [14, 0, 8, 'lunch', 'Admin Work'],
            [15, 1, 5, 'meeting', 'Code Review'],
            [14, 2, 7, 'lunch', 'Quick Email Catch-up'],
            
            # Evenings - Finances/Habits
            [19, 0, 2, 'dinner', 'Review Finances'],
            [20, 1, 1, 'dinner', 'Log Habit'],
            [19, 2, 3, 'dinner', 'Review Finances'],
            [21, 3, 0, 'movie', 'Plan Next Day'],
            [20, 4, 1, 'dinner', 'Log Habit'],
            [22, 6, 0, 'none', 'Plan Next Week']
        ]
        
        df = pd.DataFrame(data, columns=['Hour', 'DayOfWeek', 'PendingTasks', 'LastAction', 'ChosenAction'])
        return df

    def train_model(self):
        """Trains the Random Forest on historical or synthetic data."""
        try:
            self.logger.info("Training MILO Suggestion Engine...")
            df = self.generate_training_data()
            
            # Convert LastAction strings to numeric codes using the mapping
            df['LastAction_Code'] = df['LastAction'].map(lambda x: self.action_mapping.get(x, 0))
            
            # Fit encoder on the target actions
            self.action_encoder.fit(df['ChosenAction'])
            df['Target'] = self.action_encoder.transform(df['ChosenAction'])
            
            # Features: Hour, DayOfWeek, PendingTasks, LastActionCode
            X = df[['Hour', 'DayOfWeek', 'PendingTasks', 'LastAction_Code']]
            y = df['Target']
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Save model and encoder
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump((self.model, self.action_encoder), f)
                
            self.logger.info("Model trained and saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to train model: {e}")

    def load_model(self):
        """Load the trained model from disk if it exists."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model, self.action_encoder = pickle.load(f)
                self.is_trained = True
                return True
            except:
                return False
        return False

    def get_smart_suggestion(self, current_pending_tasks, last_action_str='none'):
        """
        Inferences the model based on the current time and user context.
        """
        if not self.is_trained:
            if not self.load_model():
                self.train_model()

        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()
        last_action_code = self.action_mapping.get(last_action_str, 0)
        
        # Prepare context vector as a DataFrame to keep feature names consistent with training
        current_context = pd.DataFrame(
            [[current_hour, current_day, current_pending_tasks, last_action_code]],
            columns=['Hour', 'DayOfWeek', 'PendingTasks', 'LastAction_Code']
        )
        
        try:
            # Predict probabilities
            probabilities = self.model.predict_proba(current_context)[0]
            best_action_index = np.argmax(probabilities)
            confidence = probabilities[best_action_index] * 100
            
            # Decode action
            suggested_action = self.action_encoder.inverse_transform([best_action_index])[0]
            
            return {
                "suggestion": suggested_action,
                "confidence": round(confidence, 1),
                "context": f"Hour: {current_hour}, Day: {current_day}, Tasks: {current_pending_tasks}"
            }
        except Exception as e:
            self.logger.error(f"Inference error: {e}")
            return {
                "suggestion": "Keep up the good work!",
                "confidence": 0,
                "context": "Default suggestion"
            }
