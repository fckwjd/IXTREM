from distutils.core import setup
# from cx_Freeze import setup, Executable
import py2exe
# import tkinter
# import tkinter
# import tkinter.ttk
# from tkinter import filedialog
# import ast
# import carto3Dcam
# import canvasplot
# import configparser
# import callbacktasksynchronous
# import cv2
# import cameractrl
# import cameraundistort
# import importlib
# import matplotlib
# matplotlib.use('TkAgg')
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib import cm
# import matplotlib.pyplot as plt
# from matplotlib.figure import Figure
# import mousepositionanalysis
# import numpy
# import os
# import pywin
# import PyDAQmx
# import queue
# import scipy
# from scipy.interpolate import griddata
import sys
# import threading
# import time
import glob

sys.argv.append('py2exe')

Img_files = [('logo', [
    "C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\logo\\logo_ixtrem_blanc.gif",
    'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\logo\\logo_ixtrem_blanc.ico'],
              'chessboard', [
                  'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\chessboard\\chess1.png',
                  'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\chessboard\\chess2.png',
                  'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\chessboard\\chess3.png',
                  'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\chessboard\\chess4.png'])]
includes = ["ast", "configparser", "cv2", "matplotlib", "numpy", "os", "PyDAQmx", "queue", "scipy", "sys", "threading",
            "time", "tkinter", "tkinter.ttk", "matplotlib.backends.backend_tkagg", "matplotlib.pyplot",
            "tkinter.filedialog", "matplotlib.figure", "os", "scipy.interpolate"
            ]
modules = ["mousepositionanalysis", "carto3Dcam", "canvasplot", "callbacktasksynchronous", "cameractrl",
           "cameraundistort"]
# datafiles = [("Microsoft.VC90.CRT", glob(r'C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*'))]
# datafiles.extend(matplotlib.get_py2exe_datafiles()) 

# setup(windows=['main.py'], data_files= datafiles, options={"py2exe": {"includes": ["matplotlib"]}})

setup(
    name="MagCarto",
    version="1.0.0",
    description="MagCarto App",
    author="Franck Wojda",
    options={'py2exe': {'includes': includes,
                        'bundle_files': 2,
                        'excludes': [],
                        'optimize': 2,
                        'compressed': True}},
    # data_files =[ Img_files],
    # data_files= datafiles,
    windows=[{'script': "GUI_Camera_Cartography_Thread.py",
              'icon_resources': [(1,
                                  'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Tests\\Camera\\Scanner\\logo\\logo_ixtrem_blanc.ico')]}],
    zipfile=None
)

# cx_Freeze version
# setup(
# name = "CartoMag",
# version = "1.0",
# description = "Magnet mapping using camera and sensors",
# executables = [Executable("GUI_Camera_Cartography_Thread.py", base = "Win32GUI")])
