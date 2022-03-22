""" Simple example of analog output

    This example outputs 'value' on ao0
"""
from PyDAQmx import *
# from PyDAQmx.DAQmxCallBack import *
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *
import numpy as np

value = 0.0

task = Task()
task.CreateAOVoltageChan(b'Dev1/ao0', "", -10.0, 10.0, DAQmx_Val_Volts, None)
task.StartTask()
task.WriteAnalogScalarF64(1, 10.0, value, None)
task.StopTask()
task.ClearTask()
