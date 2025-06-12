import os
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext, filedialog
import tkinter.ttk as ttk
from tkinter import PhotoImage
from tkinter.ttk import Progressbar
import tkinter.font as tkFont
import subprocess
import threading
import json
import signal
import configparser
import sys
import shlex
import re
import time
import queue
import webbrowser
from rich.console import Console
from rich.text import Text

console_stream = Console(force_terminal=True)



if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(".")
    

PROFILE_FILE = "profiles.json"
SETTINGS_FILE = "settings.ini"



yt_process = None


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        self.show_tooltip()

    def on_leave(self, event=None):
        self.hide_tooltip()

    def show_tooltip(self):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=self.text, background="lightyellow", borderwidth=1, relief="solid", font=("Segoe UI", 9))
        label.pack(ipadx=5, ipady=2)

    def hide_tooltip(self):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ============ SETTINGS =============
def load_settings():
    config = configparser.ConfigParser()
    if not os.path.exists(SETTINGS_FILE):
        config['DEFAULT'] = {
            'software_path': '',
            'output_folder': '',
            'use_custom_output': 'False'
        }
        with open(SETTINGS_FILE, 'w') as f:
            config.write(f)
    else:
        config.read(SETTINGS_FILE)
    return config

def save_settings(config):
    with open(SETTINGS_FILE, 'w') as f:
        config.write(f)

settings = load_settings()

# ============ PROFILES =============
def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

profiles = load_profiles()

# ============ COMMAND RUNNER ============
def build_command(shortname, user_args):
      
    profile = profiles.get(shortname)
    if not profile:
        raise ValueError("Profile not found.")

    template = profile['command_template']
    try:
        args = shlex.split(template.format(*user_args))
    except IndexError as e:
        raise ValueError(f"Missing arguments: {e}")

    yt_path = profile.get("custom_path") or settings['DEFAULT'].get('software_path')
    
    if not yt_path:
        raise ValueError("Software path is not defined in settings or in profile.")
    
    command = [yt_path] + args

    mode = profile.get("export_mode", "default")
    flag = profile.get("custom_output_flag", "--output")
    folder = ""

    if mode == "default" and settings['DEFAULT'].getboolean('use_custom_output', False):
        folder = settings['DEFAULT'].get('output_folder', '')
    elif mode == "custom":
        folder = profile.get("custom_export_path", "")

    if folder and mode != "none":
        command += [flag, f"{folder}/%(title)s.%(ext)s"]
        
    if settings['DEFAULT'].getboolean('use_custom_output', False):
        out_folder = settings['DEFAULT'].get('output_folder', '')
        if out_folder:
            command += ['--output', f'{out_folder}/%(title)s.%(ext)s']

    return command


