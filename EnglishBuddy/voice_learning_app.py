"""
voice_learning_app.py

A Tkinter GUI app that:
- Speaks questions/sentences (pyttsx3)
- Listens and transcribes answers (speech_recognition)
- Saves audio answers as WAV files
- Includes two games: Find Synonym and Repeat Sentence (no-looking)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import datetime
import random
import difflib

import pyttsx3
import speech_recognition as sr

# Optional: use nltk WordNet for synonyms (recommended)
try:
    from nltk.corpus import wordnet
    has_wordnet = True
except Exception:
    has_wordnet = False

# -------------------------
# Config / Globals
# -------------------------
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

engine = pyttsx3.init()
engine.setProperty('rate', 160)  # speech speed

recognizer = sr.Recognizer()

# small fallback word list if wordnet unavailable
FALLBACK_WORDS = [
    ("happy", ["glad", "joyful", "pleased"]),
    ("fast", ["quick", "rapid", "swift"]),
    ("big", ["large", "huge", "vast"]),
    ("smart", ["clever", "bright", "wise"]),
    ("sad", ["unhappy", "sorrowful", "downcast"]),
]

SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Learning by speaking is very effective.",
    "Practice makes progress every single day.",
    "Please remember to drink water while studying.",
    "Today is a good day to try something new."
]

# -------------------------
# Utility functions
# -------------------------
def speak(text, block=False):
    """Speak text using pyttsx3 on a separate thread if non-blocking."""
    def _run():
        engine.say(text)
        engine.runAndWait()
    if block:
        _run()
    else:
        t = threading.Thread(target=_run, daemon=True)
        t.start()

def listen_and_save(prompt_for_user=None, timeout=3, phrase_time_limit=4):
    """
    Listens via microphone, returns (transcript or None, audio_data or None, error_message or None).
    Also saves audio to a file. FIXED VERSION (faster + non-blocking failsafe).
    """
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except Exception:
        return None, None, None  # fail fast but continue test

    # Save audio
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(RECORDINGS_DIR, f"answer_{timestamp}.wav")
    try:
        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())
    except:
        filename = None

    # Recognize voice
    try:
        transcript = recognizer.recognize_google(audio)
    except:
        transcript = None

    return transcript, filename, None


def similarity_score(a, b):
    """Return ratio 0..1 of similarity using SequenceMatcher."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_synonyms(word):
    """Return set of synonyms using WordNet or fallback list."""
    syns = set()
    if has_wordnet:
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                candidate = lemma.name().replace('_', ' ').lower()
                if candidate != word.lower():
                    syns.add(candidate)
    else:
        # fallback: check FALLBACK_WORDS
        for w, synonyms in FALLBACK_WORDS:
            if w == word:
                for s in synonyms:
                    syns.add(s.lower())
    return syns

def pick_word_for_synonym_game():
    """Pick a word and synonyms tuple (word, synonyms list)"""
    if has_wordnet:
        # pick random synset and return first lemma as "word"
        all_synsets = list(wordnet.all_synsets(pos=None))
        # Filter to ones with multiple lemmas
        multis = [s for s in all_synsets if len(s.lemmas()) >= 2]
        if multis:
            syn = random.choice(multis)
            lemmas = [l.name().replace('_',' ') for l in syn.lemmas()]
            word = lemmas[0]
            synonyms = lemmas[1:] if len(lemmas) > 1 else []
            return word, list(set(synonyms))
    # fallback
    w, syns = random.choice(FALLBACK_WORDS)
    return w, syns

