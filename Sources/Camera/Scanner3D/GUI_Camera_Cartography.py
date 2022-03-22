from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import carto3Dcam
import mousepositionanalysis as mpa
import os.path
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import canvasplot
import configparser
import ast
import cameraundistort as undis
import numpy
import time


class GUI:
    def __init__(self, master):
        self.master = master
        self.labelText = "Welcome! You'll find here some status"
        self.menuBar()
        self.createPanel()
        self.config = configparser.ConfigParser()
        self.readConfig()
        self.optionsWindow()
        self.optionsWindowSensor()
        self.hideOptions()
        self.hideOptionsSensor()
        self.camcorr = undis.CameraUndistort()

    def createPanel(self):
        '''Create the main front Panel containing sub panels, buttons and canvas'''
        self.master.title("CartoMag")
        geom = "1010x535+100+100"
        self.master.geometry(geom)
        self.master.minsize(1010, 545)
        # self.master.maxsize(380, 250)
        self.frame = Frame(self.master, borderwidth=5, relief="flat")
        self.frame.grid(row=0, column=0, sticky=(N, E, S, W))
        self.buttonPanel, self.labelPanel, self.canvasPanel = self.createSubPanel(self.frame)
        self.start_button = self.createButton(self.buttonPanel, "Start", self.start_btn, 0, 0, (W, E))
        # self.stop_button = self.createButton(self.buttonPanel, "Stop", self.stop_btn, 0, 1, (W, E))
        self.quit_button = self.createButton(self.buttonPanel, "Quit", self.quit_btn, 0, 1, (W, E))
        self.msgLabel = self.createLabel(self.labelPanel, self.labelText, 1, 0, (W, E))
        self.createCanvas(self.canvasPanel)

    def createSubPanel(self, master):
        '''Create Button  sub Panel and Canvas sub Panel for easy geometry of the front panel'''
        buttonPanel = Frame(master=master, width=1010, height=100)
        buttonPanel.grid(row=0, column=0, sticky=(N, E, S, W))
        labelPanel = Frame(master=master, width=1010, height=100)
        labelPanel.grid(row=1, column=0, sticky=(N, E, S, W))
        canvasPanel = Frame(master=master, width=1010, height=400)
        canvasPanel.grid(row=2, column=0, sticky=(N, E, S, W))
        return buttonPanel, labelPanel, canvasPanel

    def createButton(self, master, text, command, row, column, sticky):
        '''Create a new Button'''
        newButton = Button(master=master, text=text, command=command)
        try:
            newButton.pack(side=LEFT, fill=BOTH, expand=1)
        except:
            newButton.grid(row=row, column=column, sticky=sticky)
        return newButton

    def createLabel(self, master, text, row, column, sticky):
        '''Create a new Label'''
        newLabel = Label(master=master, text=text)
        try:
            newLabel.pack(side=LEFT, fill=BOTH, expand=1)
        except:
            newLabel.grid(row=row, column=column, sticky=sticky)
        return newLabel

    def menuBar(self):
        '''Create a menu bar containing the different available options in the main window'''
        self.menubar = Menu(self.master)
        # Create the sub menu "File"
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save data", command=self.saveData)
        self.filemenu.add_command(label="Save Scatter Plot", command=self.saveScatter)
        self.filemenu.add_command(label="Save Interpolation Plot", command=self.saveInterp)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit_btn)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_command(label="DAQ Options", command=self.showOptions)
        self.menubar.add_command(label="Sensor Options", command=self.showOptionsSensor)
        self.menubar.add_command(label="Calibrate Camera", command=self.calibCam)
        self.master.config(menu=self.menubar)

    def createCanvas(self, master):
        '''Create canvas where the data will be plotted'''
        self.canvas = canvasplot.CanvasPlot()
        self.figScatt, self.figInterp = self.canvas.getFig()
        self.subScatt, self.subInterp = self.canvas.getSub()
        self.canvasScatt = FigureCanvasTkAgg(self.figScatt, master=master)
        self.canvasInterp = FigureCanvasTkAgg(self.figInterp, master=master)
        self.canvasScatt.get_tk_widget().grid(row=0, column=0, sticky=(W, E))
        self.canvasInterp.get_tk_widget().grid(row=0, column=1, sticky=(W, E))

    def start_btn(self):
        '''Start the mouse positions acquisition as well as the DAQ data acquisition, then analyse the data and plot it'''
        self.start_button.config(state="disabled")
        # self.stop_button.config(state = "normal")
        self.quit_button.config(state="disabled")
        if self.dev_name == "":
            self.dev_name = "cDAQ9191-187C90EMod1"
        if self.ch_name == [] or self.ch_name == "" or self.ch_name == None:
            self.ch_name = ["ai3", "ai2", "ai1", "ai0"]
        if self.data_nb == 0 or self.data_nb == "" or self.data_nb == None:
            self.data_nb = 1000
        if self.rate == 0 or self.rate == "" or self.rate == None:
            self.rate = 50000.0
        if self.xOffset == None or self.xOffset == "":
            self.xOffset = 4
        if self.mtx == [] or self.dist == []:
            self.mtx, self.dist = self.camcorr.calibrate()

        self.carto = carto3Dcam.Carto3D(camcorr=self.camcorr, dev_name=self.dev_name, ch_name=self.ch_name,
                                        data_nb=self.data_nb,
                                        rate=self.rate, xOffset=self.xOffset, video_ch=self.video_ch,
                                        distance_marker=self.distance_marker,
                                        mtx=self.mtx, dist=self.dist, undis=self.undistortImg)
        self.setMsgLabel("Created carto3D object")
        time.sleep(0.1)
        self.carto.initCamera()
        self.setMsgLabel("Initialized Camera")
        time.sleep(0.1)
        self.carto.startDAQTask()
        self.setMsgLabel("DAQ device Started")
        time.sleep(0.1)
        self.carto.startCamera()
        self.setMsgLabel("Camera started: press Esc. to stop the acquisition")
        time.sleep(0.1)
        self.carto.acquire3D()
        self.carto.stopCamera()
        self.setMsgLabel("Camera stopped")
        time.sleep(0.1)
        self.carto.stopDAQTask()
        self.setMsgLabel("DAQ device Stopped")
        time.sleep(0.1)
        self.xPos, self.yPos, self.zVar = self.carto.getCarto3D()
        self.ch_nb = self.carto.getchnb()
        if self.zVar != []:
            self.mouse = mpa.MousePosAnalysis(self.xPos, self.yPos, self.zVar, self.ch_nb)
            self.setMsgLabel("Analyzing data")
            time.sleep(0.1)
            self.mouse.nDimArrays()
            self.mouse.scalezVar()
            self.mouse.sort3D()
            self.mouse.normalizeCmap()
            self.setMsgLabel("Plotting data")
            time.sleep(0.1)
            self.mouse.plotScatter(self.subScatt)
            self.mouse.plotInterp(self.subInterp)
            self.canvasScatt.show()
            self.canvasInterp.show()
        else:
            self.setMsgLabel("DAQ device not working")
            time.sleep(1)

        self.start_button.config(state="normal")
        # self.stop_button.config(state = "disabled")
        self.quit_button.config(state="normal")
        self.setMsgLabel("Waiting for a new run...")

    # def stop_btn(self):
    # self.carto.stopDAQTask()
    # self.carto.stopCamera()
    # self.xPos, self.yPos, self.zVar = self.carto.getCarto3D()
    # self.ch_nb = self.carto.getchnb()

    # self.mouse = mpa.MousePosAnalysis(self.xPos, self.yPos, self.zVar, self.ch_nb)
    # self.mouse.nDimArrays()
    # self.mouse.scalezVar()
    # self.mouse.sort3D()
    # self.mouse.normalizeCmap()

    # self.mouse.plotScatter(self.subScatt)
    # self.mouse.plotInterp(self.subInterp)
    # self.canvasScatt.show()
    # self.canvasInterp.show()

    # self.start_button.config(state = "normal")
    # self.stop_button.config(state = "disabled")
    # self.quit_button.config(state = "normal")

    def quit_btn(self):
        '''Destroy and quit the main application'''
        self.setMsgLabel("Goodbye!")
        time.sleep(0.5)
        self.writeConfig()
        self.master.destroy()
        os._exit(1)

    def optionsWindow(self):
        '''Create a TopLevel Options window use to control the application parameters'''
        self.options = Toplevel(self.master)
        self.options.title("Options")
        geom = "430x220+200+200"
        self.options.geometry(geom)
        self.options.protocol('WM_DELETE_WINDOW', self.hideOptions)
        self.dev_name_string = self.createEntry(self.options, "DAQ device name:", 0, 0, (W, E))
        self.dev_name_string.set(self.dev_name)

        channelLabel = Label(self.options, text="Channels name:")
        channelLabel.grid(row=1, column=0, sticky=(W, E))
        self.optionsPanel = Frame(self.options)
        self.optionsPanel.grid(row=2, column=1, sticky=(W, E))
        self.ch_name_chk = []
        for i in range(16):
            var = IntVar()
            try:
                self.ch_name.index("ai" + str(i))
                var.set(1)
            except:
                var.set(0)
            self.chk = Checkbutton(self.options, text="ai" + str(i), onvalue=1, offvalue=0, variable=var)
            self.chk.grid(in_=self.optionsPanel, row=i % 2 + 2, column=int(i / 2))
            self.ch_name_chk.append(var)

        self.invert_chk = IntVar()
        self.invert_chk.set(self.invert)
        self.chk_invert = Checkbutton(self.options, text="Invert channels?", onvalue=1, offvalue=0,
                                      variable=self.invert_chk)
        self.chk_invert.grid(in_=self.options, row=5, column=1, sticky=(W, E))
        self.datanb_string = self.createEntry(self.options, "Number of data:", 6, 0, (W, E))
        self.datanb_string.set(str(self.data_nb))
        self.rate_string = self.createEntry(self.options, "Rate:", 7, 0, (W, E))
        self.rate_string.set(str(self.rate))
        self.apply_btn = self.createButton(self.options, "Apply", self.apply_btn, 8, 1, (W, E))
        self.quit_btn_daq = self.createButton(self.options, "Quit", self.hideOptions, 9, 1, (W, E))

    def optionsWindowSensor(self):
        '''Create a TopLevel Options window use to control the application parameters'''
        self.options_sensor = Toplevel(self.master)
        self.options_sensor.title("Options")
        geom = "430x220+200+200"
        self.options_sensor.geometry(geom)
        self.options_sensor.protocol('WM_DELETE_WINDOW', self.hideOptions)
        self.video_ch_string = self.createEntry(self.options_sensor, "Video Channel:", 0, 0, (W, E))
        self.video_ch_string.set(str(self.video_ch))
        self.distance_marker_string = self.createEntry(self.options_sensor, "Distance between markers (mm):", 1, 0,
                                                       (W, E))
        self.distance_marker_string.set(str(self.distance_marker))
        self.offset_string = self.createEntry(self.options_sensor, "Offset:", 2, 0, (W, E))
        self.offset_string.set(str(self.xOffset))
        self.undistort_chk = IntVar()
        self.undistort_chk.set(self.undistortImg)
        self.chk_undistort = Checkbutton(self.options_sensor, text="Undistort Image?", onvalue=1, offvalue=0,
                                         variable=self.undistort_chk)
        self.chk_undistort.grid(in_=self.options_sensor, row=3, column=1, sticky=(W, E))
        self.apply_btn_sensor = self.createButton(self.options_sensor, "Apply", self.apply_btn_sensor, 4, 1, (W, E))
        self.quit_btn_sensor = self.createButton(self.options_sensor, "Quit", self.hideOptionsSensor, 5, 1, (W, E))

    def createEntry(self, master, text, row, column, sticky):
        '''Create new string Entry with its label'''
        label = Label(master, text=text)
        label.grid(row=row, column=column, sticky=sticky)
        string = StringVar()
        entry = Entry(master, textvariable=string)
        entry.grid(row=row, column=column + 1, sticky=sticky)
        return string

    def apply_btn(self):
        '''Set and store the values present in the fields of Options window'''
        try:
            self.dev_name = self.dev_name_string.get()
        except:
            self.dev_name = ""
        try:
            self.data_nb = int(self.datanb_string.get())
        except:
            self.data_nb = 0
        try:
            self.rate = float(self.rate_string.get())
        except:
            self.rate = 0
        try:
            self.ch_name = []
            idx = 0
            for ch_name in self.ch_name_chk:
                if ch_name.get() == 1:
                    name = "ai" + str(idx)
                    if self.invert_chk.get() == 0:
                        self.invert = 0
                        self.ch_name.append(name)
                    else:
                        self.invert = 1
                        self.ch_name.insert(0, name)
                idx = idx + 1
        except:
            self.ch_name = []
        self.writeConfig()

    def apply_btn_sensor(self):
        try:
            self.video_ch = int(self.video_ch_string.get())
        except:
            self.video_ch = 1
        try:
            self.distance_marker = float(self.distance_marker_string.get())
        except:
            self.distance_marker = 30.0
        try:
            self.xOffset = float(self.offset_string.get())
        except:
            self.xOffset = None
        try:
            self.undistortImg = self.undistort_chk.get()
        except:
            self.undistortImg = 1
        self.writeConfig()

    def hideOptions(self):
        '''Hide the Options TopLevel window'''
        self.options.withdraw()

    def hideOptionsSensor(self):
        '''Hide the Options TopLevel window'''
        self.options_sensor.withdraw()

    def showOptions(self):
        '''Show the Options TopLevel window'''
        self.options.deiconify()

    def showOptionsSensor(self):
        '''Show the Options TopLevel window'''
        self.options_sensor.deiconify()

    def saveScatter(self):
        self.saveImage(self.figScatt)

    def saveInterp(self):
        self.saveImage(self.figInterp)

    def saveImage(self, master):
        '''Open the file browser and save the image at the location'''
        fname = ""
        fname = filedialog.asksaveasfilename(title='Choose image file name', initialdir="C:/", defaultextension='.png')
        if fname is "":
            return
        else:
            if os.access(os.path.dirname(fname), os.W_OK):
                master.savefig(fname, format='png')

    def saveData(self):
        '''Open the file browser and save the data at the location'''
        fname = ""
        fname = filedialog.asksaveasfilename(title='Choose data file name', initialdir="C:/", defaultextension='.txt')
        if fname is "":
            return
        else:
            if os.access(os.path.dirname(fname), os.W_OK):
                try:
                    self.mouse.saveData(fname)
                except:
                    return

    def calibCam(self):
        self.mtx, self.dist = self.camcorr.calibrate()
        self.writeConfig()

    def readConfig(self):
        '''Read the config file'''
        self.config.read('config.ini')
        try:
            self.dev_name = self.config['DAQ']['dev_name']
            self.ch_name = ast.literal_eval(self.config['DAQ']['ch_name'])
            self.data_nb = int(self.config['DAQ']['data_nb'])
            self.rate = float(self.config['DAQ']['rate'])
            self.invert = int(self.config['DAQ']['invert'])
            self.video_ch = int(self.config['Camera']['video_ch'])
            self.distance_marker = float(self.config['Camera']['distance_marker'])
            self.xOffset = float(self.config['Camera']['xOffset'])
            self.undistortImg = int(self.config['Camera']['undistort'])
            self.mtx = ast.literal_eval(self.config['Camera']['mtx'])
            self.mtx = numpy.array(self.mtx, dtype='|S18')
            self.mtx = self.mtx.astype(numpy.float)
            self.mtx = numpy.reshape(self.mtx, (3, 3))
            self.dist = ast.literal_eval(self.config['Camera']['dist'])
            self.dist = numpy.array(self.dist, dtype='|S18')
            self.dist = self.dist.astype(numpy.float)
        except:
            self.dev_name = 'cDAQ9191-187C90EMod1'
            self.ch_name = ["ai3", "ai2", "ai1", "ai0"]
            self.video_ch = 1
            self.distance_marker = 30
            self.data_nb = 1000
            self.rate = 50000.0
            self.xOffset = 4
            self.invert = 1
            self.mtx = numpy.matrix([])
            self.dist = numpy.array([])
            self.undistortImg = 1
            self.writeConfig()

    def writeConfig(self):
        '''Write the config file'''
        self.mtx_t = []
        for row in range(len(self.mtx)):
            for col in range(len(self.mtx[row])):
                self.mtx_t.append(str(self.mtx[row][col]))
        self.dist_t = []
        try:
            for row in range(len(self.dist)):
                for col in range(len(self.dist[row])):
                    self.dist_t.append(str(self.dist[row][col]))
        except:
            for col in range(len(self.dist)):
                self.dist_t.append(str(self.dist[col]))

        self.config['DAQ'] = {'dev_name': self.dev_name,
                              'ch_name': str(self.ch_name),
                              'data_nb': str(self.data_nb),
                              'rate': str(self.rate),
                              'invert': str(self.invert)}
        self.config['Camera'] = {'video_ch': self.video_ch,
                                 'distance_marker': self.distance_marker,
                                 'xOffset': str(self.xOffset),
                                 'mtx': (self.mtx_t),
                                 'dist': (self.dist_t),
                                 'undistort': (self.undistortImg)}
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def setMsgLabel(self, text):
        self.msgLabel.config(text=text)


if __name__ == "__main__":
    root = Tk()
    main_ui = GUI(root)
    root.mainloop()