def kill_process():
    global yt_process
    progressvar.set(100)
    progress.stop()
    # --- DEBUGGING START ---
    append_console_output("\n[Stop Button Clicked]\n")
    if yt_process:
        poll_result = yt_process.poll()
        append_console_output(f"[DEBUG] kill_process check. Process object: {yt_process}\n")
        append_console_output(f"[DEBUG] PID: {yt_process.pid}. Poll result: {poll_result}\n")
        if poll_result is not None:
            append_console_output(f"[DEBUG] Conclusion: Process has already terminated with code: {poll_result}.\n")
    # else:
        # append_console_output("[DEBUG] Conclusion: Global 'yt_process' variable is None.\n")
    # --- DEBUGGING END ---

    if not yt_process or yt_process.poll() is not None:
        append_console_output("\n[No active process to stop]\n")
        return

    append_console_output("\n[Attempting to stop the process...]\n")
    
    try:
        if os.name == 'nt':
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(yt_process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            append_console_output("[Process terminated by user]\n")
        else:
            pgid = os.getpgid(yt_process.pid)
            os.killpg(pgid, signal.SIGINT)
            append_console_output("[Interruption signal sent (Ctrl+C)]\n")
            try:
                yt_process.wait(timeout=5)
                append_console_output("[Process terminated gracefully]\n")
            except subprocess.TimeoutExpired:
                append_console_output("[Process did not respond. Forcing termination...]\n")
                os.killpg(pgid, signal.SIGKILL)
                append_console_output("[Process forcefully terminated]\n")

    except Exception as e:
        append_console_output(f"[ERROR] Failed to stop process: {e}\n")
    finally:
        yt_process = None


def center_window(win, width=400, height=300):
    win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - width) // 2
    y = root.winfo_y() + (root.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


# --- NEW FUNCTION ---
# This function sends user input to the running process.
def send_to_process(event=None):
    global yt_process
    # Get text from the input entry and clear it
    input_text = console_input_entry.get()
    console_input_entry.delete(0, tk.END)

    # Echo the input to the console display with a special tag
    append_console_output(f"{input_text}\n", "user_input")

    # If a process is running, write the input to its stdin
    if yt_process and yt_process.poll() is None:
        try:
            # Add a newline character and flush immediately
            yt_process.stdin.write(f"{input_text}\n")
            yt_process.stdin.flush()
            append_console_output("[Input sent to process]\n")
        except (IOError, BrokenPipeError, OSError) as e:
            append_console_output(f"\n[ERROR] Failed to send input to process: {e}\n")
            # Try to check if process is still alive
            if yt_process and yt_process.poll() is not None:
                append_console_output(f"[Process has already exited with code: {yt_process.poll()}]\n")
    else:
        if yt_process:
            rc = yt_process.poll()
            append_console_output(f"\n[Process has exited with code: {rc}]\n")
        else:
            append_console_output("\n[No active process to send input to]\n")


def run_command(command, show_output_in_gui=True):
    global yt_process
    
    def task():
        global yt_process  # Add this line to ensure we're modifying the global variable
        nonlocal command
        # Clear console and start progress bar
        console_output.configure(state='normal')
        console_output.delete("1.0", tk.END)
        console_output.configure(state='disabled')
        progressvar.set(0)
        progress.start()
        append_console_output(f"[DEBUG] Running command: {' '.join(shlex.quote(c) for c in command)}\n")

        try:
            # Common Popen arguments
            popen_args = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,  # Separate stderr
                "text": True,
                "encoding": 'utf-8',
                "errors": 'replace',
                "bufsize": 1,
            }

            # if os.name == 'nt':
                # # Windows-specific settings
                # popen_args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            # else:
                # # Unix-specific settings
                # popen_args['preexec_fn'] = os.setsid

            if os.name == 'nt':
                # Windows-specific settings:
                # CREATE_NEW_PROCESS_GROUP is for sending Ctrl+C/signals.
                # CREATE_NO_WINDOW prevents a new console from popping up for the subprocess.
                popen_args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            else:
                # Unix-specific settings
                popen_args['preexec_fn'] = os.setsid
                
            yt_process = subprocess.Popen(command, **popen_args)
            append_console_output(f"\n[DEBUG] Process started. PID: {yt_process.pid}\n\n")

        except Exception as e:
            append_console_output(f"[ERROR] Failed to start process: {e}\n")
            yt_process = None
            return

        # Read output using threading for both stdout and stderr
        try:
            import queue
            import threading
            
            output_queue = queue.Queue()
            
            def read_stream(stream, stream_name):
                try:
                    buffer = ""
                    while True:
                        char = stream.read(1)
                        if not char:  # End of stream
                            if buffer:
                                output_queue.put((stream_name, buffer))
                            break
                        
                        buffer += char
                        
                        # Send output immediately if:
                        # 1. We hit a newline (complete line)
                        # 2. We hit a prompt indicator (: or >) 
                        # 3. Buffer gets too long (safety)
                        # 4. We hit a space after certain prompt words
                        if (char == '\n' or 
                            char in ':>' or 
                            len(buffer) > 100 or
                            (char == ' ' and any(word in buffer.lower() for word in ['continue', 'name', 'input', 'enter', 'press', 'choose', 'select']))):
                            output_queue.put((stream_name, buffer))
                            buffer = ""
                            
                except Exception as e:
                    if buffer:
                        output_queue.put((stream_name, buffer))
                    output_queue.put(('error', f"Error reading {stream_name}: {e}\n"))
            
            # Start threads for reading stdout and stderr
            stdout_thread = threading.Thread(target=read_stream, args=(yt_process.stdout, 'stdout'), daemon=True)
            stderr_thread = threading.Thread(target=read_stream, args=(yt_process.stderr, 'stderr'), daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Process output from both streams
            while yt_process and yt_process.poll() is None:
                try:
                    stream_name, line = output_queue.get(timeout=0.1)
                    append_console_output(line)
                except queue.Empty:
                    continue
                except Exception as e:
                    append_console_output(f"[ERROR] Queue error: {e}\n")
                    break
            
            # Read any remaining output after process ends
            timeout_count = 0
            while timeout_count < 10:  # Give it 1 second to finish
                try:
                    stream_name, line = output_queue.get(timeout=0.1)
                    append_console_output(line)
                    timeout_count = 0  # Reset if we got data
                except queue.Empty:
                    timeout_count += 1
                    continue
                except Exception:
                    break

        except Exception as e:
            append_console_output(f"[ERROR] Error reading process output: {e}\n")

        finally:
            progressvar.set(100)
            progress.stop()
            append_console_output(f"\n[DEBUG] Process finished reading output.\n")

            if yt_process:
                # Wait a moment for the process to finish naturally
                try:
                    yt_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                    
                rc = yt_process.poll()
                if rc is not None:
                    append_console_output(f"\n[Process exited with code: {rc}]\n")
                else:
                     append_console_output(f"\n[Process completed]\n")
                     
                # Close stdin properly
                try:
                    if yt_process.stdin:
                        yt_process.stdin.close()
                except:
                    pass

            # Only set to None after everything is done
            yt_process = None

    threading.Thread(target=task, daemon=True).start()
    


def count_placeholders(template):
    return len(re.findall(r"{[^}]*}", template))
    
def run_command_threaded(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            console_output.insert(tk.END, line)
            console_output.see(tk.END)
        process.wait()
        append_console_output("\n[Command finished]\n")
        progressvar.set(100)
        progress.stop()        
        console_output.insert(tk.END, f"\nDone. Exit code: {process.returncode}\n")
    except Exception as e:
        console_output.insert(tk.END, f"Error: {str(e)}\n")

# ============ GUI =============
def add_profile():
    root.focus_set()
    top = tk.Toplevel(root)
    top.grab_set()
    top.title("Add profile")
    top.resizable(False, False)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    top.attributes("-topmost", True)
    center_window(top, width=580, height=370)  # Adjust dimensions as needed

    entries = {}

    def labeled_entry(label, row):
        tk.Label(top, text=label).grid(row=row, column=0, sticky='e')
        e = tk.Entry(top, width=40)
        e.grid(row=row, column=1, padx=5, pady=2)
        return e

    entries['name'] = labeled_entry("Profile Display Name:", 0)
    entries['short'] = labeled_entry("Profile Shortname:", 1)
    entries['template'] = labeled_entry("Command Template:", 2)
    entries['arg_names'] = labeled_entry("Argument Names (comma-separated):", 3)
  
    export_mode = tk.StringVar(value="default")

    # Frame for radio buttons
    export_group = tk.LabelFrame(top, text="Export Folder Mode")
    export_group.grid(row=5, column=0,  sticky='e')

    tk.Radiobutton(export_group, text="Use default", variable=export_mode, value="default").grid(row=0, column=0, sticky='w')
    tk.Radiobutton(export_group, text="Use custom", variable=export_mode, value="custom").grid(row=1, column=0, sticky='w')
    tk.Radiobutton(export_group, text="Do not use export", variable=export_mode, value="none").grid(row=2, column=0, sticky='w')

    custom_frame = tk.Frame(top)

    custom_output_label = tk.Label(custom_frame, text="Custom Output Path Parameter:")
    custom_output_label.grid(row=6, column=0, sticky='e')    
    custom_output_entry = tk.Entry(custom_frame, width=40)
    custom_output_entry.grid(row=6, column=1, padx=5, pady=2)
    
    custom_export_label = tk.Label(custom_frame, text="Custom Export Folder Path:")
    custom_export_label.grid(row=7, column=0, sticky='e')    
    custom_export_entry = tk.Entry(custom_frame, width=40)
    custom_export_entry.grid(row=7, column=1, padx=5, pady=2)    
    browse_export_btn = ttk.Button(custom_frame, text="Browse", command=lambda: choose_folder(custom_export_entry))
    browse_export_btn.grid(row=7, column=2, padx=5)
    
    def update_custom_export_visibility(*args):
        if export_mode.get() == "custom":
            custom_frame.grid(row=6, column=0, columnspan=3,  padx=5, pady=2, sticky='e')
        else:
            custom_frame.grid_remove()

    export_mode.trace_add("write", update_custom_export_visibility)
    update_custom_export_visibility()



    entries['custom_path'] = labeled_entry("Custom Program Path (optional):", 4)
    browse_btn = ttk.Button(top, text="Browse", command=lambda: choose_file(entries['custom_path'], top))
    browse_btn.grid(row=4, column=2, padx=5)
    
    error_label = tk.Label(top, text="", fg="red")
    error_label.grid(row=8, column=0, columnspan=2, sticky='e')
    
    def save():
            name = entries['name'].get()
            short = entries['short'].get()  # Define 'short' here
            template = entries['template'].get()
            arg_count = count_placeholders(template)
            arg_names_str = entries['arg_names'].get()
            arg_names = [s.strip() for s in arg_names_str.split(',') if s.strip()] if arg_names_str else []

            # Validate shortname first
            if not re.match(r"^[a-zA-Z0-9\-]+$", short):
                error_label.config(text="Profile Shortname must only contain letters, numbers, or dashes.")
                return

            if short in profiles:
                error_label.config(text="Profile Shortname must be unique.")
                return

                
            if len(name) == 0:
                error_label.config(text="Profile Display name cannot be empty.")
                return
                
            if arg_count > 0 and not arg_names_str:
                 error_label.config(text="Argument names are required for templates with placeholders.")
                 return

            if len(arg_names) != arg_count:
                error_label.config(text=f"Template has {arg_count} arguments placeholders, but you provided {len(arg_names)} argument names.")
                return

            if export_mode.get() == "custom":
                custom_export_path = custom_export_entry.get().strip()
                custom_output_flag = custom_output_entry.get().strip()
                if len(custom_export_path) == 0:
                    error_label.config(text="Custom Export Folder Path cannot be empty.")
                    return           
            else:
                custom_export_path = ""
                custom_output_flag = ""

            profiles[short] = {
                "display_name": name,
                "shortname": short,
                "command_template": template,
                "custom_path": entries['custom_path'].get().strip(),
                "arg_names": arg_names,
                "export_mode": export_mode.get(),
                "custom_export_path": custom_export_path,
                "custom_output_flag": custom_output_flag
            }
            save_profiles(profiles)
            refresh_profiles()
            top.destroy()

    ttk.Button(top, text="Save", command=save).grid(row=9, column=1, pady=10, sticky='e')


def choose_file(entry_field, top):
    top.attributes("-topmost", False)
    path = filedialog.askopenfilename()
    top.attributes("-topmost", True)
    if path:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, path)

def choose_folder(entry_widget, top):
    top.attributes("-topmost", False)
    path = filedialog.askdirectory()
    top.attributes("-topmost", True)
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)


