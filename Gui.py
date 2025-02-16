import tkinter as tk
import customtkinter
from tkinter import filedialog, Toplevel
import subprocess
import threading

# System Settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Function to open file explorer and get directory
def browse_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        opt_dir.set(folder_selected)

# Function to run script with progress bar
def run_script():
    output_dir = opt_dir.get()
    if not output_dir:
        return
    
    options = []
    if run_options['dry_run']: options.append('-n')
    if run_options['verbose_run']: options.append('-v')
    if run_options['force_run']: options.append('-f')
    if run_options['copy_run']: options.append('-C')
    if run_options['quit_on_error']: options.append('-Q')
    
    cmd = ['python3', 'main.py', output_dir] + options
    
    progress_window = Toplevel(app)
    progress_window.title("Progress")
    progress_window.geometry("300x100")
    progress_label = customtkinter.CTkLabel(progress_window, text="Processing...")
    progress_label.pack(pady=10)
    progress_bar = customtkinter.CTkProgressBar(progress_window, width=250)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
    
    def execute():
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            progress_bar.set(progress_bar.get() + 10)
        progress_bar.set(100)
        progress_label.configure(text="Completed!")
    
    threading.Thread(target=execute, daemon=True).start()

# App Frame
app = customtkinter.CTk()
app.geometry("500x300")
app.title("Paperctl")

# UI Elements
title = customtkinter.CTkLabel(app, text="Choose Download Directory", font=("Arial", 20))
title.pack(pady=10)

opt_dir = tk.StringVar()
output_dir = customtkinter.CTkEntry(app, width=400, height=30, textvariable=opt_dir)
output_dir.pack(pady=10)

browse_button = customtkinter.CTkButton(app, text="Browse", command=browse_directory)
browse_button.pack(pady=10)

run_options = {
    "dry_run": False,
    "verbose_run": False,
    "force_run": False,
    "copy_run": False,
    "quit_on_error": False
}

run_button = customtkinter.CTkButton(app, text="Run Script", command=run_script)
run_button.pack(pady=20)

# Run app
app.mainloop()
