#Written by Franck Wojda with Python 3.4
#IXTREM, 22nd October 2015
#Version: 1.0.1
#
#****************************************
#*              TESTER4                 *
#****************************************

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from time import sleep
from serial import Serial, SerialException
from queue import Queue
from threading import Thread
import string
import os.path
import sys
import glob
import re
import eventlet.timeout as timeout
#! python

def vp_start_gui():
#Create Main window + icon
    global w, root
    root = Tk()
    root.title('TESTER 4')
    geom = "380x250+626+254"
    root.geometry(geom)
    root.minsize(380, 250)
    root.maxsize(380, 250)
    logopath = 'images\\'+'logo_ixtrem_blanc.gif' 
    img = PhotoImage(file=logopath)
    root.tk.call('wm', 'iconphoto', root._w, img)
    w = GUI(root)
    root.mainloop()

w = None
def create_GUI(root, param=None):
    '''Starting point when module is imported by another program.'''
    global w, w_win, rt
    rt = root
    w = TopLevel(root)
    w.title('TESTER 4')
    w_win = GUI(w)
    return w_win

class GUI(ttk.Frame):
    def __init__(self, parent, name='TESTER 4'):
		#Initialize the GUI class
        ttk.Frame.__init__(self)
        self.grid(row = 0, column = 0, sticky = (N, E, S, W))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.parent = parent
        self.parent.title("TESTER 4 PC DATA V1.0.1")		
        self.fname = ""
        self.fileObj = None
        self.data = []
        self.dataHold = []
        self.started = False
        self.QUIT = False		
        self.Saving = False
        self.validate = False
        self.size = 0
        self.Combo_value = ''
        self._createPanel(self)
        self.bar = self._menuBar(self)
        
    def _process_serial(self):
		#Get values from the serial port, set it in Table and save it in file if asked
        try:
			#Check if Acquisition started
            if self.started:
                if self.queue.empty() == False:
                    self.data = self.queue.get()			
                    self._loadTable(self.table1)
                    self._saveFile(self.fileObj, self.data)                                    
                # self.after(50, self._process_serial)
            if self.queueHold.empty() == False:
                self.dataHold = self.queueHold.get()
            
            timeOut = timeout.Timeout(0.04)
            try:                
                self._loadHoldTable(self.top.treeHold, self.dataHold)
            except:
                timeOut.cancel()
                    
            # self._loadHoldTable(self.top.treeHold, self.dataHold)
            
            self.after(50, self._process_serial)            
        except:
            pass
    
    def _createPanel(self, parent):
		#Create Front panel frames
        logoFrame = Frame(self)
        logoFrame.grid(row = 0, column = 0 , sticky = (N, E, S, W))
		
        panel = Frame(self)
        panel.grid(row = 1, column = 0 , sticky = (N, E, S, W))
		
        panel2 = Frame(self)
        panel2.grid(row = 2, column = 0 , sticky = (N, E, S, W))
		
        #Create Logo frame
        self._createLogo(logoFrame)
		
        #Create Button frame
        self._createButton(panel, parent)
		
        #Create Labels	
        self._createLabel(panel2, "TESTER 4 sensor data:")
		
        #Create main window Treeview		
        self.table1 = self._createTreeview(panel2)
		
        self.port = self._serial_ports()
         
        if self.port != []:	
            self._createCombo(panel, self.port)	    						
            #Set threading		
            self.queue = Queue()
            self.queueHold = Queue()
            
            self.thread = Acquisition(self.queue, self.queueHold, self.port[self.Combo.current()])
            self.thread.start()
            self._process_serial()
        else:
            self.buttonStart.config(state = 'disabled')
            self.buttonStop.config(state = 'disabled')				
            self.buttonBrowse.config(state = 'disabled')
            self.buttonQuit.config(state = 'enable')				
    
    def _menuBar(self, parent):
        #Create a menu bar containing the different available options in the main window
        menubar = Menu(self)
        
        #Create the sub menu "File"
        filemenu = Menu(menubar, tearoff = 0)    
        # filemenu.add_separator()
        filemenu.add_command(label = "Exit", command = self._quitApp)
        menubar.add_cascade(label = "File", menu = filemenu)
        
        #Create the sub menu "Hold values"
        holdmenu = Menu(menubar, tearoff = 0)      
        self.tableHold = holdmenu.add_command(label = "Display hold values...", command = self._create_toplevel)
        holdmenu.add_command(label = "Save hold values", command = self._saveHoldFile)
        menubar.add_cascade(label = "Hold values", menu = holdmenu) 
        
        Tk.config(root, menu = menubar)
        # self.tableHold = self._create_toplevel
        return self._create_toplevel
        
    def _create_toplevel(self):
        self.top = Toplevel()

        #Create the tree 
        self.top.dataHoldTree = ('Mode','Value','Units')
        self.top.treeHold = ttk.Treeview(self.top, columns = self.top.dataHoldTree)

        #Setup column headings
        self.top.treeHold.heading('#0', text = 'Hold number', anchor = 'center')
        self.top.treeHold.column('#0', anchor = 'center', width = 90)
        self.top.treeHold.heading('Mode', text = 'Mode', anchor = 'center')
        self.top.treeHold.column('#1', anchor = 'center', width = 140)
        self.top.treeHold.heading('Value', text = 'Value', anchor = 'center')
        self.top.treeHold.column('#2', anchor = 'center', width = 60)
        self.top.treeHold.heading('Units', text = 'Units', anchor = 'center')
        self.top.treeHold.column('#3', anchor = 'center', width = 60)
        
        #Set row height
        style = ttk.Style()
        style.configure('Treeview', rowheight = 20)

        self.top.treeHold.configure(height = 10)
		
        #Add tree and scrollbars to frame
        self.top.treeHold.grid(row = 0, column = 0 , sticky = (N, E, S, W))

        #Set frame resizing priorities
        self.top.rowconfigure(0, weight = 1)
        self.top.columnconfigure(0, weight = 1)
        
        return self.top.treeHold
        
    def _createLogo(self, parent):
		#Create the logo on top of the application
        logopath = 'images\\'+'logo_ixtrem_blanc.gif' 
        self.img = PhotoImage(file = logopath)
        canvas = Canvas(parent, width = 376, height = 50)  
        canvas.create_image(195,0, anchor = N, image = self.img) 
        canvas.grid(row = 0, column = 0 , sticky = (N, E, S, W))
		
    def _createButton(self, parent, window):
		#Create the buttons of the application
        buttonFrame = ttk.Frame(parent)
        buttonFrame.pack(side = TOP, fill = BOTH, expand = Y)
        
        #Set style to Button		
        style = ttk.Style()
        style.theme_use('vista')
        style.map("C.TButton", foreground = [('pressed', 'red'), ('active', 'blue')], background = [('pressed', '!disabled', 'black'), ('active', 'white')]) 		

		#Set Buttons commands
        self.buttonStart = ttk.Button(self, text = "Start", command = self._onStartClick, style = "C.TButton", width = 15)
        self.buttonStop = ttk.Button(self, text = "Stop", state = 'disabled', command = self._onStopClick, style = "C.TButton", width = 15)
        self.buttonQuit = ttk.Button(self, text = "Quit", command = self._quitApp, style = "C.TButton", width = 15)		
        self.buttonBrowse = ttk.Button(self, text = "Browse", command = self._load_file, style = "C.TButton", width = 15)
		
        #Set Button positions		
        self.buttonStart.grid(in_ = buttonFrame, row = 0, column = 0, sticky = (W, E))
        self.buttonStop.grid(in_ = buttonFrame, row = 0, column = 1, sticky = (W, E))
        self.buttonQuit.grid(in_ = buttonFrame, row = 0, column = 2, sticky = (W, E))
        self.buttonBrowse.grid(in_ = buttonFrame, row = 1, column = 0, sticky = (W, E))
		
        #Set frame resizing priorities
        buttonFrame.rowconfigure(0, weight = 1)
        buttonFrame.columnconfigure(0, weight = 1, minsize = 50)
        buttonFrame.columnconfigure(1, weight = 1, minsize = 50)
        buttonFrame.columnconfigure(2, weight = 1, minsize = 50)

    def _createTreeview(self, parent):
		#Create the treeview containing the values displayed
        TreeviewFrame = ttk.Frame(parent)	
        TreeviewFrame.pack(side = TOP, fill = BOTH, expand = N)
        
        #Create the tree 
        self.dataCols = ('Value','Units')
        self.tree = ttk.Treeview(columns = self.dataCols)

        #Setup column headings
        self.tree.heading('#0', text = 'Mode', anchor = 'center')
        self.tree.column('#0', anchor = 'center', width = 130)
        self.tree.heading('Value', text = 'Value', anchor = 'center')
        self.tree.column('#1', anchor = 'center', width = 60)
        self.tree.heading('Units', text = 'Units', anchor = 'center')
        self.tree.column('#2', anchor = 'center', width = 60)
        
        #Set row height
        style = ttk.Style()
        style.configure('Treeview', rowheight = 20)

        self.tree.configure(height = 4)
		
        #Add tree and scrollbars to frame
        self.tree.grid(in_ = TreeviewFrame, row = 0, column = 0, sticky = (N, S, E, W))

        #Set frame resizing priorities
        TreeviewFrame.rowconfigure(0, weight = 1)
        TreeviewFrame.columnconfigure(0, weight = 1)	
        return self.tree		

    def _createLabel(self, parent, Label):
		#Create Labels to name the sensors tables
        LabelFrame = ttk.Frame(parent)
        LabelFrame.pack(side = TOP, fill = BOTH, expand = Y)		
        self.Lbl = ttk.Label(self, text = Label)
        self.Lbl.grid(in_ = LabelFrame, row = 0, column = 0, sticky = (N, S, E, W))

    def _createCombo(self, parent, Ports):
		#Create a combobox filled with available COM ports
        comboFrame = ttk.Frame(parent)
        self.Combo_value = StringVar()
        comboFrame.pack(side = TOP, fill = BOTH, expand = Y)
        style = ttk.Style()
        style.theme_settings("default", {"TCombobox": {"configure": {"padding": 5},"map": {"background": [("active", "green2"),("!disabled", "green4")],"fieldbackground": [("!disabled", "green3")],"foreground": [("focus", "OliveDrab1"),("!disabled", "OliveDrab2")]}}})		

		#Label for the combo box
        self.Lbl = ttk.Label(self, text = 'COM port:')
        self.Lbl.grid(in_ = comboFrame, row = 0, column = 0, sticky = (W,E), ipadx = 10)

		#Create and set the values of the combobox
        self.Combo = ttk.Combobox(self, textvariable = self.Combo_value, state = 'readonly')
        self.Combo.bind('<<ComboboxSelected>>', self._comboEvent)
        self.Combo['values'] = Ports
        self.Combo.current(0)
        self.Combo.grid(in_ = comboFrame, row = 0, column = 2, sticky = (W,E), ipadx = 10)
		
		#Set frame resizing priorities
        comboFrame.rowconfigure(0, weight=1)
        comboFrame.columnconfigure(0, weight=1)
        comboFrame.columnconfigure(2, weight=2)
        
    def _comboEvent(self, event):
        self.thread.portCOM = self.port[self.Combo.current()]
		
    def _loadTable(self, Table):
		#Put data coming from the COM port in the tables
		#Delete first old data present in the table
        for i in Table.get_children():
            Table.delete(i)
		#Fill the table
        Table.insert('', 'end', text = self.data[0], values = (self.data[1:3]))
        if len(self.data)>3:
            Table.insert('', 'end', text = self.data[3], values = (self.data[4:6]))
            
    def _loadHoldTable(self, holdTable, dataToDisplay):
        #Put Hold data in the popup treeview table
		#Delete first old data present in the table          
        if holdTable.winfo_exists() == 1:
            for i in holdTable.get_children():
                holdTable.delete(i)
                
            #Write data in the treeview
            for j in range(len(dataToDisplay)//4):
                holdTable.insert('', 'end', text = dataToDisplay[4*j], values = dataToDisplay[4*j+1:4*j+4])
            
    def _quitApp(self):
		#Called when the Quit button is called. Close the thread and destroy the GUI
        try:
            self.thread.stop()
        except:
            pass
        self.QUIT = False    
        self._destroyGUI(self)
		
    def _onStartClick(self):
		#Called when Start button is pressed. Start the Acquisition
		#Get the data in the queue
        try:
            self.size = self.queue.qsize()
            for count in range(self.size-1):
                self.queue.get()
            
            #Disable buttons not needed during the Acquisition		
            self.buttonStart.config(state = 'disabled')
            self.buttonQuit.config(state = 'disabled')		
            self.Combo.config(state = 'disabled')
            self.buttonStop.config(state = 'normal')
            
            #Check if a file will be saved and fill fileObj
            if self.Saving:
                self.buttonBrowse.config(state = 'disabled', text = 'Saving...')
            else:
                self.buttonBrowse.config(state = 'disabled', text = 'Browse')			
            
            self.fileObj = self._createFile(self.fname)
        
            #Start the acquisition of the data
            self.started = True		
            self._process_serial()
        except:
            pass

    def _onStopClick(self):
		#Called when Stop button is pressed. Stop the Acquisition
        #Enable and Disable buttons not needed during the break		
        self.buttonStart.config(state = 'normal')
        self.buttonBrowse.config(state = 'normal', text = 'Browse')
        self.buttonQuit.config(state = 'normal')
        self.buttonStop.config(state = 'disabled')
        self.Combo.config(state = 'normal')
		
        self.Saving = False
        self.started = False
		
		#Close the text file that may have been opened
        self.fname =  ""			
        self._closeFile(self.fileObj)
	
    def _load_file(self):
		#Open the file browser and return the path location if a file path is choosen
        self.fname = ""
        self.fname =  filedialog.asksaveasfilename(title = 'Choose text file', initialdir = "C:/", defaultextension = '.txt')          	
        if self.fname is "":
            self.Saving = False
            self.buttonBrowse.config(text="Browse")			
            return
        else:
            self.Saving = True
            self.buttonBrowse.config(text = "Ready")
    
    def _createFile(self, fname):
		#Create a file text at the location specified in fname. Write the header
        self.fname = fname
        if self.fname != None:
            if os.access(os.path.dirname(self.fname), os.W_OK):				
                self.fileObj = open(self.fname, mode = 'w')
                self.fileObj.write('Mode'+'\t'+'Value'+'\t'+'Units'+'\n')
                return self.fileObj

    def _saveFile(self, fileObj, data):
		#Write data in the text file
        self.data = data
        self.fileObj = fileObj
        if self.fileObj != None:
            for l in range(len(self.data)-1):
                self.fileObj.write(str(self.data[l])+'\t')
            self.fileObj.write(str(self.data[len(self.data)-1])+'\n')
            
    def _saveHoldFile(self):        
        self.fnameh = ""
        self.fnameh =  filedialog.asksaveasfilename(title = 'Choose text file', initialdir = "C:/", defaultextension = '.txt')          	
        if self.fnameh != None:
            if os.access(os.path.dirname(self.fnameh), os.W_OK):				
                self.fileObjH = open(self.fnameh, mode = 'w')
                self.fileObjH.write('Hold number'+'\t'+'Mode'+'\t'+'Value'+'\t'+'Units'+'\n')
                for j in range(len(self.dataHold)//4):
                    for l in range(3):                    
                        self.fileObjH.write(str(self.dataHold[4*j+l])+'\t')
                    self.fileObjH.write(str(self.dataHold[4*j+3])+'\n')
                self.fileObjH.close()

            
    def _closeFile(self, fileObj):
		#Close the text file
        self.fileObj = fileObj
        if self.fileObj != None:		
            self.fileObj.close()
			
    def _destroyGUI(self,parent):
        parent.destroy()
        os._exit(1)

    def _serial_ports(self):
    #Lists serial ports
    # :raises EnvironmentError:
    # On unsupported or unknown platforms
    # :returns:
    # A list of available serial ports
        if sys.platform.startswith('win'):
            self.ports = ['COM' + str(i + 1) for i in range(256)]
        elif sys.platform.startswith ('linux'):
            self.temp_list = glob.glob ('/dev/tty[A-Za-z]*')
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
	#Thread class running in parallel of the main class. Prevent any freeze
    def __init__(self, queue, queueHold, port = 'COM9'):
		#Initialize the class
        Thread.__init__(self)
        self.Out = False
        self.dataList = defaultlist([])
        self.queue = queue
        self.queueHold = queueHold
        self.portCOM = port
        self.portCOM_old = ''
        self.acq = False
        self.runCOM = True
        self.data = ''
        self.dataListFilled = False
        self.dataHold = defaultlist([])
        self.temploop = 0
        
    def run(self):
		#Run continuously when the application is launched
        while self.runCOM :
			#Check if the COM port value is valid
            if str(self.portCOM)[0:3] == 'COM':
                try:
                    self.ser = Serial(self.portCOM, baudrate = 9600, timeout = 500, xonxoff = False, rtscts = False, dsrdtr = False)
                    self.portCOM_old = self.portCOM
                    self.ser.flushInput()
                    self.ser.flushOutput()
                    self.acq = True
                    
                    #Check if the COM port has been changed					
                    while self.acq:
                        if self.portCOM == self.portCOM_old:
							#Rearrange data
                            self.dataArrange()
                        else:
                            self.acq = False
                            self.portCOM_old = self.portCOM
                            self.ser.close()                         
                except:
                    pass
            sleep(0.2)		

    def dataArrange(self):
		#Get the data string and put it in the right order
        self.out = False
        while self.out == False and self.portCOM == self.portCOM_old:
            self.bytesToRead = self.ser.inWaiting()
            if self.bytesToRead>0:
                self.data = self.ser.readline()              
                try:
                    self.data = self.data.decode("utf-8")
                    if len(self.data) > 0:
                        
                        if (self.data.find('[') >= 0):
                            self.data = self.data.replace('[','')
                        if (self.data.find(']') >= 0):
                            self.data = self.data.replace(']','')
                        if (self.data.find('\r') >= 0):
                            self.data = self.data.replace('\r','')
                        if (self.data.find('\n') >= 0):
                            self.data = self.data.replace('\n','')
 
                        if len(self.data) == 8:
                            if self.data[0] != '5':
                                #Case where the modes gives only one value
                                if self.data[6:8] == 'Lu' or self.data[6:8] == 'UW':
                                    #Check if Luxmeter mode, if not, insert a coma in the value
                                    self.dataList = [self.selectMode(self.data[0]), self.data[1:6], self.selectUnits(self.data[6:8])]
                                else:
                                    self.dataList = [self.selectMode(self.data[0]), self.comaInValue(self.data[1:6]), self.selectUnits(self.data[6:8])]  
                                self.queue.put(self.dataList)    
                            elif self.data[0] == '5':
                                #Case where two values are given
                                if self.dataListFilled:
                                    if self.data[6:8] == 'Lu' or self.data[6:8] == 'UW':
                                        self.dataList = self.dataList + [self.selectMode(self.data[0]), self.data[1:6], self.selectUnits(self.data[6:8])]
                                    else:
                                        self.dataList = self.dataList + [self.selectMode(self.data[0]), self.comaInValue(self.data[1:6]), self.selectUnits(self.data[6:8])]                            
                                    self.dataListFilled = False
                                    self.queue.put(self.dataList)                              
                                else:
                                    if self.data[6:8] == 'Lu' or self.data[6:8] == 'UW':
                                        self.dataList = [self.selectMode(self.data[0]), self.data[1:6], self.selectUnits(self.data[6:8])]
                                    else:
                                        self.dataList = [self.selectMode(self.data[0]), self.comaInValue(self.data[1:6]), self.selectUnits(self.data[6:8])] 
                                    self.dataListFilled = True
                        elif len(self.data) == 9:
                            #Case of the hold function
                            self.temploop = self.temploop + 1
                            if len(self.dataHold) == 0:
                                if self.data[7:9] == 'Lu' or self.data[7:9] == 'Uw':
                                    self.dataHold = [self.data[0], self.selectMode(self.data[1]), self.data[2:7], self.selectUnits(self.data[7:9])]    
                                else:
                                    self.dataHold = [self.data[0], self.selectMode(self.data[1]), self.comaInValue(self.data[2:7]), self.selectUnits(self.data[7:9])]        
                            else:
                                if self.data[0] == str(self.temploop-1):
                                    if self.data[7:9] == 'Lu' or self.data[7:9] == 'Uw':
                                        self.dataHold = self.dataHold + [self.data[0], self.selectMode(self.data[1]), self.data[2:7], self.selectUnits(self.data[7:9])]    
                                    else:
                                        self.dataHold = self.dataHold + [self.data[0], self.selectMode(self.data[1]), self.comaInValue(self.data[2:7]), self.selectUnits(self.data[7:9])]        
                            if self.temploop == 10:
                                self.queueHold.put(self.dataHold)
                                self.dataHold = defaultlist([]) 
                                self.temploop = 0
                                
                        if self.runCOM:
                            self.out = False
                        else :
                            self.out = True												
                except:
                    pass

    def selectUnits(self, units = 'GA'):
        #Select and return the proper units
        self.units = units
        if self.units == 'GA':
            return 'G'
        elif self.units == 'mT':
            return 'mT'
        elif self.units == 'kA':
            return 'kA/m'
        elif self.units == 'Lu':
            return 'lx'
        elif self.units == 'Uw':
            return 'µW/cm²'
        elif self.units == 'UW':
            return 'µW/cm²'            
        else:
            return ''
            
    def selectMode(self, mode = '0'):
        #Select and return the acquisition mode
        self.mode = mode
        if self.mode == '0':
            return 'DC Magn. field'
        elif self.mode == '1':
            return 'AC Magn. field'            
        elif self.mode == '2':
            return 'AC+DC Magn. field'
        elif self.mode == '3':
            return 'Vis.light illuminance'
        elif self.mode == '4':
            return 'UV light illuminance'
        elif self.mode == '5':
            return 'Vis.+UV light illuminance'
        else:
            return ''

    def comaInValue(self, value = '+0000'):
        #Format the input value with the correct coma separator
        self.value = value
        
        self.value = self.value[:3] + '.' + self.value[3:]
        return self.value
    
    def stop(self):
		#Stop the Thread in order to close it properly
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
            
class defaultlist(list):
	#Allow the list to be expanded
    def __setitem__(self, index, value):
        size = len(self)
        if index >= size:
            self.extend(0 for _ in range(size, index + 1))
        list.__setitem__(self, index, value)
					
if __name__ == "__main__":	
    vp_start_gui()