def edit_profile():
    root.focus_set()
    short = get_selected_shortname()
    original_short = short
    if not short:
        custom_info_dialog("Info", "Choose a profile first.")
        return

    profile = profiles[short]

    top = tk.Toplevel(root)
    top.grab_set()
    top.title("Edit profile")
    top.resizable(False, False)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    top.attributes("-topmost", True)
    center_window(top, width=580, height=370)  # Adjust dimensions as needed


    entries = {}

    def labeled_entry(label, row, val):
        tk.Label(top, text=label).grid(row=row, column=0, sticky='e')
        e = tk.Entry(top, width=40)
        e.insert(0, val)
        e.grid(row=row, column=1, padx=5, pady=2)
        return e

    entries['name'] = labeled_entry("Profile Display Name:", 0, profile['display_name'])
    entries['short'] = labeled_entry("Profile Shortname:", 1, profile['shortname'])
    entries['template'] = labeled_entry("Command Template:", 2, profile['command_template'])
    entries['arg_names'] = labeled_entry(
        "Argument Names (comma-separated):", 3, ",".join(profile.get("arg_names", []))
    )
    
    export_mode = tk.StringVar(value=profile.get("export_mode", "default"))

    # Frame for radio buttons
    export_group = tk.LabelFrame(top, text="Export Folder Mode")
    export_group.grid(row=5, column=0,  sticky='e')
    
    tk.Radiobutton(export_group, text="Use default", variable=export_mode, value="default").grid(row=0, column=0, sticky='w', columnspan=2)
    tk.Radiobutton(export_group, text="Use custom", variable=export_mode, value="custom").grid(row=1, column=0, sticky='w', columnspan=2)
    tk.Radiobutton(export_group, text="Do not use export", variable=export_mode, value="none").grid(row=2, column=0, sticky='w', columnspan=2)

    custom_frame = tk.Frame(top)
    
    custom_output_label = tk.Label(custom_frame, text="Custom Output Path Parameter:")
    custom_output_label.grid(row=6, column=0, sticky='e')    
    custom_output_entry = tk.Entry(custom_frame, width=40)
    custom_output_entry.grid(row=6, column=1, padx=5, pady=2)
    
    custom_export_label = tk.Label(custom_frame, text="Custom Export Folder Path:")
    custom_export_label.grid(row=7, column=0, sticky='e')    
    custom_export_entry = tk.Entry(custom_frame, width=40)
    custom_export_entry.grid(row=7, column=1, padx=5, pady=2)    
    browse_export_btn = ttk.Button(custom_frame, text="Browse", command=lambda: choose_folder(custom_export_entry))
    browse_export_btn.grid(row=7, column=2, padx=5)
    
    def update_custom_export_visibility(*args):
        if export_mode.get() == "custom":
            custom_frame.grid(row=6, column=0, columnspan=3,  padx=5, pady=2, sticky='e')
        else:
            custom_frame.grid_remove()

    export_mode.trace_add("write", update_custom_export_visibility)
    update_custom_export_visibility()



    entries['custom_path'] = labeled_entry("Custom Program Path (optional):", 4, profile.get("custom_path", ""))
    browse_btn = ttk.Button(top, text="Browse", command=lambda: choose_file(entries['custom_path'], top))
    browse_btn.grid(row=4, column=2, padx=5)
    
    error_label = tk.Label(top, text="", fg="red")
    error_label.grid(row=8, column=0, columnspan=2, sticky='e')
              
    def save():
            name = entries['name'].get()
            short_new = entries['short'].get()
            template = entries['template'].get()
            arg_count = count_placeholders(template)
            arg_names_str = entries['arg_names'].get()
            arg_names = [s.strip() for s in arg_names_str.split(',') if s.strip()] if arg_names_str else []

            # Validate shortname
            if not re.match(r"^[a-zA-Z0-9\-]+$", short_new):
                error_label.config(text="Profile Shortname must only contain letters, numbers, or dashes.")
                return

            # Check if the new shortname already exists (and it's not the original shortname)
            if short_new != short and short_new in profiles:
                error_label.config(text="Profile Shortname must be unique.")
                return

            if arg_count > 0 and not arg_names_str:
                error_label.config(text="Argument names are required for templates with placeholders.")
                return

            if len(name) == 0:
                error_label.config(text="Profile Display name cannot be empty.")
                return
                
            if len(arg_names) != arg_count:
                error_label.config(text=f"Template has {arg_count} arguments placeholders, but {len(arg_names)} argument names were provided.")
                return

            # If the shortname was changed, remove the old profile
            # if short_new != short:
                # del profiles[short]

            if short_new != original_short:
                del profiles[original_short]
    

            if export_mode.get() == "custom":
                custom_export_path = custom_export_entry.get().strip()
                custom_output_flag = custom_output_entry.get().strip()
                if len(custom_export_path) == 0:
                    error_label.config(text="Custom Export Folder Path cannot be empty.")
                    return                       
            else:
                custom_export_path = ""
                custom_output_flag = ""

            # profiles[short] = {
            profiles[short_new] = {
                "display_name": name,
                "shortname": short_new,
                "command_template": template,
                "custom_path": entries['custom_path'].get().strip(),
                "arg_names": arg_names,
                "export_mode": export_mode.get(),
                "custom_export_path": custom_export_path,
                "custom_output_flag": custom_output_flag
            }
            
            save_profiles(profiles)
            refresh_profiles()
            top.destroy()

    ttk.Button(top, text="Save", command=save).grid(row=9, column=1, pady=10, sticky='e')



