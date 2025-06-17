# arGUIments
Simplify execution of commands with arguments

## Purpose
Create profiles to ease up usage of softwares with command lines, so that you can re-use them more easily (and also via command lines which would work like a sort of alias of command lines).


## Usage
Launch with `python arGUIments.py` or `python arGUIments-console.py` (for the console version).

You can also compile it to an exe by having the *.ico and *.spec file in same folder as arGUIments.py and launching the file "pyinstaller arGUIments.spec". The output exe will be in the "dist" folder.
Then you simply execute the exe file to launch it.

![Image](https://i.imgur.com/ogsXwzX.gif)
![Image](https://i.imgur.com/WQGVBxK.gif)

## Config
A settings.ini file will be generated to adjust some settings.

```
[DEFAULT]
software_path = yt-dlp
output_flag = --output
output_folder = E:/arGUIments/test
filename_template = %(title)s.%(ext)s
show_hints = False
```

adjust "software_path" as per your install (this will be the default software for which you wish to create profiles).

"output_flag" will correspond to the default tag to enable output generation (depends on the software you use).

"output_folder" will be the folder in which you wish the output of your commands to be.

"filename_template" will be either a fixed name (eg. "output.csv" etc) or following an output template as per the software you use. The example provided is for 

"show_hints" to show or hide the hints that will be displayed when howevering some labels.


## Profiles
A profiles.json file will be generated once you create your first profile.
You can also manually create it, or import one by copying the file in same folder as the software.

```
{
  "format": {
    "display_name": "Show video format",
    "shortname": "format",
    "path_mode": "default",
    "program_path": "yt-dlp",
    "command_template": "-F {0}",
    "arg_names": [
      "Video link"
    ],
    "export_output_mode": "disable",
    "custom_output_flag": "",
    "export_mode": "software",
    "custom_output_folder": "",
    "filename_mode": "default",
    "custom_filename_template": ""
  }
}
```

"display_name" is the name that should be displayed in arGUIments.

"shortname" will be used to be passed as argument of arGUIments-console.exe (example : `arGUIments-console.exe format {insert_video_link}` to trigger the equivalent of running `yt-dlp -F {insert_video_link}`).
As you start having more complex command lines, arGUIments can become more useful.

"path_mode" can be default, custom. default will mean that "program_path" will be set to what is in settings, "custom" will allow a specific "program_path" for this profile.

"program_path" will be the path for the specific software to use for this profile.

"command_template" can accept multiple arguments (`{0}, {1}, etc`) as long as you have the same number of arg_names. Can be for example `-F {0}` where {0} will be a link to a video that will need to be provided when running the profile.

"arg_names"  will list out the names/sentences/words you wish to display in the prompt when running the profile, to give a hint on what should be entered by the user to run the profile properly. For example, for above command_template, the arg_name for {0] will be "Video link".

"export_output_mode" can be default, disable, or custom. This will allow to customize the value for "custom_output_flag". default will use the value from settings, custom will allow for a specific "custom_output_flag" for this profile, while disable will turn off this feature for this profile.

"custom_output_flag" will be the value of the tag to enable output generation (depends on the software you use). (example, for yt-dlp, the value should be `--output`)

"export_mode" can be "default", "variable" or "custom". This will allow to customize the value for "custom_output_folder". default will use the value from settings, "custom" will use the value from "custom_output_folder", and "software" will use the path from which arGUIments was ran from. Note that if you added the path in which arGUIments is installed in, to the PATH environment variable, this will also work (and the output will be in the path from which arGUIments or arGUIments-console was ran from.

"custom_output_folder" will be the path where to export/output the result of the profile.

"filename_mode" can be "default" or "custom". default will use the value from settings, and custom will use the value from "custom_filename_template". 

"custom_filename_template" will be the value for the filename (or filename template) to use for the output/export (example for yt-dlp, use `%(title)s.%(ext)s` to rename with the title of the video and the extension, removing everything else.

Note : you don't need to create your profiles.json manually, the GUI will do it for you. You can however adjust it manually (or programmatically) if you wish.
