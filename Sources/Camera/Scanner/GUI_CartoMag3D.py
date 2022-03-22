# -*- coding: utf-8 -*-
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import ast
import canvasplot
import configparser
import cameraundistort as undis
import carto4Dcam
import dataanalysis4D as dat4d
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import axes3d, Axes3D
from mpl_toolkits.mplot3d import proj3d
import matplotlib.pyplot as plt
import numpy
import os.path
from queue import Queue
import time
from threading import Thread


class GUI:
    def __init__(self):
        self.root = Tk()
        self.master = self.root
        self.labelText = "Welcome! You'll find here some status"
        self.width = 1210
        self.height = 675
        self.left = 100
        self.top = 100
        self.dpifig = 100
        self.colors_combo = ['yellow', 'pink', 'red', 'green', 'blue', 'orange', 'white', 'black']
        self.choice = 'pack'
        self.menuBar()
        self.createPanel()
        self.config = configparser.ConfigParser()
        self.readConfig()
        self.optionsWindow()
        self.optionsWindowSensor()
        self.lineCutFigureWindow()
        self.hideOptions()
        self.hideOptionsSensor()
        self.hideCutFigure()
        self.camcorr = undis.CameraUndistort()
        self.queue = Queue()
        self.queuestart = Queue()
        self.started = False
        self.isCalibrating = False
        self.SDataMean = []
        self.board_h = 6
        self.board_w = 5
        self.folder = 'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Sources\\Camera\\test\\'
        self.camcorr.setFolder(
            'C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Sources\\Camera\\Scanner\\chessboard\\')
        self.size = 25

        self.root.mainloop()

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
        self.menubar.add_command(label="Calibrate Sensor", command=self.calibSensor)
        self.master.config(menu=self.menubar)

    def createPanel(self):
        '''Create the main front Panel containing sub panels, buttons and canvas'''
        self.master.title("CartoMag")
        geom = str(str(self.width) + "x" + str(self.height) + "+" + str(self.left) + "+" + str(self.top))
        self.master.geometry(geom)
        self.master.minsize(self.width, self.height)
        self.frame = Frame(self.master, borderwidth=5, relief="flat")
        self.placeWidget(self.frame, 0, 0, (N, E, S, W), TOP, BOTH, 1, CENTER, choice=self.choice)

        self.buttonPanel = self.createSubPanel(self.frame)
        self.labelPanel = self.createSubPanel(self.frame)
        self.canvasPanel = self.createSubPanel(self.frame)
        self.rotationPanel = self.createSubPanel(self.frame)
        self.start_button = self.createButton(self.buttonPanel, "Start", self.start_btn)
        self.quit_button = self.createButton(self.buttonPanel, "Quit", self.quit_btn)
        self.rotation_scale = self.createScale(self.rotationPanel, 0, 360, HORIZONTAL)
        self.msgLabel = self.createLabel(self.labelPanel, self.labelText)
        self.createCanvas(self.canvasPanel)

        self.placeWidget(self.buttonPanel, 0, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.labelPanel, 1, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.canvasPanel, 2, 0, (N, E, S, W), TOP, BOTH, 1, CENTER, choice=self.choice)
        self.placeWidget(self.rotationPanel, 3, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.start_button, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.quit_button, 0, 1, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.rotation_scale, 0, 0, (W, E), RIGHT, NONE, 1, E, choice=self.choice)
        self.placeWidget(self.msgLabel, 1, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.canvasScatt.get_tk_widget(), 0, 0, (W, E), LEFT, BOTH, 1, W, choice=self.choice)
        self.placeWidget(self.canvasInterp.get_tk_widget(), 0, 1, (W, E), RIGHT, BOTH, 1, E, choice=self.choice)
        # self.placeWidget(self.fig, 0, 0, (W, E), LEFT, BOTH, 1, W, choice = self.choice)        
        # self.placeWidget(self.figInterp, 0, 1, (W, E), RIGHT, BOTH, 1, E, choice = self.choice) 

    def createSubPanel(self, master):
        '''Create Button  sub Panel and Canvas sub Panel for easy geometry of the front panel'''
        subPanel = Frame(master=master)  # , width=1010, height=100
        return subPanel

    def createButton(self, master, text, command):
        '''Create a new Button'''
        newButton = Button(master=master, text=text, command=command)
        return newButton

    def createLabel(self, master, text):
        '''Create a new Label'''
        newLabel = Label(master=master, text=text)
        return newLabel

    def createCanvas(self, master):
        '''Create canvas where the data will be plotted'''

        self.fig = plt.figure()
        # self.canvas = FigureCanvasTkAgg(self.fig,master = master )
        # self.figScatt = self.fig.add_subplot(121, projection='3d')
        # self.figInterp = self.fig.add_subplot(122)        
        self.canvas = canvasplot.CanvasPlot()
        self.figScatt, self.figInterp = self.canvas.getFig()
        self.figScatt.set_size_inches(6, 6, forward=True)
        self.figScatt.set_dpi(self.dpifig)
        self.figInterp.set_size_inches(6, 6, forward=True)
        self.figInterp.set_dpi(self.dpifig)
        self.subScatt, self.subInterp = self.canvas.getSub()
        self.canvasScatt = FigureCanvasTkAgg(self.figScatt, master=master)
        self.canvasInterp = FigureCanvasTkAgg(self.figInterp, master=master)
        self.canvasInterp.mpl_connect('button_press_event', self.onpress)
        self.figScatt.gca(projection='3d')

    def createScale(self, master, fromValue=0, toValue=360, orient=HORIZONTAL):
        '''Create a new Scale'''
        value = DoubleVar()
        newScale = Scale(master=master, variable=value, from_=fromValue, to=toValue, orient=orient)
        return newScale

    def createEntry(self, master, text):
        '''Create new string Entry with its label'''
        label = Label(master, text=text)
        # label.grid(row = row, column = column, sticky = sticky)
        string = StringVar()
        entry = Entry(master, textvariable=string)
        # entry.grid(row = row, column = column+1, sticky = sticky)
        return string, label, entry

    def createCombobox(self, master, colors_combo):
        '''Create a combobox'''
        combo_var = StringVar()
        combo = Combobox(master, textvariable=combo_var)
        combo['values'] = colors_combo
        return combo

    def setCurrentComboValue(self, combo, current_color):
        '''Set the combobox current value'''
        combo.current(combo['values'].index(current_color))

    def placeWidget(self, widgetName, row=0, column=0, sticky=(N, E, S, W), side=LEFT, fill=BOTH, expand=1,
                    anchor=CENTER, choice='grid'):
        '''Place the widget wit grid or pack options'''
        if choice == 'pack':
            try:
                widgetName.pack(side=side, fill=fill, expand=expand, anchor=anchor)
            except:
                widgetName.grid(row=row, column=column, sticky=sticky)
        else:
            try:
                widgetName.grid(row=row, column=column, sticky=sticky)
            except:
                widgetName.pack(side=side, fill=fill, expand=expand)

    def processAcquisition(self):
        '''Read message queues from the thread'''
        try:
            # Check if Acquisition is still running
            if not self.queuestart.empty():
                self.started = self.queuestart.get()
            if self.started:
                if not self.queue.empty():
                    self.msglabel = self.queue.get()
                    self.setMsgLabel(self.msglabel)
                if self.isCalibrating:
                    time.sleep(0.2)
                    self.processAcquisition()
                else:
                    self.root.after(200, self.processAcquisition)
        except:
            pass

    def start_btn(self):
        '''Start the mouse positions acquisition as well as the DAQ data acquisition, then analyse the data and plot it'''
        self.defaultSettings()
        if self.SDataMean != [] or np.isnan(self.SDataMean[:]) == False:
            self.carto = carto4Dcam.Carto4D(camcorr=self.camcorr, dev_name=self.dev_name, ch_name=self.ch_name,
                                            data_nb=self.data_nb,
                                            rate=self.rate, video_ch=self.video_ch,
                                            distance_marker=self.distance_marker,
                                            mtx=self.mtx, dist=self.dist, undis=self.undistortImg, board_h=self.board_h,
                                            board_w=self.board_w, size=self.size, folder=self.folder)
            self.dataanalysis = dat4d.DataAnalysis4D(SDataMean=self.SDataMean)

            self.thread = Acquisition(self.camcorr, self.dev_name, self.ch_name, self.data_nb, self.rate,
                                      self.xOffset, self.video_ch, self.distance_marker, self.mtx, self.dist,
                                      self.undistortImg, self.canvasScatt, self.subScatt, self.canvasInterp,
                                      self.subInterp, self.queue, self.queuestart, self.carto, self.dataanalysis,
                                      self.isCalibrating)
            self.thread.start()
            self.start_button.config(state="disabled", text='Stop')
            self.quit_button.config(state="disabled")
            self.processAcquisition()

            self.start_button.config(state="normal", text='Start')
            self.quit_button.config(state="normal")
        else:
            self.setMsgLabel('Please calibrate the sensor')

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
        # geom = "430x220+200+200"
        # self.options.geometry(geom)
        self.options.protocol('WM_DELETE_WINDOW', self.hideOptions)

        self.dev_name_panel = self.createSubPanel(self.options)
        self.dev_name_string, self.dev_name_label, self.dev_name_entry = self.createEntry(self.dev_name_panel,
                                                                                          "DAQ device name:")
        self.dev_name_string.set(self.dev_name)

        self.channelLabel = Label(self.options, text="Channels name:")
        self.chk_panel_1 = self.createSubPanel(self.options)
        self.chk_panel_2 = self.createSubPanel(self.options)

        self.ch_name_chk = []
        self.chk = []
        for i in range(16):
            var = IntVar()
            try:
                self.ch_name.index("ai" + str(i))
                var.set(1)
            except:
                var.set(0)
            if i % 2 == 0:
                panel = self.chk_panel_1
            else:
                panel = self.chk_panel_2
            self.chk.append(Checkbutton(panel, text="ai" + str(i), onvalue=1, offvalue=0, variable=var))
            self.ch_name_chk.append(var)

        self.chkInvert_panel = self.createSubPanel(self.options)
        self.invert_chk = IntVar()
        self.invert_chk.set(self.invert)
        self.chk_invert = Checkbutton(self.chkInvert_panel, text="Invert channels?", onvalue=1, offvalue=0,
                                      variable=self.invert_chk)

        self.datanb_panel = self.createSubPanel(self.options)
        self.datanb_string, self.datanb_label, self.datanb_entry = self.createEntry(self.datanb_panel,
                                                                                    "Number of data:")
        self.rate_panel = self.createSubPanel(self.options)
        self.rate_string, self.rate_label, self.rate_entry = self.createEntry(self.rate_panel, "Rate:")
        self.apply_btn = self.createButton(self.options, "Apply", self.apply_btn)
        self.quit_btn_daq = self.createButton(self.options, "Quit", self.hideOptions)

        self.placeWidget(self.dev_name_panel, 0, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.dev_name_label, 0, 0, (N, E, S, W), LEFT, NONE, 1, W, choice=self.choice)
        self.placeWidget(self.dev_name_entry, 0, 1, (N, E, S, W), LEFT, X, 1, E, choice=self.choice)
        self.placeWidget(self.channelLabel, 1, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)

        self.placeWidget(self.chk_panel_1, 2, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.chk_panel_2, 3, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        for i in range(16):
            self.placeWidget(self.chk[i], i % 2 + 2, int(i / 2), (E, W), LEFT, X, 1, CENTER, choice=self.choice)

        self.placeWidget(self.chkInvert_panel, 4, 1, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.chk_invert, 0, 0, (E, W), LEFT, X, 1, CENTER, choice=self.choice)

        self.placeWidget(self.datanb_panel, 5, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.datanb_label, 0, 0, (E, W), LEFT, NONE, 1, W, choice=self.choice)
        self.placeWidget(self.datanb_entry, 0, 1, (E, W), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.rate_panel, 6, 0, (N, E, S, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.rate_label, 0, 0, (E, W), LEFT, NONE, 1, W, choice=self.choice)
        self.placeWidget(self.rate_entry, 0, 1, (E, W), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.apply_btn, 7, 0, (E, W), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.quit_btn_daq, 8, 0, (E, W), TOP, X, 1, CENTER, choice=self.choice)

        self.datanb_string.set(str(self.data_nb))
        self.rate_string.set(str(self.rate))

    def optionsWindowSensor(self):
        '''Create a TopLevel Options window use to control the application parameters'''
        self.options_sensor = Toplevel(self.master)
        self.options_sensor.title("Options")
        # geom = "430x220+200+200"
        # self.options_sensor.geometry(geom)
        self.options_sensor.protocol('WM_DELETE_WINDOW', self.hideOptions)

        self.video_ch_panel = self.createSubPanel(self.options_sensor)
        self.video_ch_string, self.video_ch_label, self.video_ch_entry = self.createEntry(self.video_ch_panel,
                                                                                          "Video Channel:")
        self.video_ch_string.set(str(self.video_ch))

        self.distance_marker_panel = self.createSubPanel(self.options_sensor)
        self.distance_marker_string, self.distance_marker_label, self.distance_marker_entry = self.createEntry(
            self.distance_marker_panel, "Distance between markers (mm):")
        self.distance_marker_string.set(str(self.distance_marker))

        self.offset_panel = self.createSubPanel(self.options_sensor)
        self.offset_string, self.offset_label, self.offset_entry = self.createEntry(self.offset_panel, "Offset:")
        self.offset_string.set(str(self.xOffset))

        self.undistort_chk = IntVar()
        self.undistort_chk.set(self.undistortImg)
        self.chk_undistort = Checkbutton(self.options_sensor, text="Undistort Image?", onvalue=1, offvalue=0,
                                         variable=self.undistort_chk)

        self.combodir_panel = self.createSubPanel(self.options_sensor)
        self.colordir_label = Label(self.combodir_panel, text='Direction color:')
        self.colordir_combo = self.createCombobox(self.combodir_panel, self.colors_combo)

        self.combosensor_panel = self.createSubPanel(self.options_sensor)
        self.colorsensor_label = Label(self.combosensor_panel, text='Sensor color:')
        self.colorsensor_combo = self.createCombobox(self.combosensor_panel, self.colors_combo)

        self.apply_btn_sensor = self.createButton(self.options_sensor, "Apply", self.apply_btn_sensor)
        self.quit_btn_sensor = self.createButton(self.options_sensor, "Quit", self.hideOptionsSensor)

        self.placeWidget(self.video_ch_panel, 0, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.video_ch_label, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.video_ch_entry, 0, 1, (W, E), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.distance_marker_panel, 1, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.distance_marker_label, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.distance_marker_entry, 0, 1, (W, E), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.offset_panel, 2, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.offset_label, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.offset_entry, 0, 1, (W, E), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.chk_undistort, 3, 1, (W, E), TOP, X, 1, CENTER, choice=self.choice)

        self.placeWidget(self.combodir_panel, 4, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.colordir_label, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.colordir_combo, 0, 1, (W, E), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.combosensor_panel, 5, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.colorsensor_label, 0, 0, (W, E), LEFT, X, 1, W, choice=self.choice)
        self.placeWidget(self.colorsensor_combo, 0, 1, (W, E), RIGHT, NONE, 1, E, choice=self.choice)

        self.placeWidget(self.apply_btn_sensor, 6, 1, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.quit_btn_sensor, 7, 1, (W, E), TOP, X, 1, CENTER, choice=self.choice)

        self.setCurrentComboValue(self.colordir_combo, self.color_dir)
        self.setCurrentComboValue(self.colorsensor_combo, self.color_sensor)

    def lineCutFigureWindow(self):
        '''Open a new window display the cut lines graphs'''
        self.cut_figure_window = Toplevel(self.master)
        self.cut_figure_window.title("Interpolation line cut drawing")
        # geom = "700x725+50+50"
        # self.cut_figure_window.geometry(geom)
        self.cut_figure_window.protocol('WM_DELETE_WINDOW', self.hideCutFigure)
        self.figCut = Figure(figsize=(7, 7), dpi=self.dpifig)
        self.subXFigCut = self.figCut.add_subplot(211)
        self.subYFigCut = self.figCut.add_subplot(212)
        self.canvas_figCut = FigureCanvasTkAgg(self.figCut, master=self.cut_figure_window)
        self.canvas_figCut.show()
        self.figCutButtonPanel = self.createSubPanel(self.cut_figure_window)
        self.clean_btn = self.createButton(self.figCutButtonPanel, 'Clean figure', self.figClean)
        self.quit_btn_figcut = self.createButton(self.figCutButtonPanel, 'Close figure', self.figClose)

        self.placeWidget(self.canvas_figCut.get_tk_widget(), 0, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.figCutButtonPanel, 1, 0, (W, E), TOP, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.clean_btn, 0, 0, (W, E), LEFT, X, 1, CENTER, choice=self.choice)
        self.placeWidget(self.quit_btn_figcut, 0, 1, (W, E), RIGHT, X, 1, CENTER, choice=self.choice)

    def apply_btn(self):
        '''Set and store the values present in the fields of DAQ Options window'''
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
        '''Set and store the values present in the fields of Sensor Options window'''
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
        try:
            self.color_dir = self.colordir_combo.get()
        except:
            self.color_dir = 'yellow'
        try:
            self.color_sensor = self.colorsensor_combo.get()
        except:
            self.color_sensor = 'pink'
        self.writeConfig()

    def figClean(self):
        '''Clean the figure'''
        self.cleanPlot(self.subXFigCut)
        self.cleanPlot(self.subYFigCut)
        self.canvas_figCut.show()

    def cleanPlot(self, plotToClean):
        '''Clean the plot'''
        plotToClean.cla()

    def figClose(self):
        '''Close the figure'''
        self.figClean()
        self.hideCutFigure()

    def hideOptions(self):
        '''Hide the Options TopLevel window'''
        self.options.withdraw()

    def hideOptionsSensor(self):
        '''Hide the Options TopLevel window'''
        self.options_sensor.withdraw()

    def hideCutFigure(self):
        '''Hide the Line Cut Figure window'''
        self.cut_figure_window.withdraw()

    def showCutFigure(self):
        '''Show the Line Cut Figure window'''
        self.cut_figure_window.deiconify()

    def showOptions(self):
        '''Show the Options TopLevel window'''
        self.options.deiconify()

    def showOptionsSensor(self):
        '''Show the Options TopLevel window'''
        self.options_sensor.deiconify()

    def saveScatter(self):
        '''Save the scattered points figure'''
        self.saveImage(self.figScatt)

    def saveInterp(self):
        '''Save the interpolated points figure'''
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
                    self.dataanalysis.saveData(fname)
                except:
                    return

    def calibCam(self):
        '''Calibrate the distortion matrix of the camera'''
        self.mtx, self.dist = self.camcorr.calibrate()
        self.writeConfig()

    def calibSensor(self):
        '''Calibrate the sensor in order to remove the offset'''
        self.defaultSettings(isCalibrating=True)
        self.carto = carto4Dcam.Carto4D(dev_name=self.dev_name, ch_name=self.ch_name, data_nb=self.data_nb,
                                        rate=self.rate)
        self.thread = Acquisition(dev_name=self.dev_name, ch_name=self.ch_name, data_nb=self.data_nb, rate=self.rate,
                                  queue=self.queue, queuestart=self.queuestart, cartoObj=self.carto,
                                  isCalibrating=self.isCalibrating)
        self.start_button.config(state="disabled")
        self.quit_button.config(state="disabled")
        self.thread.start()
        self.processAcquisition()
        self.SDataMean = self.carto.getSDataMean()
        self.setMsgLabel('Ready to start...')
        self.start_button.config(state="normal")
        self.quit_button.config(state="normal")
        self.isCalibrating = False

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
            self.color_sensor = self.config['Camera']['color_sensor']
            self.color_dir = self.config['Camera']['color_dir']
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
            self.color_dir = 'yellow'
            self.color_sensor = 'pink'
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
                                 'undistort': (self.undistortImg),
                                 'color_sensor': (self.color_sensor),
                                 'color_dir': (self.color_dir)}
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def setMsgLabel(self, text):
        '''Set the label message'''
        self.msgLabel.config(text=text)

    def onpress(self, event):
        '''Get the position of the mouse on the figure when clicking'''
        Z, Xline, Yline = self.dataanalysis.getDataAtPoint(event.xdata, event.ydata)
        self.dataanalysis.plotIntersec(Xline, Yline, self.subXFigCut, self.subYFigCut)
        self.showCutFigure()
        self.canvas_figCut.show()

    def defaultSettings(self, isCalibrating=False):
        '''Defaults parameters'''
        self.isCalibrating = isCalibrating
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


class Acquisition(Thread):
    '''Thread Acquisition class use to run the camera and analyze the data without freezing the GUI'''

    def __init__(self, camcorr='', dev_name='Dev1', ch_name=['ai0'], data_nb=1000, rate=50000.0, xOffset=2, video_ch=1,
                 distance_marker=30, mtx=[], dist=[], undistortImg=1, canvasScatt='', subScatt='', canvasInterp='',
                 subInterp='', queue='', queuestart='', cartoObj='', mouseObj='', isCalibrating=False):
        Thread.__init__(self)
        self.camcorr = camcorr
        self.dev_name = dev_name
        self.ch_name = ch_name
        self.data_nb = data_nb
        self.rate = rate
        self.xOffset = xOffset
        self.video_ch = video_ch
        self.distance_marker = distance_marker
        self.mtx = mtx
        self.dist = dist
        self.undistortImg = undistortImg
        self.canvasScatt = canvasScatt
        self.subScatt = subScatt
        self.canvasInterp = canvasInterp
        self.subInterp = subInterp
        self.queue = queue
        self.queuestart = queuestart
        self.carto = cartoObj
        self.dataanalysis = mouseObj
        self.isCalibrating = isCalibrating

    def run(self):
        self.queuestart.put(True)
        if self.isCalibrating:
            self.carto.startDAQTask()
            self.queue.put("DAQ device Started")
            self.carto.acquireSData()
            self.queue.put("Calibration data Acquired")
            self.carto.stopDAQTask()
            self.queue.put("DAQ device Stopped")
            self.carto.calibSData()
        else:
            self.queue.put("Created carto3D object")
            self.carto.initCamera()
            self.queue.put("Initialized Camera")
            self.carto.startDAQTask()
            self.queue.put("DAQ device Started")
            self.carto.startCamera()
            self.queue.put("Camera started: press Esc. to stop the acquisition")
            self.carto.acquire4D()
            self.carto.stopCamera()
            self.queue.put("Camera stopped")
            self.carto.stopDAQTask()
            self.queue.put("DAQ device Stopped")
            self.points4D = self.carto.getCarto4D()
            self.ch_nb = self.carto.getchnb()
            self.dataanalysis.setData(self.points4D)
            self.dataanalysis.setChNb(self.ch_nb)
            if self.points4D != []:
                self.queue.put("Analyzing data")
                self.dataanalysis.nDimArrays()
                self.dataanalysis.scaleSData()
                self.dataanalysis.sort3D()
                self.dataanalysis.normalizeCmap()
                self.queue.put("Plotting data")
                self.dataanalysis.plotScatter(self.subScatt)
                self.dataanalysis.plotInterp(self.subInterp)
                self.canvasScatt.draw()
                self.canvasInterp.show()
                self.queue.put("Data plotted")
            else:
                self.queue.put("DAQ device not working")

        self.queue.put("Ready to start again...")
        time.sleep(0.5)
        self.queuestart.put(False)


if __name__ == "__main__":
    App = GUI()