def custom_confirm_dialog(title, message):
    root.focus_set()
    result = {"confirmed": False}

    top = tk.Toplevel(root)
    top.title(title)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    center_window(top, 300, 120)
    top.grab_set()
    top.transient(root)

    tk.Label(top, text=message, wraplength=280).pack(pady=(10, 5), padx=10)

    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Yes", command=lambda: [top.destroy(), result.update({"confirmed": True})]).pack(side=tk.LEFT, padx=10)
    ttk.Button(btn_frame, text="No", command=top.destroy).pack(side=tk.RIGHT, padx=10)

    top.wait_window()
    return result["confirmed"]
    
    
def custom_info_dialog(title, message):
    root.focus_set()
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    center_window(top, 300, 120)
    top.grab_set()
    top.transient(root)

    tk.Label(top, text=message, wraplength=280).pack(pady=(20, 10), padx=10)
    ttk.Button(top, text="OK", command=top.destroy).pack(pady=(0, 10))

    top.wait_window()

    
def delete_profile():
    root.focus_set()
    short = get_selected_shortname()
    if not short:
        custom_info_dialog("Info", "Choose a profile first.")
        return
    if short and custom_confirm_dialog("Confirm Delete", "Are you sure you want to delete this profile?"):
        profiles.pop(short)
        save_profiles(profiles)
        refresh_profiles()

