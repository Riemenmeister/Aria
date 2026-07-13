## FileSystem
## This file contains some default directories of your system

import os
from pathlib import Path

## Special Directories
CurrentPath = os.getcwd()
User = str(Path.home()) + "\\"

Desktop = str(Path.home() / "Desktop") + "\\"
Documents = str(Path.home() / "Documents") + "\\"
Downloads = str(Path.home() / "Downloads") + "\\"
Music = str(Path.home() / "Music") + "\\"
Pictures = str(Path.home() / "Pictures") + "\\"

## Project Directories
PyBridgeFolder = Documents + "PyBridge\\"
ProjectsRepo = PyBridgeFolder + "Projects\\"
PythonExtension = ".py"
