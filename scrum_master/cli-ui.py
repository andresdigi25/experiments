import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Label, Input, Button, Static, Footer, Header

# File to store standup responses
STANDUP_FILE = Path("standup_log.json")

class ScrumBot(App):
    """Interactive Scrum Master Bot using Textual."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    #question {
        margin-bottom: 1;
    }
    #response {
        width: 80%;
    }
    """

    def __init__(self):
        super().__init__()
        self.responses = {
            "How are you?": "",
            "What did you do yesterday?": "",
            "What do you plan to do today?": "",
            "Do you have any blockers?": "",
        }
        self.current_index = 0
        self.questions = list(self.responses.keys())

    def compose(self) -> ComposeResult:
        """Define UI components."""
        yield Header()
        yield Static("📌 **Daily Scrum Standup**", classes="header")
        yield Label(self.questions[self.current_index], id="question")
        yield Input(placeholder="Type your response...", id="response")
        yield Button("Next", id="next_btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        user_input = self.query_one("#response", Input).value.strip()

        if user_input:
            self.responses[self.questions[self.current_index]] = user_input

        self.current_index += 1

        if self.current_index < len(self.questions):
            self.update_ui()
        else:
            self.save_responses()
            self.show_summary()

    def update_ui(self):
        """Update question and input field."""
        self.query_one("#question", Label).update(self.questions[self.current_index])
        self.query_one("#response", Input).clear()

    def save_responses(self):
        """Save responses to a JSON file."""
        data = []
        if STANDUP_FILE.exists():
            with STANDUP_FILE.open("r") as f:
                data = json.load(f)

        data.append(self.responses)

        with STANDUP_FILE.open("w") as f:
            json.dump(data, f, indent=4)

    def show_summary(self):
        """Display the summary of responses."""
        # Remove all previous UI elements before showing summary
        self.query_one("#question", Label).remove()
        self.query_one("#response", Input).remove()
        self.query_one("#next_btn", Button).remove()

        self.mount(Static("✅ **Standup Complete!**\n", classes="header"))

        for question, answer in self.responses.items():
            self.mount(Label(f"🔹 {question}"))
            self.mount(Label(f"   {answer}\n"))

        self.mount(Button("Exit", id="exit_btn"))

    def on_mount(self):
        """Style the app."""
        self.query_one("#response", Input).focus()

if __name__ == "__main__":
    ScrumBot().run()