def get_selected_shortname():
    selected = profile_listbox.curselection()
    if selected:
        return profile_keys[selected[0]]
    return None

def custom_input_popup(title, prompt, icon_path="icon.ico"):
    def on_ok():
        nonlocal user_input
        user_input = entry.get()
        top.destroy()
    
    user_input = None
    top = tk.Toplevel(root)
    top.grab_set()
    top.title(title)
    top.iconbitmap(os.path.join(BASE_DIR, icon_path))
    center_window(top, 300, 120)
    top.resizable(False, False)
    top.grab_set()
    tk.Label(top, text=prompt).pack(padx=10, pady=(10, 2))
    entry = tk.Entry(top, width=40)
    entry.pack(padx=10, pady=(0, 10))
    entry.focus()
    entry.bind("<Return>", lambda e: on_ok())
    ttk.Button(top, text="OK", command=on_ok).pack(pady=(0, 10))
    top.wait_window()
    return user_input


def on_profile_double_click(event=None):
    short = get_selected_shortname()
    if not short:
        custom_info_dialog("Info", "Choose a profile first.")
        return
    profile = profiles[short]
    args = []
    arg_names = profile.get('arg_names', [])
    template = profile['command_template']
    arg_count = count_placeholders(template)
    for i in range(arg_count):
        label = arg_names[i] if i < len(arg_names) else f"Argument {i+1}"
        val = custom_input_popup("Parameter", f"{label}:", icon_path="icon.ico")
        if val is None: return
        args.append(val)
    try:
        command = build_command(short, args)
        run_command(command, show_output_in_gui=True)
    except Exception as e:
        messagebox.showerror("Error", str(e))



