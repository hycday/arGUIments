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
    # config = configparser.ConfigParser()
    config = configparser.ConfigParser(interpolation=None)
    if not os.path.exists(SETTINGS_FILE):
        config['DEFAULT'] = {
            'software_path': 'yt-dlp',
            'output_flag': '--output',
            'output_folder': '',
            'filename_template': '%(title)s.%(ext)s',
            # 'use_custom_output': 'False'
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

    command_template = profile['command_template']
    try:
        args = shlex.split(command_template.format(*user_args))
    except IndexError as e:
        raise ValueError(f"Missing arguments: {e}")

    path_mode = profile.get("path_mode", "default")
    
    if path_mode == "default":
        software_path = settings['DEFAULT'].get('software_path')
    elif path_mode == "custom":
        software_path = profile.get("program_path")
    
    if not software_path:
        raise ValueError("Software path is not defined in settings or in profile.")
    
    command = [software_path] + args


    flag = None
    exportmode = profile.get("export_output_mode")
    if exportmode == "default":
        flag = settings['DEFAULT'].get('output_flag')
    elif exportmode == "custom":
        flag = profile.get("custom_output_flag")       
    
    folder = None
    mode = profile.get("export_mode", "default")
    if mode == "default":
        folder = settings['DEFAULT'].get('output_folder')
    elif mode == "software":
        folder = ''
    elif mode == "custom":
        folder = profile.get("custom_output_folder", "")        
        
    template = None
    template_name = profile.get("filename_mode")
    if template_name == "default":
        template = settings['DEFAULT'].get('filename_template')
    elif template_name == "custom":
        template = profile.get("custom_filename_template")       
        
        
    if exportmode != "disable":
        if folder == "":
            command += [flag, f"{template}"]
        else:
            command += [flag, f"{folder}/{template}"]
        
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