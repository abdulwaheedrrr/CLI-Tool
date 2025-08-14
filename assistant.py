# assistant.py
import argparse
import json
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
        except Exception:
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

def add_task(task):
    tasks = load_tasks()
    tasks.append({"task": task, "done": False})
    save_tasks(tasks)
    speak(f" Task added: {task}")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        speak(" No tasks found.")
        return
    print(" Your tasks:")
    for i, t in enumerate(tasks, 1):
        status = "✓" if t.get("done") else "❌"
        print(f"{i}. {t.get('task')} [{status}]")
    # Speak each task (no limit now)
    speak(f"You have {len(tasks)} tasks:")
    for i, t in enumerate(tasks, 1):
        speak(f"Task {i}: {t.get('task')}. {'done' if t.get('done') else 'not done'}")

def complete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        tasks[index]["done"] = True
        save_tasks(tasks)
        speak(f"Marked as complete: {tasks[index]['task']}")
    else:
        speak("❗ Invalid task number.")

def remove_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        save_tasks(tasks)
        speak(f"Removed task: {removed['task']}")
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
    speak(f"Note added: {note}")

def show_notes():
    notes = load_notes()
    if not notes:
        speak(" No notes found.")
        return
    print("Your notes:")
    for i, note in enumerate(notes, 1):
        print(f"{i}. {note}")
    # Speak all notes (no limit now)
    speak(f"You have {len(notes)} notes:")
    for i, note in enumerate(notes, 1):
        speak(f"Note {i}: {note}")

def search_notes(keyword):
    notes = load_notes()
    found = [n for n in notes if keyword.lower() in n.lower()]
    if found:
        speak(f"🔍 Found {len(found)} note(s) containing '{keyword}':")
        for i, n in enumerate(found, 1):
            print(f"{i}. {n}")
            speak(n)
    else:
        speak("No matching notes found.")

# ---------------- REMINDERS ----------------
def load_reminders():
    return load_json(REMINDERS_FILE)

def save_reminders(reminders):
    save_json(REMINDERS_FILE, reminders)

def add_reminder(text, date_str, time_str):
    try:
        reminder_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        speak("❗ Invalid date/time format. Use YYYY-MM-DD HH:MM")
        return
    reminders = load_reminders()
    reminders.append({"text": text, "time": reminder_time.strftime("%Y-%m-%d %H:%M")})
    save_reminders(reminders)
    speak(f"Reminder set: '{text}' at {reminder_time.strftime('%Y-%m-%d %H:%M')}")

def show_reminders():
    reminders = load_reminders()
    if not reminders:
        speak(" No reminders found.")
        return
    print(" Your reminders:")
    for i, r in enumerate(reminders, 1):
        print(f"{i}. {r.get('text')} — {r.get('time')}")
    # Speak all reminders (no limit now)
    speak(f"You have {len(reminders)} reminders:")
    for i, r in enumerate(reminders, 1):
        speak(f"Reminder {i}: {r.get('text')} at {r.get('time')}")

def check_reminders():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    reminders = load_reminders()
    due = [r for r in reminders if r.get("time") == now]
    if due:
        for r in due:
            speak(f"REMINDER: {r.get('text')}")
    else:
        speak("No reminders right now.")

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
            speak(f"❌ Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        speak(f"Could not fetch weather: {e}")

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
        print(f"\n Definitions for '{word}':\n")
        first_def = None
        for meaning in data[0].get("meanings", []):
            part = meaning.get("partOfSpeech", "")
            print(f"🔹 {part.capitalize()}:")
            for idx, d in enumerate(meaning.get("definitions", []), 1):
                definition = d.get("definition", "")
                if not first_def:
                    first_def = definition
                print(f"   {idx}. {definition}")
                if d.get("example"):
                    print(f"      💡 Example: {d.get('example')}")
            print()
        save_word_to_history(word)
        if first_def:
            speak(f"{word}: {first_def}")
    except Exception as e:
        speak(f"Error fetching definition: {e}")

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
        
        print("\nTop Headlines:\n")
        headlines_text = "Here are the top 5 news headlines: "
        for i, a in enumerate(articles, 1):
            title = a.get("title", "No title")
            url = a.get("url", "")
            print(f"{i}. {title}")
            if url:
                print(f"   🔗 {url}")
            print()
            headlines_text += f"Headline {i}: {title}. "
        speak(headlines_text)
    except Exception as e:
        speak(f"Could not fetch news: {e}")

# ---------------- MAIN ----------------
def main():
    parser = argparse.ArgumentParser(description="Your Personal Assistant CLI")
    parser.add_argument("command", help="Command (greet, addtask, showtasks, done, remove, addnote, shownotes, searchnote, addreminder, showreminders, checkreminders, weather, define, vocab, news, bye)")
    parser.add_argument("value", nargs="?", help="Extra value (put in quotes if it contains spaces).")
    args = parser.parse_args()
    cmd = args.command.lower()

    if cmd == "greet":
        speak(" Hello! Abdul waheed How can I help you today?")
    elif cmd == "bye":
        speak("Goodbye! Abdul waheed Have a great day!")
    elif cmd == "addtask":
        if args.value:
            add_task(args.value)
        else:
            speak("❗ Please provide a task description.")
    elif cmd == "showtasks":
        show_tasks()
    elif cmd == "done":
        if args.value and args.value.isdigit():
            complete_task(int(args.value) - 1)
        else:
            speak("❗ Please provide the task number.")
    elif cmd == "remove":
        if args.value and args.value.isdigit():
            remove_task(int(args.value) - 1)
        else:
            speak("❗ Please provide the task number.")
    elif cmd == "addnote":
        if args.value:
            add_note(args.value)
        else:
            speak("❗ Please provide a note.")
    elif cmd == "shownotes":
        show_notes()
    elif cmd == "searchnote":
        if args.value:
            search_notes(args.value)
        else:
            speak("❗ Please provide a keyword to search.")
    elif cmd == "addreminder":
        if args.value:
            parts = args.value.split(";")
            if len(parts) == 3:
                add_reminder(parts[0].strip(), parts[1].strip(), parts[2].strip())
            else:
                speak("❗ Use format: addreminder \"Text;YYYY-MM-DD;HH:MM\"")
        else:
            speak("❗ Please provide reminder text, date, and time.")
    elif cmd == "showreminders":
        show_reminders()
    elif cmd == "checkreminders":
        check_reminders()
    elif cmd == "weather":
        if args.value:
            get_weather(args.value)
        else:
            speak("❗ Please provide a city name.")
    elif cmd == "define":
        if args.value:
            define_word(args.value)
        else:
            speak("❌ Please provide a word to define.")
    elif cmd == "vocab":
        history = load_json(HISTORY_FILE)
        if not history:
            speak("No dictionary history yet.")
        else:
            print("\n Vocabulary History:\n")
            for entry in history:
                print(f"🔹 {entry.get('word')} — {entry.get('date')}")
            speak(f"You have {len(history)} saved words.")
    elif cmd == "news":
        get_news()
    else:
        speak("❗ Unknown command. Try: greet, addtask, showtasks, news, weather, define, vocab, bye")

if __name__ == "__main__":
    main()