def open_settings_window():
    root.focus_set()
    top = tk.Toplevel(root)
    top.grab_set()
    top.title("Settings")
    top.resizable(False, False)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    center_window(top, width=500, height=250)

    tk.Label(top, text="Program Path").grid(row=0, column=0, sticky='e', padx=10, pady=5)
    yt_entry = tk.Entry(top, width=40)
    yt_entry.insert(0, settings['DEFAULT'].get('software_path', ''))
    yt_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(top, text="Export Folder Path").grid(row=1, column=0, sticky='e', padx=10, pady=5)
    folder_entry = tk.Entry(top, width=40)
    folder_entry.insert(0, settings['DEFAULT'].get('output_folder', ''))
    folder_entry.grid(row=1, column=1, padx=10, pady=5)

    def browse_folder():
        top.attributes("-topmost", False)
        folder = filedialog.askdirectory()
        top.attributes("-topmost", True)
        if folder:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder)

    ttk.Button(top, text="Browse", command=browse_folder).grid(row=1, column=2, padx=5)

    use_custom = tk.BooleanVar(value=settings['DEFAULT'].getboolean('use_custom_output', False))
    tk.Checkbutton(top, text="Use Export Folder", variable=use_custom).grid(row=2, column=1, sticky='w', pady=5)

    def save():
        settings['DEFAULT']['software_path'] = yt_entry.get()
        settings['DEFAULT']['output_folder'] = folder_entry.get()
        settings['DEFAULT']['use_custom_output'] = str(use_custom.get())
        save_settings(settings)
        top.destroy()

    ttk.Button(top, text="Save", command=save).grid(row=3, column=1, sticky='e', pady=10)



def open_about_window():
    root.focus_set()
    top = tk.Toplevel(root)
    top.title("About")
    top.resizable(False, False)
    top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    center_window(top, 400, 150)
    top.grab_set()

    tk.Label(top, text="arGUIments \nv1.0.0\nCreated with ❤️\nby hycday", font=("Segoe UI", 10)).pack(pady=(10, 5))

 
    
