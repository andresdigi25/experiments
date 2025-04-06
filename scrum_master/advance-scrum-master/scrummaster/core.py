"""
Core functionality for the Scrum Master Bot
This module contains the business logic and data handling
that can be reused across different interfaces (CLI, API, etc.)
"""

import json
import os
import datetime
import re
import random
from typing import Dict, List, Any, Optional, Tuple

# NLTK for text analysis
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')


class ScrumData:
    """Class to handle scrum data storage and retrieval"""
    
    def __init__(self, data_file="scrum_data.json"):
        self.data_file = data_file
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load data from JSON file or create new if it doesn't exist"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "team_members": {},
                "sprint": {
                    "current": None,
                    "history": []
                }
            }
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def add_team_member(self, name: str) -> bool:
        """Add a new team member
        
        Returns:
            bool: True if member was added, False if already exists
        """
        if name not in self.data["team_members"]:
            self.data["team_members"][name] = {
                "status": {
                    "yesterday": "",
                    "today": "",
                    "blockers": ""
                },
                "history": {}
            }
            self.save_data()
            return True
        return False
    
    def remove_team_member(self, name: str) -> bool:
        """Remove a team member
        
        Returns:
            bool: True if member was removed, False if not found
        """
        if name in self.data["team_members"]:
            del self.data["team_members"][name]
            self.save_data()
            return True
        return False
    
    def get_team_members(self) -> List[str]:
        """Get list of team members"""
        return list(self.data["team_members"].keys())
    
    def record_standup(self, name: str, feeling: str, yesterday: str, today: str, blockers: str) -> bool:
        """Record standup for a team member
        
        Returns:
            bool: True if recorded successfully, False otherwise
        """
        if name not in self.data["team_members"]:
            return False
            
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Update current status
        self.data["team_members"][name]["status"] = {
            "feeling": feeling,
            "yesterday": yesterday,
            "today": today,
            "blockers": blockers
        }
        
        # Add to history
        if "history" not in self.data["team_members"][name]:
            self.data["team_members"][name]["history"] = {}
            
        self.data["team_members"][name]["history"][today_date] = {
            "feeling": feeling,
            "yesterday": yesterday,
            "today": today,
            "blockers": blockers
        }
        
        self.save_data()
        return True
    
    def get_standup_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of standup for a specific date
        
        Args:
            date: Date in format 'YYYY-MM-DD', default is today
            
        Returns:
            Dict containing the summary information
        """
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            
        summary = {
            "date": date,
            "members": {},
            "blockers_exist": False
        }
        
        for name, data in self.data["team_members"].items():
            # Check if we have data for the specified date
            if "history" in data and date in data["history"]:
                member_data = data["history"][date]
                summary["members"][name] = member_data
                
                # Check for blockers
                blockers = member_data.get("blockers", "")
                if blockers and blockers.lower() not in ["no", "none", "n/a", ""]:
                    summary["blockers_exist"] = True
            # If no data for specified date but we're looking for today and have current status
            elif date == datetime.datetime.now().strftime('%Y-%m-%d') and "status" in data and data["status"].get("today", ""):
                summary["members"][name] = data["status"]
                
                # Check for blockers
                blockers = data["status"].get("blockers", "")
                if blockers and blockers.lower() not in ["no", "none", "n/a", ""]:
                    summary["blockers_exist"] = True
            else:
                summary["members"][name] = {"absent": True}
        
        return summary
    
    def get_member_history(self, name: str) -> Dict[str, Any]:
        """Get standup history for a specific team member
        
        Returns:
            Dict containing the member's history or empty dict if not found
        """
        if name in self.data["team_members"] and "history" in self.data["team_members"][name]:
            return self.data["team_members"][name]["history"]
        return {}


class NLPAnalyzer:
    """Class to handle NLP analysis"""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text and return score (-1 to 1)"""
        if not text:
            return 0
        return self.sia.polarity_scores(text)["compound"]
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract key words from text"""
        if not text:
            return []
            
        # Tokenize and lowercase
        words = word_tokenize(text.lower())
        
        # Remove stopwords and punctuation
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Get frequency distribution and return top N
        freq_dist = nltk.FreqDist(words)
        return [word for word, freq in freq_dist.most_common(top_n)]
    
    def extract_tasks(self, text: str) -> List[str]:
        """Extract tasks from text based on patterns"""
        if not text:
            return []
            
        # Common patterns for task descriptions
        task_patterns = [
            r'(?:need to|going to|plan to|will) (.+?)[\.|\n]',
            r'working on (.+?)[\.|\n]',
            r'focus(ing)? on (.+?)[\.|\n]',
            r'complet(?:e|ing) (.+?)[\.|\n]'
        ]
        
        tasks = []
        for pattern in task_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the captured group (the task)
                if match.group(1):
                    tasks.append(match.group(1).strip())
                elif len(match.groups()) > 1 and match.group(2):
                    tasks.append(match.group(2).strip())
        
        return tasks


class ResponseGenerator:
    """Class to generate responses for the standup conversation"""
    
    def __init__(self):
        # Greeting responses
        self.greeting_responses = [
            "Good morning! How are you feeling today?",
            "Hello! How's your day going so far?",
            "Hey there! How are you doing today?",
            "Welcome to standup! How are you?"
        ]
        
        # Question prompts
        self.yesterday_questions = [
            "What did you accomplish yesterday?",
            "What tasks did you complete yesterday?",
            "Tell me about your progress from yesterday.",
            "What did you work on in your last working day?"
        ]
        
        self.today_questions = [
            "What are you planning to work on today?",
            "What's on your agenda for today?",
            "What tasks will you be focusing on today?",
            "What do you aim to accomplish today?"
        ]
        
        self.blocker_questions = [
            "Are there any obstacles blocking your progress?",
            "Do you have any blockers I should know about?",
            "Is anything preventing you from making progress?",
            "Are there any issues or dependencies that are holding you back?"
        ]
        
        # Response variations
        self.positive_responses = [
            "Great to hear!",
            "Sounds good!",
            "Excellent!",
            "That's fantastic progress!"
        ]
        
        self.blocker_responses = [
            "I'll make note of that blocker.",
            "Thanks for sharing that blocker. We'll need to address it.",
            "I'll highlight this blocker in our summary.",
            "Let's make sure that blocker gets resolved soon."
        ]
        
        self.no_blocker_responses = [
            "Glad to hear you don't have any blockers!",
            "Great! Clear sailing ahead.",
            "No blockers is always good news.",
            "Perfect! Keep up the good momentum."
        ]
    
    def get_greeting(self) -> str:
        """Get a random greeting response"""
        return random.choice(self.greeting_responses)
    
    def get_yesterday_question(self) -> str:
        """Get a random question about yesterday's work"""
        return random.choice(self.yesterday_questions)
    
    def get_today_question(self) -> str:
        """Get a random question about today's plan"""
        return random.choice(self.today_questions)
    
    def get_blocker_question(self) -> str:
        """Get a random question about blockers"""
        return random.choice(self.blocker_questions)
    
    def get_blocker_response(self, has_blockers: bool) -> str:
        """Get response based on whether there are blockers"""
        if has_blockers:
            return random.choice(self.blocker_responses)
        else:
            return random.choice(self.no_blocker_responses)
    
    def get_positive_response(self) -> str:
        """Get a random positive response"""
        return random.choice(self.positive_responses)


