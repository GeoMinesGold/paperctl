#!/usr/bin/env python3
import tkinter
import customtkinter
from tkinter import filedialog

# System Settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Function to open file explorer and get directory
def browse_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        opt_dir.set(folder_selected)  # Update the entry field

# Function to update checkbox states
def update_option(option, var):
    run_options[option] = bool(var.get())
    print(run_options)  # Debugging: Print options when changed

# App Frame
app = customtkinter.CTk()
app.geometry("600x480")
app.title("Paperctl")

# UI Elements
title = customtkinter.CTkLabel(app, text="Choose Download Directory", font=("Arial", 20))
title.pack(pady=10)

opt_dir = tkinter.StringVar()
output_dir = customtkinter.CTkEntry(app, width=400, height=30, textvariable=opt_dir)
output_dir.pack(pady=10)

# Button to Open File Explorer
browse_button = customtkinter.CTkButton(app, text="Browse", command=browse_directory)
browse_button.pack(pady=10)

# Dictionary to store checkbox states
run_options = {
    "dry_run": False,
    "verbose_run": False,
    "force_run": False,
    "copy_run": False,
    "quit_on_error": False
}

# Checkbutton Variables
dry_run_var = tkinter.IntVar()
verbose_var = tkinter.IntVar()
force_var = tkinter.IntVar()
copy_var = tkinter.IntVar()
quit_var = tkinter.IntVar()

# Frame for Checkboxes
checkbox_frame = customtkinter.CTkFrame(app)
checkbox_frame.pack(pady=10)

# Checkboxes (side by side)
dry_run_cb = customtkinter.CTkCheckBox(checkbox_frame, text="Dry Run", variable=dry_run_var, command=lambda: update_option("dry_run", dry_run_var), width=20)
dry_run_cb.grid(row=0, column=0, padx=5)

verbose_cb = customtkinter.CTkCheckBox(checkbox_frame, text="Verbose", variable=verbose_var, command=lambda: update_option("verbose_run", verbose_var), width=20)
verbose_cb.grid(row=0, column=1, padx=6)

force_cb = customtkinter.CTkCheckBox(checkbox_frame, text="Force", variable=force_var, command=lambda: update_option("force_run", force_var), width=20)
force_cb.grid(row=0, column=2, padx=7)

copy_cb = customtkinter.CTkCheckBox(checkbox_frame, text="Copy", variable=copy_var, command=lambda: update_option("copy_run", copy_var), width=20)
copy_cb.grid(row=0, column=3, padx=8)

quit_cb = customtkinter.CTkCheckBox(checkbox_frame, text="Quit on Error", variable=quit_var, command=lambda: update_option("quit_on_error", quit_var), width=20)
quit_cb.grid(row=0, column=4, padx=9)




# Run app
app.mainloop()
5