def clear_console():
    console_output.configure(state='normal')
    console_output.delete("1.0", tk.END)
    console_output.configure(state='disabled')
    progressvar.set(0)
 
 
def center_window_main(win, width=1200, height=600):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# GUI layout
def refresh_profiles():
    profile_listbox.delete(0, tk.END)
    global profile_keys
    profile_keys = list(profiles.keys())
    for key in profile_keys:
        profile_listbox.insert(tk.END, profiles[key]["display_name"])


       
def toggle_console():
    if console_visible.get():
        right_frame.pack_forget()
        root.geometry("360x600")
        root.resizable(False, False)
        toggle_btn.config(image=show_icon)
        console_visible.set(False)
    else:
        # right_frame.pack(fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=6)        
        root.geometry("1200x600")
        root.resizable(True, True)
        toggle_btn.config(image=hide_icon)
        console_visible.set(True)
        root.resizable(False, False)


        
def append_console_output(text, tag=None):
    # Enable writing to the widget
    console_output.configure(state='normal')

    # This regex removes ANSI color codes which can mess up the display
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)

    # Insert text and apply the specified tag if any
    if tag:
        console_output.insert(tk.END, clean_text, tag)
    else:
        # If no tag provided, apply default coloring logic
        start_pos = console_output.index(tk.INSERT)
        console_output.insert(tk.END, clean_text)
        end_pos = console_output.index(tk.INSERT)

        lower_text = clean_text.lower()
        if any(word in lower_text for word in ['error', 'failed', 'exception']):
            console_output.tag_add("error", start_pos, end_pos)
        elif any(word in lower_text for word in ['warning', 'warn']):
            console_output.tag_add("warning", start_pos, end_pos)
        elif any(word in lower_text for word in ['downloading', 'download']):
            console_output.tag_add("download", start_pos, end_pos)
        elif '[' in clean_text and ']' in clean_text:
            console_output.tag_add("progress", start_pos, end_pos)

    # Scroll to the end and disable writing again
    console_output.see(tk.END)
    console_output.configure(state='disabled')
    # Force the GUI to update to show the new text immediately
    root.update_idletasks()



if __name__ == "__main__":
    
