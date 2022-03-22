from PyDAQmx import *
from PyDAQmx.DAQmxCallBack import *
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *
import numpy as np
from ctypes import *


class AnalogOutput(Task):
    def __init__(self, dev_name=b'Dev1/ao0', minVal=-10.0, maxVal=10.0):
        taskHandle = TaskHandle(0)
        DAQmxCreateTask("", byref(taskHandle))
        self.taskHandle = taskHandle
        ch = DAQmxCreateAOVoltageChan(self.taskHandle, dev_name, "", minVal, maxVal, DAQmx_Val_Volts, None)

    def createNewTask(self, dev_name=b'Dev1/ao0', minVal=-10.0, maxVal=10.0):
        taskHandle = TaskHandle(0)
        DAQmxCreateTask("", byref(taskHandle))
        self.taskHandle = taskHandle
        ch = DAQmxCreateAOVoltageChan(self.taskHandle, dev_name, "", minVal, maxVal, DAQmx_Val_Volts, None)

    def getTaskHandle(self):
        return self.taskHandle

    def configClock(self, rate=250000.0, sampsPerChanToAcquire=250000):
        DAQmxCfgSampClkTiming(self.taskHandle, '', rate, DAQmx_Val_Rising, DAQmx_Val_ContSamps, sampsPerChanToAcquire)

    def generateContinuousPulseTrain(self, rate=1000, nbsample=1000, frequency=100, signaltype='sinus', amplitude=1.0):
        dataarray = []
        timestep = 1. / rate
        sampleperperiod = rate / frequency
        for idx in range(nbsample - 1):
            if signaltype == 'sinus':
                if idx == 0:
                    dataarray = [0]
                else:
                    dataarray.append(amplitude * np.sin(2 * np.pi * frequency * idx * timestep))
            if signaltype == 'square':
                if (idx % sampleperperiod) <= sampleperperiod / 2:
                    dataarray.append(amplitude)
                else:
                    dataarray.append(-amplitude)

        self.dataarray = np.array(dataarray)
        self.nbsample = nbsample
        self.sampsPerChanWritten = c_int32()

    def writeAnalog(self):
        dataarray = self.dataarray
        nbsample = self.nbsample
        sampsPerChanWritten = self.sampsPerChanWritten
        DAQmxWriteAnalogF64(self.taskHandle, nbsample, 1, 1.0, DAQmx_Val_GroupByChannel, dataarray, sampsPerChanWritten,
                            reserved=None)

    def writeAnalogSingle(self, value=0.0):
        DAQmxWriteAnalogScalarF64(self.taskHandle, 1, 1.0, value, reserved=None)

    def start(self):
        DAQmxStartTask(self.taskHandle)

    def stop(self):
        DAQmxStopTask(self.taskHandle)

    def clear(self):
        DAQmxClearTask(self.taskHandle)


if __name__ == "__main__":
    device = b'Dev1/ao0'
    rate = 250000.0
    sampsPerChanToAcquire = 250000
    frequency = 10000
    amplitude = 0.5
    signalType = 'square'

    task = AnalogOutput(device, -1.0, 1.0)

    taskHandle = task.getTaskHandle()
    task.configClock(taskHandle, rate, sampsPerChanToAcquire)
    task.generateContinuousPulseTrain(sampsPerChanToAcquire, frequency, signalType, amplitude)
    task.writeAnalog(taskHandle)

    # Wait...it is generating a signal
    time.sleep(3)
    task.stop(taskHandle)
    task.clear(taskHandle)

    # New task to set the last value to 0, generate a CC 0 V signal
    value = 0.0
    task.createNewTask(device, -1.0, 1.0)
    taskHandle = task.getTaskHandle()

    task.start(taskHandle)
    task.WriteAnalogScalarF64(1, 10.0, value, None)
    task.stop(taskHandle)
    task.clear(taskHandle)
