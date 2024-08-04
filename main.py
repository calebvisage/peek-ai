import tkinter as tk
from tkinter import simpledialog, messagebox
import pyscreenshot as ImageGrab
import base64
from io import BytesIO
import os
import sys
import signal
from openai import OpenAI
from time import sleep
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
SCREENSHOT_DIR = './screenshots'
SCREENSHOT_FORMAT = 'PNG'
DEFAULT_QUERY = 'Describe everything in this image. List every open window if applicable. List the number of visible windows. Briefly describe what the user is doing for each open window. Do not describe the contents of the windows unless asked to do so. Censor sensitive information.'

# Configure OpenAI API
API_KEY = os.getenv('OPENAI_API_KEY')
MODELS = ['gpt-4o-mini', 'gpt-4o']
MODEL = MODELS[0]
TEMPERATURE = 0.5
SYSTEM_PROMPT = '''You are a helpful assistant. You answer queries based on a given screenshot image. Always assume the user is querying about the image. Use direct personal language, so instead of "the user" use "you", instead of "the image" use "your desktop". Be concise.'''
MAX_TOKENS = 300

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

# Signal handler to stop the script on Ctrl+C
def signal_handler(sig, frame):
    print('Interrupt received, stopping the script.')
    root.quit()
    sys.exit(0)

# Capture the screen, save it and return the image as a base64 string
def capture_screen():
    screenshot = ImageGrab.grab()
    screenshots_dir = SCREENSHOT_DIR
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    latest_screenshot = max([int(f.split('.')[0]) for f in os.listdir(screenshots_dir)]) if os.listdir(screenshots_dir) else 0
    screenshot_path = os.path.join(screenshots_dir, f'{latest_screenshot + 1}.{SCREENSHOT_FORMAT.lower()}')
    screenshot.save(screenshot_path, format=SCREENSHOT_FORMAT)
    buffer = BytesIO()
    screenshot.save(buffer, format=SCREENSHOT_FORMAT)
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_str

def ask_openai(query, image_data):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{SCREENSHOT_FORMAT.lower()};base64,{image_data}"}
                }
            ]},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    return completion.choices[0].message.content

class QueryDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("PeekAI")
        self.geometry("400x100")
        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        tk.Label(self, text="What is your query?").pack(pady=5)
        self.entry = tk.Entry(self, width=50)
        self.entry.pack(pady=5)
        self.entry.focus_set()
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="Submit", command=self.on_submit).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.bind("<Return>", lambda event: self.on_submit())
        self.bind("<Escape>", lambda event: self.destroy())

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def on_submit(self):
        query = self.entry.get()
        query = query if query else DEFAULT_QUERY
        if query:
            self.withdraw() # Hide the dialog
            self.update_idletasks() # Update the window to hide it before taking the screenshot
            sleep(0.5)
            image_data = capture_screen() # Capture the screen
            self.deiconify() # Show the dialog again
            response = ask_openai(query, image_data) # Ask OpenAI
            messagebox.showinfo("Answer", response, parent=self) # Show the response
        self.destroy()

def on_ask(event=None):
    QueryDialog(root)

# Setup GUI
root = tk.Tk()
root.title("PeekAI")
root.withdraw()  # Hide the main window

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

on_ask()

# Start the GUI loop
root.mainloop()