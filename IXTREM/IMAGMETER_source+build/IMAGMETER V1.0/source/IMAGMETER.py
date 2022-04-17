# Written by Franck Wojda with Python 3.4
# IXTREM, 15th July 2015
# Version: 1.0

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


def vp_start_gui():
    #  Create Main window + icon
    global val, w, root
    root = Tk()
    root.title('IMAGMETER')
    geom = "300x650+626+154"
    root.geometry(geom)
    logopath = 'images\\' + 'logo_ixtrem_blanc.gif'
    img = PhotoImage(file=logopath)
    root.tk.call('wm', 'iconphoto', root._w, img)
    w = GUI(root)
    root.mainloop()


w = None


def create_GUI(root, param=None):
    #   '''Starting point when module is imported by another program.'''
    global w, w_win, rt
    rt = root
    w = TopLevel(root)
    w.title('IMAGMETER')
    w_win = GUI(w)
    return w_win


def destroy_GUI():
    #  Destroy Main window
    root.destroy()


class GUI(ttk.Frame):
    def __init__(self, parent, name='IMAGEMETER'):
        # Initialize the GUI class
        ttk.Frame.__init__(self)
        self.pack(expand=Y, fill=BOTH)
        self.parent = parent
        self.parent.title("Imagmeter PC DATA V1.0")
        self.fname = ""
        self.fileObj = None
        self.data = defaultlist([])
        self.started = False
        self.QUIT = False
        self.Saving = False
        self.validate = False
        self.size = 0
        self.Combo_value = ''
        self._createPanel(self)

    def process_serial(self):
        # Get values from the serial port, set it in Table and save it in file if asked
        try:
            # Check if Acquisition started
            if self.started:
                self.data = self.queue.get()
                self.queue.empty()
                self.LoadTable(self.Table1, 0)
                self.LoadTable(self.Table2, 9)
                self.LoadTable(self.Table3, 18)
                self.saveFile(self.fileObj, self.data)
                self.after(200, self.process_serial)
            else:
                self.queue.empty()
        except self.queue.empty():
            pass

    def _createPanel(self, parent):
        # Create Front panel frames
        LogoFrame = Frame(self)
        LogoFrame.pack(side=TOP, fill=X, expand=N)

        Panel = Frame(self)
        Panel.pack(side=TOP, fill=BOTH, expand=Y)

        Panel2 = Frame(self)
        Panel2.pack(side=TOP, fill=BOTH, expand=Y)

        Panel3 = Frame(self)
        Panel3.pack(side=TOP, fill=BOTH, expand=Y)

        Panel4 = Frame(self)
        Panel4.pack(side=BOTTOM, fill=BOTH, expand=Y)

        # Create Logo frame
        self._createLogo(LogoFrame)

        # Create Button frame
        self._createButton(Panel, parent)

        # Create Labels	
        self._createLabel(Panel2, "Sensor 1 (kA / m):")
        self._createLabel(Panel3, "Sensor 2 (kA / m):")
        self._createLabel(Panel4, "Sensor 3 (kA / m):")

        # Create Treeviews		
        self.Table1 = self._createTreeview(Panel2)
        self.Table2 = self._createTreeview(Panel3)
        self.Table3 = self._createTreeview(Panel4)

        self.port = self.serial_ports()
        if self.port != []:
            self._createCombo(Panel, self.port)

            # set threading		
            self.queue = queue.Queue()

            self.thread = Acquisition(self.queue, self.port[self.Combo.current()])
            self.thread.start()
            self.process_serial()
        else:
            self.buttonStart.config(state='disabled')
            self.buttonStop.config(state='disabled')
            self.buttonBrowse.config(state='disabled')
            self.buttonQuit.config(state='disabled')

    def _createLogo(self, parent):
        # Create the logo on top of the application
        logopath = 'images\\' + 'logo_ixtrem_blanc.gif'
        self.img = PhotoImage(file=logopath)
        canvas = Canvas(parent, width=300, height=50)
        canvas.create_image(150, 0, anchor=N, image=self.img)
        canvas.pack()

    def _createButton(self, parent, window):
        # Create the buttons of the application
        ButtonFrame = ttk.Frame(parent)
        ButtonFrame.pack(side=TOP, fill=BOTH, expand=Y)
        # set style to Button		
        style = ttk.Style()
        style.map("C.TButton", foreground=[('pressed', 'red'), ('active', 'blue')],
                  background=[('pressed', '!disabled', 'black'), ('active', 'white')])

        # set Buttons commands
        self.buttonStart = ttk.Button(self, text="Start", command=self.OnStartClick, style="C.TButton")
        self.buttonStop = ttk.Button(self, text="Stop", state='disabled', command=self.OnStopClick, style="C.TButton")
        self.buttonQuit = ttk.Button(self, text="Quit", command=self.quitApp, style="C.TButton")
        self.buttonBrowse = ttk.Button(self, text="Browse", command=self.load_file, style="C.TButton")

        # set Button positions		
        self.buttonStart.grid(in_=ButtonFrame, row=0, column=0, sticky='W')
        self.buttonStop.grid(in_=ButtonFrame, row=0, column=0, sticky='N')
        self.buttonQuit.grid(in_=ButtonFrame, row=0, column=0, sticky='E')
        self.buttonBrowse.grid(in_=ButtonFrame, row=1, column=0, sticky='W')

        # set frame resizing priorities
        ButtonFrame.rowconfigure(0, weight=1)
        ButtonFrame.columnconfigure(0, weight=1)

    def _createTreeview(self, parent):
        # Create the treeview containing the values displayed
        TreeviewFrame = ttk.Frame(parent)
        TreeviewFrame.pack(side=BOTTOM, fill=BOTH, expand=Y)
        # create the tree 
        self.dataCols = ('DC', 'AC', 'AC+DC')
        self.tree = ttk.Treeview(columns=self.dataCols)

        # setup column headings
        self.tree.heading('#0', text='Axe', anchor=W)
        self.tree.column('#0', anchor=W, width=60)
        self.tree.heading('DC', text='DC', anchor=W)
        self.tree.column('#1', anchor='center', width=60)
        self.tree.heading('AC', text='AC', anchor=W)
        self.tree.column('AC', anchor='center', width=60)
        self.tree.heading('AC+DC', text='AC+DC', anchor=W)
        self.tree.column('AC+DC', anchor='center', width=60)

        # set row height
        style = ttk.Style()
        style.configure('Treeview', rowheight=15)

        # add tree and scrollbars to frame
        self.tree.grid(in_=TreeviewFrame, row=0, column=0, sticky=NSEW)

        # set frame resizing priorities
        TreeviewFrame.rowconfigure(0, weight=1)
        TreeviewFrame.columnconfigure(0, weight=1)
        return self.tree

    def _createLabel(self, parent, Label):
        # Create Labels to name the sensors tables
        LabelFrame = ttk.Frame(parent)
        LabelFrame.pack(side=TOP, fill=BOTH, expand=Y)
        self.Lbl = ttk.Label(self, text=Label)
        self.Lbl.grid(in_=LabelFrame, row=0, column=0, sticky=NSEW)

    def _createCombo(self, parent, Ports):
        # Create a combobox filled with available COM ports
        ComboFrame = ttk.Frame(parent)
        self.Combo_value = StringVar()
        ComboFrame.pack(side=TOP, fill=BOTH, expand=Y)
        style = ttk.Style()
        style.theme_settings("default", {"TCombobox": {"configure": {"padding": 5}, "map": {
            "background": [("active", "green2"), ("!disabled", "green4")], "fieldbackground": [("!disabled", "green3")],
            "foreground": [("focus", "OliveDrab1"), ("!disabled", "OliveDrab2")]}}})

        # Label for the combo box
        self.Lbl = ttk.Label(self, text='COM port:')
        self.Lbl.grid(in_=ComboFrame, row=0, column=0, sticky='W')

        # Create and set the values of the combobox
        self.Combo = ttk.Combobox(self, textvariable=self.Combo_value, state='readonly')
        self.Combo.bind('<<ComboboxSelected>>', self.comboEvent)
        self.Combo['values'] = Ports
        self.Combo.current(0)
        self.Combo.grid(in_=ComboFrame, row=0, column=0, sticky='E')

        # set frame resizing priorities
        ComboFrame.rowconfigure(0, weight=1)
        ComboFrame.columnconfigure(0, weight=1)

    def comboEvent(self, event):
        self.thread.portCOM = self.port[self.Combo.current()]

    def LoadTable(self, Table, Sensor):
        # Put data coming from the COM port in the tables
        # Delete first old data present in the table
        for i in Table.get_children():
            Table.delete(i)
        # Fill the table
        Table.insert('', 'end', text="X", values=(self.data[0 + Sensor], self.data[1 + Sensor], self.data[2 + Sensor]))
        Table.insert('', 'end', text="Y", values=(self.data[3 + Sensor], self.data[4 + Sensor], self.data[5 + Sensor]))
        Table.insert('', 'end', text="Z", values=(self.data[6 + Sensor], self.data[7 + Sensor], self.data[8 + Sensor]))

    def quitApp(self):
        # Called when the Quit button is called. Close the thread and destroy the GUI
        self.QUIT = False
        self.thread.stop()
        destroy_GUI()

    def OnStartClick(self):
        # Called when Start button is pressed. Start the Acquisition
        # Get the data in the queue
        count = 0
        self.size = self.queue.qsize()
        for count in range(self.size - 1):
            self.queue.get()

        # Disable buttons not needed during the Acquisition
        self.buttonStart.config(state='disabled')
        self.buttonQuit.config(state='disabled')
        self.Combo.config(state='disabled')
        self.buttonStop.config(state='normal')

        # Check if a file will be saved and fill fileObj
        if self.Saving:
            self.buttonBrowse.config(state='disabled', text='Saving...')
        else:
            self.buttonBrowse.config(state='disabled', text='Browse')

        self.fileObj = self.createFile(self.fname)

        # Start the acquisition of the data
        self.started = True
        self.process_serial()

    def OnStopClick(self):
        # Called when Stop button is pressed. Stop the Acquisition
        # Enable and Disable buttons not needed during the break
        self.buttonStart.config(state='normal')
        self.buttonBrowse.config(state='normal', text='Browse')
        self.buttonQuit.config(state='normal')
        self.buttonStop.config(state='disabled')
        self.Combo.config(state='normal')

        self.Saving = False
        self.started = False

        # Close the text file that may have been opened
        self.fname = ""
        self.closeFile(self.fileObj)

    def load_file(self):
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

    def createFile(self, fname):
        # Create a file text at the location specified in fname. Write the header
        if fname != None:
            if os.access(os.path.dirname(fname), os.W_OK):
                fileObj = open(fname, mode='w')
                fileObj.write(
                    'PROBE 1' + '\t' + '\t' + '\t' + 'PROBE 1' + '\t' + '\t' + '\t' + 'PROBE 1' + '\t' + '\t' + '\t' + 'PROBE 2' + '\t' + '\t' + '\t' + 'PROBE 2' + '\t' + '\t' + '\t' + 'PROBE 2' + '\t' + '\t' + '\t' + 'PROBE 3' + '\t' + '\t' + '\t' + 'PROBE 3' + '\t' + '\t' + '\t' + 'PROBE 3' + '\n')
                fileObj.write(
                    'X DC\t' + 'X AC\t' + 'X AC+DC\t' + 'Y DC\t' + 'Y AC\t' + 'Y AC+DC\t' + 'Z DC\t' + 'Z AC\t' + 'Z AC+DC\t' + 'X DC\t' + 'X AC\t' + 'X AC+DC\t' + 'Y DC\t' + 'Y AC\t' + 'Y AC+DC\t' + 'Z DC\t' + 'Z AC\t' + 'Z AC+DC\t' + 'X DC\t' + 'X AC\t' + 'X AC+DC\t' + 'Y DC\t' + 'Y AC\t' + 'Y AC+DC\t' + 'Z DC\t' + 'Z AC\t' + 'Z AC+DC\n')
                return fileObj

    def saveFile(self, fileObj, data):
        # Write data in the text file
        if fileObj != None:
            l = 0
            for l in range(len(data) - 1):
                fileObj.write(str(data[l]) + '\t')
            fileObj.write(str(data[len(data) - 1]) + '\n')

    def closeFile(self, fileObj):
        # Close the text file
        if fileObj != None:
            fileObj.close()

    def destroyGUI(self, parent):
        print('OK')
        parent.destroy()

    def serial_ports(self):
        # Lists serial ports
        # :raises EnvironmentError:
        # On unsupported or unknown platforms
        # :returns:
        # A list of available serial ports
        if sys.platform.startswith('win'):
            ports = ['COM' + str(i + 1) for i in range(256)]
        elif sys.platform.startswith('linux'):
            temp_list = glob.glob('/dev/tty[A-Za-z]*')
            result = []
            for a_port in temp_list:
                try:
                    s = serial.Serial(a_port)
                    s.close()
                    result.append(a_port)
                except serial.SerialException:
                    pass
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result


