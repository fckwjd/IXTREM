# Written by Franck Wojda with Python 3.4
# IXTREM, 16th December 2015
# Version: 1.0.4
#
# ****************************************
# *              TestCOM                 *
# ****************************************

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from time import sleep
import tkinter.scrolledtext as tkst
from serial import Serial, SerialException
from queue import Queue
import string
from threading import Thread
import os.path
import sys
import glob
import re
import eventlet.timeout as timeout


# ! python

def vp_start_gui():
    #  Create Main window + icon
    global val, w, root
    root = Tk()
    root.title('TestCOM')
    geom = "300x210+626+254"
    root.geometry(geom)
    root.minsize(400, 330)
    root.maxsize(400, 330)
    logopath = 'images\\' + 'logo_ixtrem_blanc.gif'
    img = PhotoImage(file=logopath)
    root.tk.call('wm', 'iconphoto', root._w, img)
    w = GUI(root)
    # Call _quitApp if the window is closed using 'X' in order to close the COM port properly
    root.protocol('WM_DELETE_WINDOW', w._quitApp)
    root.mainloop()


class GUI(ttk.Frame):
    def __init__(self, parent, name='TestCOM'):
        # Initialize the GUI class
        ttk.Frame.__init__(self)
        self.pack(expand=N, fill=BOTH)
        self.parent = parent
        self.parent.title("TestCOM V1.0.3")
        self.fname = ""
        self.fileObj = None
        self.data = []
        self.started = False
        self.QUIT = False
        self.Saving = False
        self.validate = False
        self.size = 0
        self.Combo_value = ''
        self.baudrate = ['110', '300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400',
                         '56000', '57600', '115200', '128000', '153600', '230400', '256000', '460800', '921600']
        self._createPanel(self)

    def _process_serial(self):
        # Get values from the serial port, set it in Table and save it in file if asked
        try:
            # Check if Acquisition started
            if self.started:
                if self.queue.empty() == False:
                    self.data = self.queue.get()
                    self._fillScrolledText(self.list, self.data)
                    self._saveFile(self.fileObj, self.data)
                self.after(100, self._process_serial)
            else:
                self.after(100, self._process_serial)
        except:
            pass

    def _createPanel(self, parent):
        # Create Front panel frames
        logoFrame = Frame(self)
        logoFrame.pack(side=TOP, fill=BOTH, expand=N)

        self.panel = Frame(self)
        self.panel.pack(side=TOP, fill=BOTH, expand=N)

        self.panel2 = Frame(self)
        self.panel2.pack(side=TOP, fill=BOTH, expand=N)

        # Create Logo frame
        self._createLogo(logoFrame)

        # Create Button frame
        self._createButton(self.panel, parent)

        # Create ScrolledText
        self.list = self._createScrolledText(self.panel2)

        self.port = self._serial_ports()
        if self.port != []:
            # Create the combo boxes
            self._createCombo(self.panel, self.port)
            self.comboBaud = self._createComboBaudrate(self.panel, self.baudrate)

            # Create the queue
            self.queue = Queue()

            # Set and start the thread
            self.thread = Acquisition(self.queue, self.port[self.Combo.current()])
            self.thread.start()
            self._process_serial()
        else:
            self.buttonStart.config(state='disabled')
            self.buttonStop.config(state='disabled')
            self.buttonBrowse.config(state='disabled')
            self.buttonQuit.config(state='enable')

    def _createLogo(self, parent):
        # Create the logo on top of the application
        logopath = 'images\\' + 'logo_ixtrem_blanc.gif'
        self.img = PhotoImage(file=logopath)
        canvas = Canvas(parent, width=300, height=50)
        canvas.create_image(150, 0, anchor=N, image=self.img)
        canvas.pack()

    def _createButton(self, parent, window):
        # Create the buttons of the application
        buttonFrame = ttk.Frame(parent)
        buttonFrame.pack(side=TOP, fill=BOTH, expand=Y)

        # Set style to Button
        style = ttk.Style()
        style.theme_use('vista')
        style.map("C.TButton", foreground=[('pressed', 'red'), ('active', 'blue')],
                  background=[('pressed', '!disabled', 'black'), ('active', 'white')])

        # Set Buttons commands
        self.buttonStart = ttk.Button(self, text="Start", command=self._onStartClick, style="C.TButton", width=15)
        self.buttonStop = ttk.Button(self, text="Stop", state='disabled', command=self._onStopClick, style="C.TButton",
                                     width=15)
        self.buttonQuit = ttk.Button(self, text="Quit", command=self._quitApp, style="C.TButton", width=15)
        self.buttonBrowse = ttk.Button(self, text="Browse", command=self._load_file, style="C.TButton", width=15)

        # Set Button positions
        self.buttonStart.grid(in_=buttonFrame, row=0, column=0, sticky=(W, E))
        self.buttonStop.grid(in_=buttonFrame, row=0, column=1, sticky=(W, E))
        self.buttonQuit.grid(in_=buttonFrame, row=0, column=2, sticky=(W, E))
        self.buttonBrowse.grid(in_=buttonFrame, row=1, column=0, sticky=(W, E))

        # Set frame resizing priorities
        buttonFrame.rowconfigure(0, weight=1)
        buttonFrame.columnconfigure(0, weight=1, minsize=50)
        buttonFrame.columnconfigure(1, weight=1, minsize=50)
        buttonFrame.columnconfigure(2, weight=1, minsize=50)

    def _createLabel(self, parent, Label):
        # Create Labels to name the sensors tables
        LabelFrame = ttk.Frame(parent)
        LabelFrame.pack(side=TOP, fill=BOTH, expand=Y)
        self.Lbl = ttk.Label(self, text=Label)
        self.Lbl.grid(in_=LabelFrame, row=0, column=0, sticky=(N, S, E, W))

    def _createCombo(self, parent, Ports):
        # Create a combobox filled with available COM ports
        comboFrame = ttk.Frame(parent)
        self.Combo_value = StringVar()
        comboFrame.pack(side=TOP, fill=BOTH, expand=Y)
        style = ttk.Style()
        style.theme_settings("default", {"TCombobox": {"configure": {"padding": 5}, "map": {
            "background": [("active", "green2"), ("!disabled", "green4")], "fieldbackground": [("!disabled", "green3")],
            "foreground": [("focus", "OliveDrab1"), ("!disabled", "OliveDrab2")]}}})

        # Label for the combo box
        self.Lbl = ttk.Label(self, text='COM port:')
        self.Lbl.grid(in_=comboFrame, row=0, column=0, sticky=(W, E), ipadx=10)

        # Create and set the values of the combobox
        self.Combo = ttk.Combobox(self, textvariable=self.Combo_value, state='readonly')
        self.Combo.bind('<<ComboboxSelected>>', self._comboEvent)
        self.Combo['values'] = Ports
        self.Combo.current(0)
        self.Combo.grid(in_=comboFrame, row=0, column=2, sticky=(W, E), ipadx=10)

        # Set frame resizing priorities
        comboFrame.rowconfigure(0, weight=1)
        comboFrame.columnconfigure(0, weight=1)
        comboFrame.columnconfigure(2, weight=2)

    def _createComboBaudrate(self, parent, baudrate):
        # Create a combobox filled with baudrates
        combobaudFrame = ttk.Frame(parent)
        self.Combobaud_value = StringVar()
        combobaudFrame.pack(side=TOP, fill=BOTH, expand=Y)
        style = ttk.Style()
        style.theme_settings("default", {"TCombobox": {"configure": {"padding": 5}, "map": {
            "background": [("active", "green2"), ("!disabled", "green4")], "fieldbackground": [("!disabled", "green3")],
            "foreground": [("focus", "OliveDrab1"), ("!disabled", "OliveDrab2")]}}})

        # Label for the combo box
        self.Lblbaud = ttk.Label(self, text='Baudrate:  ')
        self.Lblbaud.grid(in_=combobaudFrame, row=0, column=0, sticky=(W, E), ipadx=10)

        # Create and set the values of the combobox
        self.Combobaud = ttk.Combobox(self, textvariable=self.Combobaud_value, state='readonly')
        self.Combobaud.bind('<<ComboboxSelected>>', self._combobaudEvent)
        self.Combobaud['values'] = baudrate
        self.Combobaud.current(6)
        self.Combobaud.grid(in_=combobaudFrame, row=0, column=2, sticky=(W, E), ipadx=10)

        # Set frame resizing priorities
        combobaudFrame.rowconfigure(0, weight=1)
        combobaudFrame.columnconfigure(0, weight=1)
        combobaudFrame.columnconfigure(2, weight=2)

    def _createScrolledText(self, parent):
        # Create ScrolledText which contains the data displayed on the screen
        ListFrame = ttk.Frame(parent)
        self.List = tkst.ScrolledText(parent, wrap=WORD)
        self.List.pack(padx=0, pady=0, fill=BOTH, expand=True)
        return self.List

    def _fillScrolledText(self, parent, data):
        parent.insert(INSERT, data)

    def _comboEvent(self, event):
        self.thread.portCOM = self.port[self.Combo.current()]

    def _combobaudEvent(self, event):
        self.thread.baudrate = self.baudrate[self.Combobaud.current()]

    def _quitApp(self):
        # Called when the Quit button is called. Close the thread and destroy the GUI
        try:
            self.thread.stop()
        except:
            pass
        self.QUIT = False
        self._destroyGUI(self)

    def _onStartClick(self):
        # Called when Start button is pressed. Start the Acquisition
        # Get the data in the queue
        try:
            self.size = self.queue.qsize()
            for count in range(self.size - 1):
                self.queue.get()

            # Disable buttons not needed during the Acquisition
            self.buttonStart.config(state='disabled')
            self.buttonQuit.config(state='disabled')
            self.Combo.config(state='disabled')
            self.Combobaud.config(state='disabled')
            self.buttonStop.config(state='normal')

            # Check if a file will be saved and fill fileObj
            if self.Saving:
                self.buttonBrowse.config(state='disabled', text='Saving...')
            else:
                self.buttonBrowse.config(state='disabled', text='Browse')

            self.fileObj = self._createFile(self.fname)

            # Start the acquisition of the data
            self.started = True
            self._process_serial()
        except:
            pass

    def _onStopClick(self):
        # Called when Stop button is pressed. Stop the Acquisition
        # Enable and Disable buttons not needed during the break
        self.buttonStart.config(state='normal')
        self.buttonBrowse.config(state='normal', text='Browse')
        self.buttonQuit.config(state='normal')
        self.buttonStop.config(state='disabled')
        self.Combo.config(state='normal')
        self.Combobaud.config(state='normal')

        self.Saving = False
        self.started = False

        # Close the text file that may have been opened
        self.fname = ""
        self._closeFile(self.fileObj)

    def _load_file(self):
        # Open the file browser and return the path location if a file path is choosen
        self.fname = ""
        self.fname = filedialog.asksaveasfilename(title='Choose text file', initialdir="C:/", defaultextension='.txt')
        if self.fname is "":
            self.Saving = False
            self.buttonBrowse.config(text="Browse")
            return
        else:
            self.Saving = True
            self.buttonBrowse.config(text="Ready")

    def _createFile(self, fname):
        # Create a file text at the location specified in fname. Write the header
        self.fname = fname
        if self.fname != None:
            if os.access(os.path.dirname(self.fname), os.W_OK):
                self.fileObj = open(self.fname, mode='w')
                return self.fileObj

    def _saveFile(self, fileObj, data):
        # Write data in the text file
        self.data = data
        self.fileObj = fileObj
        if self.fileObj != None:
            self.fileObj.write(str(self.data) + '\n')

    def _closeFile(self, fileObj):
        # Close the text file
        self.fileObj = fileObj
        if self.fileObj != None:
            self.fileObj.close()

    def _destroyGUI(self, parent):
        parent.destroy()
        os._exit(1)

    def _serial_ports(self):
        # Lists serial ports
        # :raises EnvironmentError:
        # On unsupported or unknown platforms
        # :returns:
        # A list of available serial ports
        if sys.platform.startswith('win'):
            self.ports = ['COM' + str(i + 1) for i in range(256)]
        elif sys.platform.startswith('linux'):
            self.temp_list = glob.glob('/dev/tty[A-Za-z]*')
            self.result = []
            for a_port in self.temp_list:
                try:
                    self.s = Serial(a_port)
                    self.s.close()
                    self.result.append(a_port)
                except SerialException:
                    pass
        elif sys.platform.startswith('darwin'):
            self.ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        self.result = []
        for port in self.ports:
            try:
                self.s = Serial(port)
                self.s.close()
                self.result.append(port)
            except (OSError, SerialException):
                pass
        return self.result


