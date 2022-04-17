from distutils.core import setup
import py2exe, sys, os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from time import sleep
import serial
import string
import threading
import queue
import os.path
import sys
import glob

sys.argv.append('py2exe')

Img_files = [('images', ["logo_ixtrem_blanc.gif", 'logo_ixtrem_blanc.ico'])]

setup(
    name="IMAGMETER",
    version="1.0.2",
    description="IMAGMETER PC DATA App",
    author="Franck Wojda",
    options={'py2exe': {'includes': ["sys", "string", "threading", "queue", "glob", "tkinter", 'os', "time"],
                        'bundle_files': 2}},
    data_files=Img_files,
    windows=[{'script': "IMAGMETER.py", 'icon_resources': [(1, 'logo_ixtrem_blanc.ico')]}],
    zipfile=None
)
