import json
import datetime

def ask_question(question):
    response = input(question + " ")
    return response

def collect_standup():
    print("\nDaily Standup - Scrum Master Bot\n")
    standup_data = {
        "date": str(datetime.date.today()),
        "status": ask_question("How are you?"),
        "yesterday": ask_question("What did you do yesterday?"),
        "today": ask_question("What do you plan to do today?"),
        "blockers": ask_question("Do you have any blockers?"),
    }
    
    save_standup(standup_data)
    print("\nStandup recorded successfully!")

def save_standup(data, filename="standup_log.json"):
    try:
        with open(filename, "r") as file:
            logs = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    logs.append(data)
    with open(filename, "w") as file:
        json.dump(logs, file, indent=4)

def view_standup_log(filename="standup_log.json"):
    try:
        with open(filename, "r") as file:
            logs = json.load(file)
            for entry in logs:
                print(f"\nDate: {entry['date']}\nStatus: {entry['status']}\nYesterday: {entry['yesterday']}\nToday: {entry['today']}\nBlockers: {entry['blockers']}\n{'-'*40}")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No standup logs found.")

if __name__ == "__main__":
    while True:
        print("\n1. Start Standup\n2. View Logs\n3. Exit")
        choice = input("Choose an option: ")
        
        if choice == "1":
            collect_standup()
        elif choice == "2":
            view_standup_log()
        elif choice == "3":
            print("Exiting... Have a great day!")
            break
        else:
            print("Invalid option, please try again.")
