
"""Jarvis: a simple voice assistant for Windows.
 
Say "Jarvis" to wake it, then give a command, or say both at once:
"Jarvis open YouTube".
"""
 
import subprocess
import time
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus
 
import pyttsx3
import speech_recognition as sr
 
try:
    import psutil
except ImportError:  # optional: uv add psutil
    psutil = None
 
WAKE_WORD = "jarvis"
MIC_INDEX = None  # set to a number from list_mics() if the wrong mic is used
 
recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8
 
 

def speak(text: str) -> None:
    """Speak text. A fresh engine per call avoids pyttsx3 going silent."""
    print(f"Jarvis: {text}")
    try:
        engine = pyttsx3.init("sapi5")
        engine.setProperty("volume", 1.0)
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:  # fall back to Windows' built-in speech
        print(f"(pyttsx3 failed: {e}; using fallback)")
        safe = text.replace("'", "").replace('"', "")
        subprocess.run(
            [
                "powershell",
                "-Command",
                "Add-Type -AssemblyName System.Speech; "
                "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                f".Speak('{safe}')",
            ]
        )
    time.sleep(0.3)  # keeps the mic from hearing Jarvis's own voice
 
 

def list_mics() -> None:
    """Print available microphones (use to find MIC_INDEX)."""
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        print(i, name)
 
 
def listen(timeout: int = 5, phrase_time_limit: int = 7) -> str:
    """Listen once. Return lowercase text, or '' if nothing was understood."""
    with sr.Microphone(device_index=MIC_INDEX) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        try:
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        except sr.WaitTimeoutError:
            return ""
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Network error: {e}")
        return ""
 
 

def open_app(exe: str, name: str) -> None:
    speak(f"Opening {name}")
    try:
        subprocess.Popen(exe)
    except FileNotFoundError:
        speak(f"I couldn't find {name}")
 
 
def handle(command: str) -> bool:
    """Run a command. Return False to quit."""
    if not command:
        return True
 
    if any(w in command for w in ("exit", "stop", "goodbye", "shut down")):
        speak("Goodbye sir")
        return False
 
    # Searches (checked first so "search youtube for X" works)
    if "search youtube for" in command or "play" in command and "youtube" in command:
        query = command.split("for", 1)[-1] if "for" in command else command.replace("play", "")
        query = query.replace("on youtube", "").replace("youtube", "").strip()
        speak(f"Searching YouTube for {query}")
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    elif "search for" in command or command.startswith("search "):
        query = command.split("search for", 1)[-1] if "search for" in command else command[7:]
        query = query.strip()
        speak(f"Searching for {query}")
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
 
    # Websites
    elif "youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")
    elif "google" in command:
        speak("Opening Google")
        webbrowser.open("https://google.com")
    elif "github" in command:
        speak("Opening GitHub")
        webbrowser.open("https://github.com")
 
    # Apps
    elif "notepad" in command:
        open_app("notepad.exe", "Notepad")
    elif "calculator" in command:
        open_app("calc.exe", "Calculator")
    elif "paint" in command:
        open_app("mspaint.exe", "Paint")
    elif "explorer" in command or "file manager" in command:
        open_app("explorer.exe", "File Explorer")
    elif "code" in command and "vs" in command:
        speak("Opening VS Code")
        subprocess.Popen("code", shell=True)
 
    # Info
    elif "time" in command:
        speak(f"It is {datetime.now():%I:%M %p}")
    elif "date" in command or "today" in command:
        speak(f"Today is {datetime.now():%A, %d %B %Y}")
    elif "battery" in command:
        battery = psutil.sensors_battery() if psutil else None
        if battery:
            plugged = "and charging" if battery.power_plugged else "and not charging"
            speak(f"Battery is at {int(battery.percent)} percent {plugged}")
        else:
            speak("I can't read the battery. Install psutil to enable this")
    elif "hello" in command or "hi" == command:
        speak("Hello sir")
 
    else:
        speak("Sorry, I don't know that command yet")
    return True
 
 

def main() -> None:
    speak("Initializing Jarvis")
    running = True
    try:
        while running:
            heard = listen()
            if WAKE_WORD not in heard:
                continue
 
            # Handle "jarvis open youtube" in one sentence
            command = heard.split(WAKE_WORD, 1)[1].strip()
            if not command:
                speak("Yes sir")
                command = listen(timeout=6, phrase_time_limit=8)
            running = handle(command)
    except KeyboardInterrupt:
        print("\nStopped.")
 
 
if __name__ == "__main__":
    main()
 
