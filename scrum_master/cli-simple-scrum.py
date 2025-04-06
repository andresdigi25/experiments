import datetime
import json
import os

class ScrumMasterBot:
    def __init__(self, team_data_file="team_data.json"):
        self.team_data_file = team_data_file
        self.team_data = self.load_team_data()
        
    def load_team_data(self):
        """Load team data from JSON file or create new if it doesn't exist"""
        if os.path.exists(self.team_data_file):
            with open(self.team_data_file, 'r') as f:
                return json.load(f)
        else:
            return {"team_members": {}}
    
    def save_team_data(self):
        """Save team data to JSON file"""
        with open(self.team_data_file, 'w') as f:
            json.dump(self.team_data, f, indent=4)
    
    def run_standup(self):
        """Run the daily standup meeting for all team members"""
        print("\n===== DAILY SCRUM STANDUP =====")
        print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        print("===============================\n")
        
        # Get team members or add new ones
        if not self.team_data["team_members"]:
            self.add_team_members()
        
        # Run standup for each team member
        for name in self.team_data["team_members"]:
            self.individual_standup(name)
            
        print("\n===== STANDUP COMPLETE =====")
        print("All responses have been saved.")
        
    def add_team_members(self):
        """Add team members to the bot"""
        print("Let's add team members to the standup:")
        while True:
            name = input("Enter team member name (or 'done' to finish): ")
            if name.lower() == 'done':
                break
            self.team_data["team_members"][name] = {
                "yesterday": "",
                "today": "",
                "blockers": ""
            }
        self.save_team_data()
    
    def individual_standup(self, name):
        """Run standup for an individual team member"""
        print(f"\n----- Standup for {name} -----")
        
        # Ask the standard scrum questions
        print(f"Hi {name}, how are you today?")
        feeling = input("> ")
        
        print("\nWhat did you accomplish yesterday?")
        yesterday = input("> ")
        
        print("\nWhat do you plan to do today?")
        today = input("> ")
        
        print("\nDo you have any blockers?")
        blockers = input("> ")
        
        # Save the responses
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        if "history" not in self.team_data["team_members"][name]:
            self.team_data["team_members"][name]["history"] = {}
            
        self.team_data["team_members"][name]["history"][today_date] = {
            "feeling": feeling,
            "yesterday": yesterday,
            "today": today,
            "blockers": blockers
        }
        
        # Update current status
        self.team_data["team_members"][name]["yesterday"] = yesterday
        self.team_data["team_members"][name]["today"] = today
        self.team_data["team_members"][name]["blockers"] = blockers
        
        self.save_team_data()
        
        # Provide feedback based on blockers
        if blockers.lower() not in ["no", "none", "n/a", ""]:
            print(f"\nI've noted your blocker: '{blockers}'")
            print("This will be highlighted in the summary report.")
    
    def generate_summary(self):
        """Generate a summary of today's standup"""
        today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"\n===== STANDUP SUMMARY FOR {today_date} =====")
        
        # Track blockers to highlight
        blockers_exist = False
        
        for name, data in self.team_data["team_members"].items():
            if "history" in data and today_date in data["history"]:
                print(f"\n{name}:")
                print(f"  Yesterday: {data['history'][today_date]['yesterday']}")
                print(f"  Today: {data['history'][today_date]['today']}")
                
                # Highlight blockers
                blockers = data['history'][today_date]['blockers']
                if blockers.lower() not in ["no", "none", "n/a", ""]:
                    print(f"  BLOCKER: {blockers}")
                    blockers_exist = True
                else:
                    print("  Blockers: None")
            else:
                print(f"\n{name}: Did not participate in today's standup.")
        
        # Final notes
        if blockers_exist:
            print("\nNOTE: There are blockers that need attention!")

if __name__ == "__main__":
    bot = ScrumMasterBot()
    
    while True:
        print("\nSCRUM MASTER BOT")
        print("1. Run Daily Standup")
        print("2. Add Team Members")
        print("3. Generate Summary Report")
        print("4. Exit")
        
        choice = input("Select an option: ")
        
        if choice == '1':
            bot.run_standup()
        elif choice == '2':
            bot.add_team_members()
        elif choice == '3':
            bot.generate_summary()
        elif choice == '4':
            print("Exiting Scrum Master Bot. Goodbye!")
            break
        else:
            print("Invalid option, please try again.")