class Acquisition(Thread):
    # Thread class running in parallel of the main class. Prevent any freeze
    def __init__(self, queue, port='COM9'):
        # Initialize the class
        Thread.__init__(self)
        self.Out = False
        self.dataList = []
        self.queue = queue
        self.portCOM = port
        self.portCOM_old = ''
        self.acq = False
        self.runCOM = True
        self.baudrate = '9600'

    def run(self):
        # Run continuously when the application is launched
        while self.runCOM:
            # Check if the COM port value is valid
            if str(self.portCOM)[0:3] == 'COM':
                try:
                    # Check if the baudrate is working with the device, otherwise timeout
                    timeOut = timeout.Timeout(0.1)
                    try:
                        # Initialize the serial connection
                        self.ser = Serial(self.portCOM, int(self.baudrate), timeout=None, xonxoff=False, rtscts=False,
                                          dsrdtr=False)
                        self.portCOM_old = self.portCOM
                        self.baudrate_old = self.baudrate
                        self.ser.flushInput()
                        self.ser.flushOutput()
                        self.acq = True
                    except:
                        self.acq = False
                        timeOut.cancel()

                    # Check if the COM port has been changed
                    while self.acq:
                        if self.portCOM == self.portCOM_old and self.baudrate == self.baudrate_old:
                            # Rearrange data
                            self.dataArrange()
                        else:
                            self.acq = False

                            self.portCOM_old = self.portCOM
                            self.baudrate_old = self.baudrate
                            self.ser.close()
                except:
                    pass
            sleep(0.1)

    def dataArrange(self):
        # Get the data string and put it in the right order
        self.out = False
        while self.out == False and self.portCOM == self.portCOM_old and self.baudrate_old == self.baudrate:
            self.bytesToRead = self.ser.inWaiting()
            if self.bytesToRead > 0:
                self.data = self.ser.readline()
                try:
                    self.data = self.data.decode("utf-8")
                    if len(self.data) > 0:
                        self.queue.put(self.data)
                        if self.runCOM:
                            self.out = False
                        else:
                            self.out = True
                except:
                    pass

    def stop(self):
        # Stop the Thread in order to close it properly
        try:
            self.ser.close()
            self.out = True
            self.runCOM = False
            self.acq = False
            self.Terminated = True
        except:
            self.out = True
            self.runCOM = False
            self.acq = False
            self.Terminated = True


if __name__ == "__main__":
    vp_start_gui()