class ScrumMaster:
    """Main class that coordinates the scrum master functionality"""
    
    def __init__(self, data_file="scrum_data.json"):
        self.scrum_data = ScrumData(data_file)
        self.nlp = NLPAnalyzer()
        self.response_gen = ResponseGenerator()
    
    # Team management methods
    def add_team_member(self, name: str) -> bool:
        """Add a new team member"""
        return self.scrum_data.add_team_member(name)
    
    def remove_team_member(self, name: str) -> bool:
        """Remove a team member"""
        return self.scrum_data.remove_team_member(name)
    
    def get_team_members(self) -> List[str]:
        """Get list of all team members"""
        return self.scrum_data.get_team_members()
    
    # Standup methods
    def record_standup(self, name: str, feeling: str, yesterday: str, today: str, blockers: str) -> bool:
        """Record a team member's standup"""
        return self.scrum_data.record_standup(name, feeling, yesterday, today, blockers)
    
    def get_standup_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of standup for a specific date"""
        return self.scrum_data.get_standup_summary(date)
    
    def get_member_history(self, name: str) -> Dict[str, Any]:
        """Get standup history for a specific team member"""
        return self.scrum_data.get_member_history(name)
    
    # NLP analysis methods
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text"""
        return self.nlp.analyze_sentiment(text)
    
    def extract_tasks(self, text: str) -> List[str]:
        """Extract tasks from text"""
        return self.nlp.extract_tasks(text)
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords from text"""
        return self.nlp.extract_keywords(text, top_n)
    
    # Response generation methods
    def get_greeting(self) -> str:
        """Get a greeting question"""
        return self.response_gen.get_greeting()
    
    def get_yesterday_question(self) -> str:
        """Get a question about yesterday's work"""
        return self.response_gen.get_yesterday_question()
    
    def get_today_question(self) -> str:
        """Get a question about today's plan"""
        return self.response_gen.get_today_question()
    
    def get_blocker_question(self) -> str:
        """Get a question about blockers"""
        return self.response_gen.get_blocker_question()
    
    def get_blocker_response(self, has_blockers: bool) -> str:
        """Get response based on whether there are blockers"""
        return self.response_gen.get_blocker_response(has_blockers)