from distutils.core import setup
import py2exe, os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from time import sleep
from serial import Serial, SerialException
from queue import Queue
from threading import Thread
import string
import queue
import os.path
import sys
import glob
import re
import eventlet.timeout as timeout

sys.argv.append('py2exe')

Img_files = [('images', ["logo_ixtrem_blanc.gif", 'logo_ixtrem_blanc.ico'])]

setup(
    name="TESTEUR 4",
    version="1.0.4",
    description="TESTER 4 PC DATA App",
    author="Franck Wojda",
    options={'py2exe': {
        'includes': ["sys", "string", "threading", "queue", "glob", "tkinter", 'os', "time", "re", "serial",
                     "eventlet.timeout"], 'bundle_files': 2}},
    data_files=Img_files,
    windows=[{'script': "TESTER4.py", 'icon_resources': [(1, 'logo_ixtrem_blanc.ico')]}],
    zipfile=None,
)
