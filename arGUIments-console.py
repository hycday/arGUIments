import os
import subprocess
import json
import configparser
import sys
import shlex

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(".")
    
    
PROFILE_FILE = "profiles.json"
SETTINGS_FILE = "settings.ini"


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
    
def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    return {}
    
profiles = load_profiles()
settings = load_settings()

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