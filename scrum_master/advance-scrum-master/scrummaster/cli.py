"""
CLI interface for the Scrum Master Bot using Textual
"""

import datetime
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual.reactive import reactive
from textual.css.query import NoMatches

# Import from our core library
from scrummaster.core import ScrumMaster


class StandupMember(Static):
    """Widget to display team member standup information"""
    
    def __init__(self, member_name: str, data: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._member_name = member_name
        self._data = data
        self.scrum_master = ScrumMaster()
    
    def compose(self) -> ComposeResult:
        with Container(classes="member-card"):
            yield Label(f"📝 {self._member_name}", classes="member-name")
            
            if self._data.get("absent", False):
                yield Label("❌ Did not participate in today's standup", classes="absent")
            else:
                # Feeling section with sentiment indicator
                feeling = self._data.get("feeling", "")
                sentiment = self.scrum_master.analyze_sentiment(feeling)
                sentiment_emoji = "😊" if sentiment > 0.2 else "😐" if sentiment > -0.2 else "😟"
                
                yield Label(f"{sentiment_emoji} {feeling}", classes="feeling")
                yield Label(f"Yesterday: {self._data.get('yesterday', '')}", classes="yesterday")
                yield Label(f"Today: {self._data.get('today', '')}", classes="today")
                
                # Blockers with highlight if present
                blockers = self._data.get("blockers", "")
                if blockers and blockers.lower() not in ["no", "none", "n/a", ""]:
                    yield Label(f"⚠️ BLOCKER: {blockers}", classes="blockers")
                else:
                    yield Label("No blockers", classes="no-blockers")


class ScrumMasterCLI(App):
    """Main Textual app for Scrum Master Bot"""
    
    CSS = """
    Screen {
        background: #2d2d2d;
        color: #ffffff;
    }

    Header {
        background: #0d8686;
        color: #ffffff;
        text-align: center;
        padding: 1;
    }

    Footer {
        background: #0d8686;
        color: #ffffff;
    }

    Button {
        margin: 1 2;
        background: #0d8686;
        color: #ffffff;
    }

    Button:hover {
        background: #14a0a0;
    }

    Button:disabled {
        background: #555555;
        color: #aaaaaa;
    }

    #main-container {
        height: 100%;
        margin: 1 2;
    }

    #menu-container {
        dock: left;
        width: 20%;
        background: #3d3d3d;
        padding: 1;
        border: solid #0d8686;
    }

    #content-container {
        dock: right;
        width: 80%;
        padding: 1;
    }

    .menu-button {
        width: 100%;
        margin: 1 0;
    }

    .title {
        text-align: center;
        text-style: bold;
        background: #3d3d3d;
        padding: 1;
    }

    .form-container {
        padding: 1;
    }

    .form-label {
        padding: 1 1 0 1;
    }

    .form-input {
        margin: 0 1 1 1;
    }

    .member-card {
        background: #3d3d3d;
        border: solid #0d8686;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .member-name {
        background: #4d4d4d;
        text-style: bold;
        text-align: center;
        padding: 1;
    }

    .feeling, .yesterday, .today, .blockers, .no-blockers, .absent {
        padding: 0 1;
        margin-top: 1;
    }

    .blockers {
        background: #8b0000;
        color: #ffffff;
        padding: 1;
        text-style: bold;
    }

    .absent {
        color: #ffcc00;
        text-style: italic;
    }

    .sentiment-positive {
        color: #00cc00;
    }

    .sentiment-neutral {
        color: #cccccc;
    }

    .sentiment-negative {
        color: #cc0000;
    }

    .hidden {
        display: none;
    }
    """
    
    TITLE = "Scrum Master Bot"
    SUB_TITLE = "CLI Interface"
    
    # Reactive variables for app state
    current_view = reactive("home")
    current_member = reactive("")
    standup_step = reactive(0)  # 0: welcome, 1: feeling, 2: yesterday, 3: today, 4: blockers, 5: summary
    
    def __init__(self, data_file="scrum_data.json"):
        super().__init__()
        self.scrum_master = ScrumMaster(data_file)
        
        # Store responses for current standup
        self.current_responses = {
            "feeling": "",
            "yesterday": "",
            "today": "",
            "blockers": ""
        }
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        
        with Horizontal(id="main-container"):
            # Menu panel
            with Vertical(id="menu-container"):
                yield Button("📊 Home", classes="menu-button", id="btn-home")
                yield Button("🏃 Run Standup", classes="menu-button", id="btn-standup")
                yield Button("👥 Manage Team", classes="menu-button", id="btn-team")
                yield Button("📝 Summary", classes="menu-button", id="btn-summary")
            
            # Content panel
            with Vertical(id="content-container"):
                # Home view
                with Container(id="home-view"):
                    yield Static("Welcome to Scrum Master Bot", classes="title")
                    yield Static("A simple NLP-powered assistant for your daily standups", id="welcome-text")
                
                # Standup view
                with Container(id="standup-view", classes="hidden"):
                    yield Static("Daily Standup", classes="title")
                    yield Static("", id="standup-prompt")
                    yield Input(placeholder="Type your response here...", id="standup-input")
                    with Horizontal():
                        yield Button("Previous", id="btn-prev-step")
                        yield Button("Next", id="btn-next-step")
                
                # Team management view
                with Container(id="team-view", classes="hidden"):
                    yield Static("Team Management", classes="title")
                    with Horizontal():
                        with Vertical(classes="form-container"):
                            yield Static("Add Team Member", classes="form-label")
                            yield Input(placeholder="Enter name", id="new-member-input")
                            yield Button("Add", id="btn-add-member")
                        
                        with Vertical(classes="form-container"):
                            yield Static("Remove Team Member", classes="form-label")
                            yield Input(placeholder="Enter name", id="remove-member-input")
                            yield Button("Remove", id="btn-remove-member")
                    
                    yield Static("Team Members:", id="team-list-label")
                    yield Static("", id="team-list")
                
                # Summary view
                with Container(id="summary-view", classes="hidden"):
                    yield Static("Standup Summary", classes="title")
                    yield Static("", id="summary-date")
                    yield Vertical(id="summary-container")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app when it's mounted"""
        self.update_view()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        if button_id == "btn-home":
            self.current_view = "home"
        elif button_id == "btn-standup":
            self.current_view = "standup"
            self.standup_step = 0
            self.current_responses = {
                "feeling": "",
                "yesterday": "",
                "today": "",
                "blockers": ""
            }
        elif button_id == "btn-team":
            self.current_view = "team"
        elif button_id == "btn-summary":
            self.current_view = "summary"
        elif button_id == "btn-add-member":
            await self.add_team_member()
        elif button_id == "btn-remove-member":
            await self.remove_team_member()
        elif button_id == "btn-next-step":
            await self.next_standup_step()
        elif button_id == "btn-prev-step":
            self.standup_step = max(0, self.standup_step - 1)
        
        self.update_view()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission events"""
        if event.input.id == "standup-input":
            await self.process_standup_input(event.value)
        elif event.input.id == "new-member-input" and event.value.strip():
            await self.add_team_member()
        elif event.input.id == "remove-member-input" and event.value.strip():
            await self.remove_team_member()
    
    def watch_current_view(self) -> None:
        """Watch for changes to current_view and update UI"""
        self.update_view()
    
    def watch_standup_step(self) -> None:
        """Watch for changes to standup_step and update UI"""
        if self.current_view == "standup":
            self.update_standup_view()
    
    def update_view(self) -> None:
        """Update UI based on current view"""
        # Hide all views
        for view_id in ["home-view", "standup-view", "team-view", "summary-view"]:
            try:
                self.query_one(f"#{view_id}").add_class("hidden")
            except NoMatches:
                pass
        
        # Show current view
        try:
            self.query_one(f"#{self.current_view}-view").remove_class("hidden")
        except NoMatches:
            pass
        
        # Update specific view content
        if self.current_view == "standup":
            self.update_standup_view()
        elif self.current_view == "team":
            self.update_team_view()
        elif self.current_view == "summary":
            self.update_summary_view()
    
    def update_standup_view(self) -> None:
        """Update standup view based on current step"""
        prompt = self.query_one("#standup-prompt")
        input_field = self.query_one("#standup-input")
        prev_button = self.query_one("#btn-prev-step")
        next_button = self.query_one("#btn-next-step")
        
        # Reset input field
        input_field.value = ""
        input_field.disabled = False
        
        # Step 0: Select team member
        if self.standup_step == 0:
            team_members = self.scrum_master.get_team_members()
            
            if not team_members:
                prompt.update("No team members found. Please add team members first.")
                input_field.disabled = True
                prev_button.disabled = True
                next_button.disabled = True
                return
            
            prompt_text = "Select a team member for standup:\n"
            for i, name in enumerate(team_members):
                prompt_text += f"{i+1}. {name}\n"
            
            prompt.update(prompt_text)
            input_field.placeholder = "Enter number or name"
            prev_button.disabled = True
            next_button.disabled = False
        
        # Step 1: How are you feeling?
        elif self.standup_step == 1:
            greeting = self.scrum_master.get_greeting()
            prompt.update(f"Hi {self.current_member}, {greeting}")
            input_field.placeholder = "I'm feeling..."
            prev_button.disabled = False
            next_button.disabled = False
        
        # Step 2: What did you do yesterday?
        elif self.standup_step == 2:
            yesterday_question = self.scrum_master.get_yesterday_question()
            prompt.update(yesterday_question)
            input_field.placeholder = "Yesterday I..."
            prev_button.disabled = False
            next_button.disabled = False
        
        # Step 3: What will you do today?
        elif self.standup_step == 3:
            today_question = self.scrum_master.get_today_question()
            prompt.update(today_question)
            input_field.placeholder = "Today I'll be working on..."
            prev_button.disabled = False
            next_button.disabled = False
        
        # Step 4: Any blockers?
        elif self.standup_step == 4:
            blocker_question = self.scrum_master.get_blocker_question()
            prompt.update(blocker_question)
            input_field.placeholder = "My blockers are... (or 'None')"
            prev_button.disabled = False
            next_button.disabled = False
        
        # Step 5: Summary
        elif self.standup_step == 5:
            summary = f"Thanks {self.current_member}! Here's your standup summary:\n\n"
            summary += f"Feeling: {self.current_responses['feeling']}\n"
            summary += f"Yesterday: {self.current_responses['yesterday']}\n"
            summary += f"Today: {self.current_responses['today']}\n"
            
            blockers = self.current_responses['blockers']
            if blockers and blockers.lower() not in ["no", "none", "n/a", ""]:
                summary += f"Blockers: ⚠️ {blockers}\n"
            else:
                summary += "Blockers: None\n"
            
            # Add some analysis
            if self.current_responses['today']:
                tasks = self.scrum_master.extract_tasks(self.current_responses['today'])
                if tasks:
                    summary += "\nI identified these tasks for today:\n"
                    for task in tasks:
                        summary += f"- {task}\n"
            
            prompt.update(summary)
            input_field.placeholder = "Type 'save' to record this standup or 'again' to start over"
            prev_button.disabled = False
            next_button.disabled = True
    
    async def process_standup_input(self, value: str) -> None:
        """Process input from standup form"""
        if not value.strip():
            return
        
        # Step 0: Select team member
        if self.standup_step == 0:
            team_members = self.scrum_master.get_team_members()
            
            # Check if input is a number
            try:
                idx = int(value) - 1
                if 0 <= idx < len(team_members):
                    self.current_member = team_members[idx]
                    self.standup_step = 1
                    return
            except ValueError:
                pass
            
            # Check if input is a name
            if value in team_members:
                self.current_member = value
                self.standup_step = 1
                return
            
            # Invalid input
            self.notify("Invalid selection. Please try again.", severity="error")
        
        # Step 1: How are you feeling?
        elif self.standup_step == 1:
            self.current_responses["feeling"] = value
            self.standup_step = 2
        
        # Step 2: What did you do yesterday?
        elif self.standup_step == 2:
            self.current_responses["yesterday"] = value
            self.standup_step = 3
        
        # Step 3: What will you do today?
        elif self.standup_step == 3:
            self.current_responses["today"] = value
            self.standup_step = 4
        
        # Step 4: Any blockers?
        elif self.standup_step == 4:
            self.current_responses["blockers"] = value
            self.standup_step = 5
        
        # Step 5: Summary
        elif self.standup_step == 5:
            if value.lower() == "save":
                # Record standup
                success = self.scrum_master.record_standup(
                    self.current_member,
                    self.current_responses["feeling"],
                    self.current_responses["yesterday"],
                    self.current_responses["today"],
                    self.current_responses["blockers"]
                )
                
                if success:
                    self.notify(f"Standup recorded for {self.current_member}", severity="information")
                else:
                    self.notify(f"Failed to record standup for {self.current_member}", severity="error")
                
                # Update summary view if that's the current view
                if self.current_view == "summary":
                    self.update_summary_view()
                
                # Reset standup
                self.standup_step = 0
                self.current_member = ""
            elif value.lower() == "again":
                # Reset to beginning of current member's standup
                self.standup_step = 1
            else:
                self.notify("Type 'save' to record or 'again' to restart", severity="warning")
    
    async def add_team_member(self) -> None:
        """Add a new team member"""
        input_field = self.query_one("#new-member-input")
        name = input_field.value.strip()
        
        if name:
            success = self.scrum_master.add_team_member(name)
            if success:
                self.notify(f"Added team member: {name}", severity="information")
                input_field.value = ""
                self.update_team_view()
            else:
                self.notify(f"Team member already exists: {name}", severity="warning")
    
    async def remove_team_member(self) -> None:
        """Remove a team member"""
        input_field = self.query_one("#remove-member-input")
        name = input_field.value.strip()
        
        if name:
            success = self.scrum_master.remove_team_member(name)
            if success:
                self.notify(f"Removed team member: {name}", severity="information")
                input_field.value = ""
                self.update_team_view()
            else:
                self.notify(f"Team member not found: {name}", severity="error")
    
    def update_team_view(self) -> None:
        """Update team management view"""
        team_list = self.query_one("#team-list")
        members = self.scrum_master.get_team_members()
        
        if not members:
            team_list.update("No team members found.")
        else:
            members_text = "\n".join([f"- {name}" for name in members])
            team_list.update(members_text)
    
    def update_summary_view(self) -> None:
        """Update summary view with today's standup data"""
        summary_container = self.query_one("#summary-container")
        summary_date = self.query_one("#summary-date")
        
        # Clear existing content
        summary_container.remove_children()
        
        # Get summary data
        summary = self.scrum_master.get_standup_summary()
        summary_date.update(f"Date: {summary['date']}")
        
        # Add member cards
        for name, data in summary["members"].items():
            summary_container.mount(StandupMember(name, data))
        
        # Add blocker warning if needed
        if summary["blockers_exist"]:
            blocker_warning = Static("⚠️ There are blockers that need attention!", classes="blockers")
            summary_container.mount(blocker_warning)
    
    async def next_standup_step(self) -> None:
        """Move to the next standup step"""
        input_field = self.query_one("#standup-input")
        value = input_field.value.strip()
        
        # Only proceed if there's input or we're just starting
        if value or self.standup_step == 0:
            await self.process_standup_input(value)
        else:
            self.notify("Please enter a response before continuing", severity="warning")


def main():
    """Run the CLI application"""
    app = ScrumMasterCLI()
    app.run()


if __name__ == "__main__":
    main()