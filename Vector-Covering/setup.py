from cx_Freeze import setup, Executable
import pygame, math, time, random, copy, sys
from pygame.locals import *
from collections import OrderedDict

base = None
if sys.platform == 'win32':
    base = "Win32GUI"

executables = [Executable("NodeCoveringAlgo.py", base=base, icon = 'Auxo_Logo.ico')]

setup(
    name = "Project Auxo Network Covering",
    version = "0.8",
    author = "Project Auxo Apollo",
    license = "Project Auxo",
    options = {"build_exe": {"packages":["pygame", "math", "time", "random", "copy", "collections"], "include_files":["Auxo_Logo.ico","Auxo_Logo_Black.png"]}},
    description = "Project Auxo Node Covering Application",
    executables = executables
)