class Acquisition(threading.Thread):
    # Thread class running in parallel of the main class. Prevent any freeze
    def __init__(self, queue, port='COM9'):
        # Initialize the class
        threading.Thread.__init__(self)
        self.col = 0
        self.Out = False
        self.dataArray = defaultlist([])
        self.datacol = [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25, 2, 5, 8, 11, 14, 17, 20, 23,
                        26]
        self.queue = queue
        self.portCOM = port
        self.portCOM_old = ''
        self.Acq = True
        self.runCOM = True

    def run(self):
        # Run continuously when the application is launched
        while self.runCOM:
            # Check if the COM port value is valid
            if str(self.portCOM)[0:3] == 'COM':
                try:
                    self.ser = serial.Serial(self.portCOM, timeout=None, xonxoff=False, rtscts=False, dsrdtr=False)
                    self.portCOM_old = self.portCOM
                    self.ser.flushInput()
                    self.ser.flushOutput()
                    self.bytesToRead = self.ser.inWaiting()
                    self.data = self.ser.read(self.bytesToRead)
                    self.data = self.data.decode("utf-8")
                    self.Acq = True
                    # Check if the COM port has been changed
                    while self.Acq:
                        if self.portCOM == self.portCOM_old:
                            # Rearrange data
                            self.dataArrange()
                        else:
                            self.Acq = False
                            self.portCOM_old = self.portCOM
                            self.ser.close()
                except:
                    pass
            sleep(0.2)

    def dataArrange(self):
        # Get the data string and put it in the right order
        self.Out = False
        while self.Out == False and self.portCOM == self.portCOM_old:
            self.bytesToRead = self.ser.inWaiting()
            self.data = self.ser.readline()
            try:
                self.data = self.data.decode("utf-8")
                if len(self.data) > 0 & self.data.find('\r') >= 0:
                    if (self.data.find('[') >= 0):
                        self.data = self.data.replace('[', '')
                        self.col = 0
                        self.dataArray = defaultlist([])
                    if (self.data.find(']') >= 0):
                        self.data = self.data.replace(']', '')
                    if (self.data.find('\r') >= 0):
                        self.data = self.data.replace('\r', '')
                    if (self.data.find('\n') >= 0):
                        self.data = self.data.replace('\n', '')

                    self.dataArray[self.datacol[self.col]] = self.data
                    self.col = self.col + 1
                    if len(self.dataArray) == 27:
                        self.Out = True
                        j = 0
                        for j in range((len(self.dataArray) - 1)):
                            if type(self.dataArray[j]) != str:
                                self.Out = False
                                break
                        if self.Out:
                            self.queue.empty()
                            self.queue.put(self.dataArray)
                            if self.RunCOM:
                                self.Out = False
                            else:
                                self.Out = True
                            self.dataArray = defaultlist([])
            except:
                pass

    def stop(self):
        # Stop the Thread in order to close it properly
        self.ser.close()
        self.Out = True
        self.RunCOM = False
        self.Acq = False
        self.Terminated = True


class defaultlist(list):
    # Allow the list to be expanded
    def __setitem__(self, index, value):
        size = len(self)
        if index >= size:
            self.extend(0 for _ in range(size, index + 1))
        list.__setitem__(self, index, value)


if __name__ == "__main__":
    vp_start_gui()
    os._exit(1)
