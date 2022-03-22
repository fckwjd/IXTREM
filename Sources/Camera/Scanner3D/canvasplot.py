# -*- coding: utf-8 -*-
import matplotlib
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class CanvasPlot:
    def __init__(self):
        self.figScatt = Figure(figsize=(5, 5), dpi=100)
        self.subScatt = self.figScatt.add_subplot(111)
        self.figInterp = Figure(figsize=(5, 5), dpi=100)
        self.subInterp = self.figInterp.add_subplot(111)

    def getFig(self):
        return self.figScatt, self.figInterp

    def getSub(self):
        return self.subScatt, self.subInterp
