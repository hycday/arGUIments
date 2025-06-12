# arGUIments
Simplify execution of commands with arguments

## Purpose



## Usage
Launch with `python arGUIments.py` or `python arGUIments-console.py` (for the console version).

You can also compile it to an exe by having the *.ico and *.spec file in same folder as arGUIments.py and launching the file "build-exe.bat". The output exe will be in the "dist" folder.
Then you simply execute the exe file to launch it.

![Image](https://i.imgur.com/ogsXwzX.gif)
![Image](https://i.imgur.com/WQGVBxK.gif)

## Config
A settings.ini file will be generated to adjust some settings.

```
[DEFAULT]
software_path = yt-dlp
output_folder = 
use_custom_output = False
```

adjust "software_path" as per your install (this will be the default software for which you wish to create profiles).

adjust "output_folder" will be the folder in which you wish the output of your commands to be.

adjust "use_custom_output" to True if you wish to use the output_folder path (otherwise it will use the folder from which you call arGUIments.exe). 


## Profiles
A profiles.json file will be generated once you create your first profile.
You can also manually create it, or import one by copying the file in same folder as the software.

```
{
  "format": {
    "display_name": "Show video format",
    "shortname": "format",
    "command_template": "-F {0}",
    "custom_path": "",
    "arg_names": [
      "Video link"
    ],
    "export_mode": "default",
    "custom_export_path": "",
    "custom_output_flag": ""
  }
}
```

shortname will be used to be passed as argument of arGUIments-console.exe (example : `arGUIments-console.exe format {insert_video_link}` to trigger the equivalent of running `yt-dlp -F {insert_video_link}`).
As you start having more complex command lines, arGUIments can become more useful.

command_template can accept multiple arguments (`{0}, {1}, etc`) as long as you have the same number of arg_names.

custom_path is optional, in case you wish to have another software_path for this specific profile.

export_mode will use the output_folder as per the settings, and will be setup to default to yt-dlp output command (`--output`). In case you wish to adjust yours for this profile, adjust the custom_export_path and custom_output_flag (mode will be `custom`).

Note : you don't need to create your profiles.json manually, the GUI will do it for you. You can however adjust it manually (or programmatically) if you wish.