# ========= COMMAND-LINE MODE ===========
    if len(sys.argv) > 1:
        shortname = sys.argv[1]
        args = sys.argv[2:]
        try:
            command = build_command(shortname, args)
            # CLI mode uses subprocess.run, which inherits terminal (with colors)
            subprocess.run(command)
        except KeyboardInterrupt:
            # User pressed Ctrl+C. We can exit gracefully without an error message.
            # The newline character \n is to ensure the message appears on a new line after the ^C.
            print("\nProcess interrupted by user.")
        except Exception as e:
            print(f"[ERROR] {e}")
        sys.exit(0)
    else:
        print("Provide a profile shortname as first argument if running via command line.")
        
    # ========= GUI MODE ===========
    root = tk.Tk()
    center_window_main(root, 1200, 600)
    root.title("arGUIments - simplify execution of commands with arguments")
    root.geometry("1200x600")
    root.resizable(False, False)
    
    left_frame = tk.Frame(root, width=300)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)




    right_frame = tk.Frame(root)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)



    button_frame = tk.Frame(left_frame)
    button_frame.pack(fill=tk.X)
   
         
    add_icon = PhotoImage(file=os.path.join(BASE_DIR, "add.png"))  # Keep references global
    add_btn = ttk.Button(button_frame, image=add_icon,  command=add_profile)
    add_btn.pack(side=tk.LEFT)
    Tooltip(add_btn, "Create a new profile")
  
    edit_icon = PhotoImage(file=os.path.join(BASE_DIR, "edit.png"))  # Keep references global
    edit_btn = ttk.Button(button_frame, image=edit_icon,   command=edit_profile)
    edit_btn.pack(side=tk.LEFT)
    Tooltip(edit_btn, "Edit a profile")    
    
    delete_icon = PhotoImage(file=os.path.join(BASE_DIR, "delete.png"))  # Keep references global    
    delete_btn = ttk.Button(button_frame, image=delete_icon,  command=delete_profile)
    delete_btn.pack(side=tk.LEFT)
    Tooltip(delete_btn, "Delete a profile")    
    
    run_icon = PhotoImage(file=os.path.join(BASE_DIR, "run.png"))  # Keep references global
    run_btn = ttk.Button(button_frame, image=run_icon, command=on_profile_double_click)
    run_btn.pack(side=tk.LEFT)
    Tooltip(run_btn, "Run a profile")    
    
    stop_icon = PhotoImage(file=os.path.join(BASE_DIR, "stop.png"))  # Keep references global    
    stp_btn = ttk.Button(button_frame, image=stop_icon, command=kill_process)
    stp_btn.pack(side=tk.LEFT)
    Tooltip(stp_btn, "Stop a command")
    
    about_icon = PhotoImage(file=os.path.join(BASE_DIR, "about.png"))  # Keep references global
    about_btn = ttk.Button(button_frame, image=about_icon, command=open_about_window)
    about_btn.pack(side=tk.LEFT)
    Tooltip(about_btn, "About")
    
    settings_icon = PhotoImage(file=os.path.join(BASE_DIR, "settings.png"))  # Keep references global
    settings_btn = ttk.Button(button_frame, image=settings_icon, command=open_settings_window)
    settings_btn.pack(side=tk.LEFT)
    Tooltip(settings_btn, "Settings")
    
    show_icon = PhotoImage(file=os.path.join(BASE_DIR, "show.png"))  # Keep references global
    hide_icon = PhotoImage(file=os.path.join(BASE_DIR, "hide.png"))  # Keep references global
    toggle_btn = ttk.Button(button_frame, image=hide_icon, command=toggle_console)
    toggle_btn.pack(side=tk.LEFT)
    Tooltip(toggle_btn, "Show/Hide console")
    
    ttk.Button(right_frame, text="Clear Console", command=clear_console).pack(pady=(0, 6))

    console_visible = tk.BooleanVar(value=True)
    
    root.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))

    


    listbox_frame = tk.Frame(left_frame)
    listbox_frame.pack(fill=tk.BOTH, expand=True)
    progress_container = tk.Frame(listbox_frame, height=8)
    progress_container.pack(side=tk.BOTTOM, fill=tk.X)
    progress_container.pack_propagate(False)

    progressvar = tk.IntVar()
    progress = ttk.Progressbar(progress_container, variable=progressvar, length=335)
    progress.pack(side=tk.LEFT, fill=tk.NONE)
    progress.step(0)    
        
    xscroll = tk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL)
    xscroll.pack(side=tk.BOTTOM, fill=tk.X)
    
    yscroll = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    yscroll.pack(side=tk.RIGHT, fill=tk.Y)

    profile_listbox = tk.Listbox(
        listbox_frame,
        xscrollcommand=xscroll.set,
        yscrollcommand=yscroll.set,
        width=40
    )
    profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    profile_listbox.bind("<Double-Button-1>", on_profile_double_click)

    xscroll.config(command=profile_listbox.xview)
    yscroll.config(command=profile_listbox.yview)


  # --- RIGHT FRAME WIDGETS (CONSOLE) ---
    console_visible = tk.BooleanVar(value=True)
    root.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))

    # --- This is the main console output display ---
    console_output = scrolledtext.ScrolledText(
        right_frame, wrap=tk.WORD, bg="black", fg="lightgray",
        insertbackground="white", font=("Consolas", 10)
    )
    console_output.pack(fill=tk.BOTH, expand=True)
    console_output.configure(state='disabled') # Disabled to prevent direct typing


    
    console_input_entry = ttk.Entry(
        right_frame,
        font=("Consolas", 10),
    )
    console_input_entry.pack(fill=tk.X, pady=(5,0))
    console_input_entry.bind("<Return>", send_to_process) # Bind Enter key
    
    console_output.pack(fill=tk.BOTH, expand=True)
    console_output.configure(state='disabled')
    # Configure tags for different types of output (cmd.exe style colors)
    console_output.tag_config("error", foreground="#FF6B6B")      # Light red for errors
    console_output.tag_config("warning", foreground="#FFD93D")    # Yellow for warnings  
    console_output.tag_config("download", foreground="#6BCF7F")   # Light green for downloads
    console_output.tag_config("progress", foreground="#4ECDC4")   # Cyan for progress
    console_output.tag_config("info", foreground="lightgray")     # Default light gray
    console_output.tag_config("user_input", foreground="#82CFD8") # Color for user's echoed input


    style = ttk.Style()
    style.configure('TButton', padding=6, font=('Segoe UI', 10))
   
    refresh_profiles()
    root.mainloop()   