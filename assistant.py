# assistant.py
import argparse
import json
import sys
import random
import os
import requests
from datetime import datetime

# Try to import and initialize pyttsx3; if it fails, keep a fallback
try:
    import pyttsx3
    engine = pyttsx3.init()
except Exception:
    engine = None

def speak(text):
    """Speak text if TTS engine is available. Always print too."""
    print(text)
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            # If TTS fails, silently ignore and keep printed output
            print(f"TTS Error: {e}")
            pass

# ---------------- FILE PATHS ----------------
DATA_DIR = "data"
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")
HISTORY_FILE = os.path.join(DATA_DIR, "dictionary_history.json")

def ensure_file(path):
    """Create file with [] if missing or invalid."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return
    # if file exists but empty or invalid JSON, overwrite with []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content == "":
                with open(path, "w", encoding="utf-8") as fw:
                    json.dump([], fw)
            else:
                json.loads(content)
    except Exception:
        with open(path, "w", encoding="utf-8") as fw:
            json.dump([], fw)

# Ensure data directory and files exist
os.makedirs(DATA_DIR, exist_ok=True)
for p in (TASKS_FILE, NOTES_FILE, REMINDERS_FILE, HISTORY_FILE):
    ensure_file(p)

# ---------------- HELPERS ----------------
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------- TASKS ----------------
def load_tasks():
    return load_json(TASKS_FILE)

def save_tasks(tasks):
    save_json(TASKS_FILE, tasks)

def get_new_id(tasks):
    return max([t.get("id", 0) for t in tasks], default=0) + 1

def add_task(value):
    """
    Format:
      addtask "Task name;YYYY-MM-DD;priority"
    Example:
      addtask "Finish assignment;2025-08-21;high"
    """
    parts = value.split(";")
    task_name = parts[0].strip()
    due_date = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    priority = parts[2].strip().lower() if len(parts) > 2 and parts[2].strip() else "medium"

    tasks = load_tasks()
    task = {
        "id": get_new_id(tasks),
        "task": task_name,
        "status": "pending",
        "priority": priority,
        "due": due_date
    }
    tasks.append(task)
    save_tasks(tasks)
    speak(f" Task added: {task_name}{' (due ' + due_date + ')' if due_date else ''} with priority {priority}.")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        speak(" No tasks found.")
        return

    print("\n📋 Your tasks:")
    speech_text = "You have the following tasks. "
    for t in tasks:
        status = "[✔]" if t.get("status") == "done" else "[ ]"
        prio_icon = "🔥" if t.get("priority") == "high" else "⚡" if t.get("priority") == "medium" else "🟢"
        details = []
        if t.get("priority"):
            details.append(f"{prio_icon} {t['priority'].capitalize()}")
        if t.get("due"):
            details.append(f"📅 {t['due']}")
        details_text = ", ".join(details)
        details_text = f" ({details_text})" if details_text else ""
        print(f"{t['id']}. {status} {t.get('task')}{details_text}")

        # Build a single string for TTS
        status_text = "done" if t.get("status") == "done" else "not done"
        speech_text += f"Task {t['id']}: {t.get('task')}. Status: {status_text}. "
        if t.get('priority'):
            speech_text += f"Priority: {t.get('priority')}. "
        if t.get('due'):
            speech_text += f"Due on {t.get('due')}. "
    speak(speech_text)

def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "done"
            save_tasks(tasks)
            speak(f" Task {task_id} marked as complete.")
            return
    speak("❗ Invalid task number.")

def remove_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(new_tasks) != len(tasks):
        save_tasks(new_tasks)
        speak(f" Removed task {task_id}.")
    else:
        speak("❗ Invalid task number.")

# ---------------- NOTES ----------------
def load_notes():
    return load_json(NOTES_FILE)

def save_notes(notes):
    save_json(NOTES_FILE, notes)

def add_note(note):
    notes = load_notes()
    notes.append(note)
    save_notes(notes)
    speak(f" Note added: {note}")

def show_notes():
    notes = load_notes()
    if not notes:
        speak(" No notes found.")
        return
    
    print(" Your notes:")
    speech_text = "You have the following notes. "
    for i, note in enumerate(notes, 1):
        print(f"{i}. {note}")
        speech_text += f"Note {i}: {note}. "
    speak(speech_text)

def search_notes(keyword):
    notes = load_notes()
    found = [n for n in notes if keyword.lower() in n.lower()]
    if found:
        print(f"Found {len(found)} note(s) containing '{keyword}':")
        speech_text = f"I found {len(found)} note(s) containing the keyword {keyword}. "
        for i, n in enumerate(found, 1):
            print(f"{i}. {n}")
            speech_text += f"Note {i}: {n}. "
        speak(speech_text)
    else:
        speak(" No matching notes found.")

# ---------------- REMINDERS ----------------
def load_reminders():
    return load_json(REMINDERS_FILE)

def save_reminders(reminders):
    save_json(REMINDERS_FILE, reminders)

def add_reminder(text, date_str, time_str):
    try:
        reminder_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        speak(" Invalid date/time format. Use YYYY-MM-DD HH:MM")
        return
    reminders = load_reminders()
    reminders.append({"text": text, "time": reminder_time.strftime("%Y-%m-%d %H:%M")})
    save_reminders(reminders)
    speak(f" Reminder set: '{text}' at {reminder_time.strftime('%Y-%m-%d %H:%M')}")

def show_reminders():
    reminders = load_reminders()
    if not reminders:
        speak(" No reminders found.")
        return

    print(" Your reminders:")
    speech_text = "You have the following reminders. "
    for i, r in enumerate(reminders, 1):
        print(f"{i}. {r.get('text')} — {r.get('time')}")
        speech_text += f"Reminder {i}: {r.get('text')} at {r.get('time')}. "
    speak(speech_text)

def check_reminders():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    reminders = load_reminders()
    due = [r for r in reminders if r.get("time") == now]
    if due:
        for r in due:
            speak(f" REMINDER: {r.get('text')}")
    else:
        speak(" No reminders right now.")

# ---------------- WEATHER ----------------
WEATHER_API_KEY = "d9fe5121d3f9d2bc47998b992ac42c8e"
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        cod = data.get("cod")
        if cod == 200 or str(cod) == "200":
            name = data.get("name")
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            text = f" Weather in {name}: {temp}°C, {desc}"
            speak(text)
        else:
            speak(f" Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        speak(f" Could not fetch weather: {e}")

# ---------------- DICTIONARY ----------------
def save_word_to_history(word):
    history = load_json(HISTORY_FILE)
    history.append({"word": word, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_json(HISTORY_FILE, history)

def define_word(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            speak(f"❌ Could not find definition for '{word}'.")
            return
        data = r.json()
        print(f"\n📚 Definitions for '{word}':\n")
        first_def = None
        speech_text = f"Definitions for {word}. "
        for meaning in data[0].get("meanings", []):
            part = meaning.get("partOfSpeech", "")
            print(f"🔹 {part.capitalize()}:")
            speech_text += f"As a {part}, "
            for idx, d in enumerate(meaning.get("definitions", []), 1):
                definition = d.get("definition", "")
                if not first_def:
                    first_def = definition
                print(f"   {idx}. {definition}")
                speech_text += f"Definition {idx}: {definition}. "
                if d.get("example"):
                    print(f"      💡 Example: {d.get('example')}")
                    speech_text += f"For example: {d.get('example')}. "
            print()
        save_word_to_history(word)
        speak(speech_text)
    except Exception as e:
        speak(f"❌ Error fetching definition: {e}")

# ---------------- NEWS ----------------
NEWS_API_KEY = "2dc15d7040ab4400aaaa26629fedd979"
def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("status") != "ok":
            speak(f" Error: {data.get('message', 'Unknown error')}")
            return
        articles = data.get("articles", [])
        if not articles:
            speak(" No news found.")
            return

        print("\n Top Headlines:\n")
        # Build one string so TTS reads all 5 headlines
        headlines_text = "Here are the top 5 news headlines: "
        for i, a in enumerate(articles, 1):
            title = a.get("title", "No title")
            url = a.get("url", "")
            print(f"{i}. {title}")
            if url:
                print(f"   🔗 {url}")
            print()
            headlines_text += f"Headline {i}: {title}. "
        speak(headlines_text)

    except Exception as e:
        speak(f" Could not fetch news: {e}")

# ---------------- NEW FEATURE: RANDOM FACT ----------------
FACTS = [
    "A group of flamingos is called a flamboyance.",
    "The shortest war in history lasted only 38 to 45 minutes.",
    "Bears are the only land animals that cannot jump.",
    "The average person walks the equivalent of five times around the world in their lifetime.",
    "It is impossible for most people to lick their own elbow.",
    "The total weight of all ants on Earth is estimated to be about the same as the total weight of all humans.",
    "The world's smallest mammal is the bumblebee bat.",
    "A crocodile cannot stick its tongue out.",
    "The world's largest desert is Antarctica.",
    "Hot water will turn into ice faster than cold water."
]

def get_random_fact():
    """Selects and speaks a random fact from the list."""
    fact = random.choice(FACTS)
    speak(f"Here's a fun fact for you: {fact}")

# ---------------- MAIN ----------------
def main():
    print("Hello Abdul Waheed! How can I help you today? Type 'bye' to exit.")
    while True:
        user_input = input("You: ").strip().lower()

        if any(word in user_input for word in ["bye", "exit", "quit", "goodbye"]):
            speak("Goodbye Abdul Waheed! Have a great day!")
            break

        # GREETING
        elif any(word in user_input for word in ["hi", "hello", "hey", "greet"]):
            speak("Hello! Abdul Waheed, how can I help you today?")
        
        # TASK MANAGEMENT
        elif user_input.startswith("add task"):
            parts = user_input.split(";")
            task_info = parts[0].replace("add task", "", 1).strip()
            add_task_input = task_info
            if len(parts) > 1:
                add_task_input += ";" + ";".join(parts[1:])
            
            if add_task_input:
                add_task(add_task_input)
            else:
                speak("❗ Please provide a task in the format: \"add task My Task;YYYY-MM-DD;priority\"")
        
        elif any(word in user_input for word in ["show tasks", "list tasks", "my tasks", "what are my tasks"]):
            show_tasks()
            
        elif user_input.startswith("complete task") or user_input.startswith("done"):
            try:
                task_id = int(''.join(filter(str.isdigit, user_input)))
                complete_task(task_id)
            except ValueError:
                speak("❗ Please provide the task ID. Example: 'done task 2' or 'complete 3'")
        
        elif user_input.startswith("remove task") or user_input.startswith("delete task"):
            try:
                task_id = int(''.join(filter(str.isdigit, user_input)))
                remove_task(task_id)
            except ValueError:
                speak("❗ Please provide the task ID. Example: 'remove task 2' or 'delete 3'")

        # NOTES
        elif user_input.startswith("add note"):
            note = user_input.replace("add note", "", 1).strip()
            if note:
                add_note(note)
            else:
                speak("❗ Please tell me what note to add.")
        elif any(word in user_input for word in ["show notes", "list notes", "my notes"]):
            show_notes()
        elif user_input.startswith("search note"):
            keyword = user_input.replace("search note", "", 1).strip()
            if keyword:
                search_notes(keyword)
            else:
                speak("❗ Please provide a keyword to search.")

        # REMINDERS
        elif user_input.startswith("add reminder"):
            parts = user_input.split(";")
            if len(parts) == 3:
                add_reminder(parts[0].replace("add reminder", "", 1).strip(), parts[1].strip(), parts[2].strip())
            else:
                speak("❗ Use format: 'add reminder;Text;YYYY-MM-DD;HH:MM'")
        elif any(word in user_input for word in ["show reminders", "list reminders"]):
            show_reminders()
        elif any(word in user_input for word in ["check reminders", "reminders now"]):
            check_reminders()

        # WEATHER
        elif any(word in user_input for word in ["weather", "forecast"]):
            city = user_input.replace("what's the weather in", "").replace("weather in", "").replace("weather", "").strip()
            if city:
                get_weather(city)
            else:
                speak("❗ Please provide a city name.")

        # DICTIONARY & VOCABULARY
        elif user_input.startswith("define"):
            word = user_input.replace("define", "", 1).strip()
            if word:
                define_word(word)
            else:
                speak("❌ Please provide a word to define.")
        elif any(word in user_input for word in ["show history", "my vocabulary", "vocab"]):
            history = load_json(HISTORY_FILE)
            if not history:
                speak("No dictionary history yet.")
            else:
                print("\n Vocabulary History:\n")
                for entry in history:
                    print(f"🔹 {entry.get('word')} — {entry.get('date')}")
                speak(f"You have {len(history)} saved words.")

        # NEWS
        elif any(word in user_input for word in ["news", "headlines", "what's new"]):
            get_news()

        # RANDOM FACT
        elif any(word in user_input for word in ["fact", "tell me a fact", "fun fact"]):
            get_random_fact()
            
        else:
            speak("❗ Unknown command. Try: 'hello', 'add task', 'show notes', 'weather in Karachi', 'define word', 'news', or 'fact'.")

if __name__ == "__main__":
    main()