# -------------------------
# Tkinter GUI
# -------------------------
class VoiceLearningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice Learning App")
        self.geometry("800x520")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        # Use default theme
        self.style.configure("TButton", padding=6)

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_practice_tab()
        self.create_games_tab()
        self.create_recordings_tab()
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status_bar.pack(fill="x", padx=10, pady=(0,10))

    # -----------------
    # Practice Tab
    # -----------------
       # -----------------
    # Practice Tab
    # -----------------
       # -----------------
    # Practice Tab
    # -----------------
    def create_practice_tab(self):
        self.practice_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.practice_frame, text="Practice")

        lbl = ttk.Label(self.practice_frame, text="Practice Test (Questions Asked One by One)", font=("Segoe UI", 14))
        lbl.pack(pady=(10,6))

        # Test questions
        self.practice_questions = [
            "What is your name?",
            "How are you feeling today?",
            "What did you learn yesterday?",
            "Tell me your favourite hobby.",
            "Where do you live?"
        ]

        self.current_q_index = 0

        btn_start_test = ttk.Button(self.practice_frame, text="Start Test", command=self.start_practice_test)
        btn_start_test.pack(pady=6)

        self.practice_transcript = tk.Text(self.practice_frame, height=15, width=90)
        self.practice_transcript.pack(pady=10)

    def start_practice_test(self):
        self.current_q_index = 0
        self.practice_transcript.delete("1.0", "end")
        self.ask_next_question()

    def ask_next_question(self):
        """Speak question and start listening automatically."""
        if self.current_q_index >= len(self.practice_questions):
            self.practice_transcript.insert("end", "\n--- TEST COMPLETED ---\n")
            self.status_var.set("Test finished!")
            speak("Test completed. Good job!")
            return

        q = self.practice_questions[self.current_q_index]
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        self.practice_transcript.insert(
            "end",
            f"\nQ{self.current_q_index+1}: {q}   [{timestamp}]\n"
        )

        self.status_var.set(f"Asking question {self.current_q_index+1}...")
        speak(q)

        # Delay before listening
        self.after(1500, self.listen_answer_auto)

    def listen_answer_auto(self):
        """Listen in background and move to next question."""
        self.status_var.set("Listening for answer...")

        t = threading.Thread(target=self.capture_answer_background, daemon=True)
        t.start()

    def capture_answer_background(self):
         transcript, filename, error = listen_and_save()

    # ALWAYS continue test
         self.after(0, self.process_answer_gui, transcript, filename, error)


    def process_answer_gui(self, transcript, filename, error):
        if transcript:
            self.practice_transcript.insert("end", f"Answer: {transcript}\n")
        if filename:
            self.practice_transcript.insert("end", f"Audio saved: {filename}\n")
        else:
            self.practice_transcript.insert("end", "No valid answer received.\n")

        self.current_q_index += 1
        self.after(1000, self.ask_next_question)


        # Move to next question
        self.current_q_index += 1
        self.after(1000, self.ask_next_question)


    # -----------------
    # Games Tab
    # -----------------
    def create_games_tab(self):
        self.games_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.games_frame, text="Games")

        header = ttk.Label(self.games_frame, text="Games: Find Synonym / Repeat Sentence", font=("Segoe UI", 14))
        header.pack(pady=(10,6))

      

        # Repeat sentence game
        rep_frame = ttk.LabelFrame(self.games_frame, text="Repeat Sentence (No Looking)")
        rep_frame.pack(fill="x", padx=12, pady=8)

        self.rep_mode_var = tk.BooleanVar(value=True)  # hidden mode
        ttk.Checkbutton(rep_frame, text="Hide sentence (player should not look)", variable=self.rep_mode_var).grid(row=0, column=0, padx=6, pady=6, sticky="w")

        self.rep_sentence_var = tk.StringVar(value="Press Start")
        ttk.Label(rep_frame, text="Sentence: ").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.rep_sentence_label = ttk.Label(rep_frame, textvariable=self.rep_sentence_var, font=("Segoe UI", 11))
        self.rep_sentence_label.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        btn_rep_start = ttk.Button(rep_frame, text="Start Round", command=self.on_rep_start)
        btn_rep_start.grid(row=1, column=2, padx=6)

        btn_rep_listen = ttk.Button(rep_frame, text="Listen & Record Repeat", command=self.on_rep_listen)
        btn_rep_listen.grid(row=1, column=3, padx=6)

        self.rep_feedback = ttk.Label(rep_frame, text="Feedback: -")
        self.rep_feedback.grid(row=2, column=0, columnspan=4, padx=6, pady=6, sticky="w")

   

    def on_syn_listen(self):
        # listen in background
        self.status_var.set("Listening for synonym answer...")
        t = threading.Thread(target=self._syn_listen_worker, daemon=True)
        t.start()

    def _syn_listen_worker(self):
        transcript, filename, error = listen_and_save()
        if error:
            self.syn_feedback.config(text=f"Error: {error}")
            self.status_var.set(error)
            return
        if transcript is None:
            self.syn_feedback.config(text="Could not understand your answer.")
            self.status_var.set("No transcript.")
            return

        # Evaluate: check if any known synonym present
        answer = transcript.lower()
        # gather synonyms using WordNet or fallback
        synonyms_set = set(s.lower() for s in get_synonyms(self.current_syn_word))
        # Also include synonyms provided earlier when pick_word used wordnet
        synonyms_set |= set(self.current_synonyms) if hasattr(self, "current_synonyms") else set()

        matched = False
        matched_word = None
        # direct containment check
        for s in synonyms_set:
            if s in answer:
                matched = True
                matched_word = s
                break

        # also check simple similarity to the original word - if user repeated same word, not accepted
        if not matched:
            # check if answer equals some known lemma or close
            for s in synonyms_set:
                if similarity_score(answer, s) > 0.8:
                    matched = True
                    matched_word = s
                    break

        if matched:
            self.syn_feedback.config(text=f"Good! Recognized: '{transcript}'. Matched synonym: {matched_word}")
            self.status_var.set("Synonym correct.")
        else:
            # provide hints: show up to 4 synonyms if available
            hint_list = list(synonyms_set)[:4] if synonyms_set else []
            hint_text = f"Try again. Hints: {', '.join(hint_list)}" if hint_list else "Try another synonym."
            self.syn_feedback.config(text=f"Not matched: '{transcript}'. {hint_text}")
            self.status_var.set("Synonym not matched.")

    # Repeat sentence game logic
    def on_rep_start(self):
        sentence = random.choice(SENTENCES)
        self.current_sentence = sentence
        if self.rep_mode_var.get():
            # hide sentence visually
            self.rep_sentence_var.set("**** (hidden) ****")
        else:
            self.rep_sentence_var.set(sentence)
        self.rep_feedback.config(text="Listen to the sentence, then repeat it.")
        self.status_var.set("Speaking sentence...")
        speak(sentence)

    def on_rep_listen(self):
        self.status_var.set("Listening to repeat...")
        t = threading.Thread(target=self._rep_listen_worker, daemon=True)
        t.start()

    def _rep_listen_worker(self):
        transcript, filename, error = listen_and_save()
        if error:
            self.rep_feedback.config(text=f"Error: {error}")
            self.status_var.set(error)
            return
        if transcript is None:
            self.rep_feedback.config(text="Could not understand your repetition.")
            self.status_var.set("No transcript.")
            return

        expected = getattr(self, "current_sentence", "")
        score = similarity_score(expected, transcript) if expected else 0.0
        pct = int(score * 100)
        self.rep_feedback.config(text=f"Recognized: '{transcript}' — similarity {pct}%")
        self.status_var.set(f"Repeat scored: {pct}%")
        if not self.rep_mode_var.get():
            # if sentence visible, show it again (it already is)
            pass
        else:
            # when hidden mode, reveal the sentence after attempt
            self.rep_sentence_var.set(expected)

    # -----------------
    # Recordings Tab    
    # -----------------
    def create_recordings_tab(self):
        self.recordings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recordings_frame, text="Recordings")

        hdr = ttk.Label(self.recordings_frame, text="Saved Recordings", font=("Segoe UI", 13))
        hdr.pack(pady=(10,6))

        ctrl = ttk.Frame(self.recordings_frame)
        ctrl.pack(fill="x", padx=10)
        btn_refresh = ttk.Button(ctrl, text="Refresh List", command=self.refresh_recordings_list)
        btn_refresh.pack(side="left", padx=6)
        btn_open_folder = ttk.Button(ctrl, text="Open Folder", command=lambda: os.startfile(os.path.abspath(RECORDINGS_DIR)))
        btn_open_folder.pack(side="left", padx=6)

        self.rec_listbox = tk.Listbox(self.recordings_frame, width=100, height=16)
        self.rec_listbox.pack(padx=10, pady=8)
        rec_btn_frame = ttk.Frame(self.recordings_frame)
        rec_btn_frame.pack(pady=6)
        btn_play = ttk.Button(rec_btn_frame, text="Play Selected", command=self.play_selected)
        btn_play.grid(row=0, column=0, padx=6)
        btn_delete = ttk.Button(rec_btn_frame, text="Delete Selected", command=self.delete_selected)
        btn_delete.grid(row=0, column=1, padx=6)

        self.refresh_recordings_list()

    def refresh_recordings_list(self):
        self.rec_listbox.delete(0, "end")
        files = sorted(os.listdir(RECORDINGS_DIR))
        for f in files:
            if f.lower().endswith(".wav"):
                path = os.path.join(RECORDINGS_DIR, f)
                t = time.ctime(os.path.getmtime(path))
                self.rec_listbox.insert("end", f"{f}    ({t})")

    def play_selected(self):
        sel = self.rec_listbox.curselection()
        if not sel:
            messagebox.showinfo("Play", "Select a recording first.")
            return
        entry = self.rec_listbox.get(sel[0])
        fname = entry.split()[0]
        path = os.path.join(RECORDINGS_DIR, fname)
        try:
            os.startfile(path)  # Windows; on mac/linux you may use 'open' or 'xdg-open'
        except Exception as e:
            messagebox.showerror("Play error", f"Could not open file: {e}")

    def delete_selected(self):
        sel = self.rec_listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete", "Select a recording first.")
            return
        entry = self.rec_listbox.get(sel[0])
        fname = entry.split()[0]
        path = os.path.join(RECORDINGS_DIR, fname)
        if messagebox.askyesno("Delete", f"Delete {fname}?"):
            try:
                os.remove(path)
                self.refresh_recordings_list()
            except Exception as e:
                messagebox.showerror("Delete error", f"Could not delete file: {e}")

# -------------------------
# Run app
# -------------------------
def main():
    app = VoiceLearningApp()
    app.mainloop()

if __name__ == "__main__":
    main()
