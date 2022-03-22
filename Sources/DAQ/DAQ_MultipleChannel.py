# coding= latin-1

import numpy as np
from PyDAQmx import *
from PyDAQmx.DAQmxCallBack import *
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *
from ctypes import *


class MultiChannelAnalogInput():
    """Class to create a multi-channel analog input
    
    Usage: AI = MultiChannelInput(physicalChannel)
        physicalChannel: a string or a list of strings
    optional parameter: limit: tuple or list of tuples, the AI limit values
                        reset: Boolean
    Methods:
        read(name), return the value of the input name
        readAll(), return a dictionary name:value
    """

    def __init__(self, physicalChannel, limit=None, nbSample=None, reset=False):
        if type(physicalChannel) == type(""):
            self.physicalChannel = [physicalChannel]
        else:
            self.physicalChannel = physicalChannel
        self.numberOfChannel = physicalChannel.__len__()
        if limit is None:
            self.limit = dict([(name, (-10.0, 10.0)) for name in self.physicalChannel])
        elif type(limit) == tuple:
            self.limit = dict([(name, limit) for name in self.physicalChannel])
        else:
            self.limit = dict([(name, limit[i]) for i, name in enumerate(self.physicalChannel)])

        if nbSample is None:
            self.nbSample = dict([(name, (250000, 250000)) for name in self.physicalChannel])
        elif type(nbSample) == tuple:
            self.nbSample = dict([(name, nbSample) for name in self.physicalChannel])
        else:
            self.nbSample = dict([(name, nbSample[i]) for i, name in enumerate(self.physicalChannel)])

        if reset:
            DAQmxResetDevice(physicalChannel[0].split('/')[0])

    def configure(self):
        # Create one task handle per Channel
        taskHandles = dict([(name, TaskHandle(0)) for name in self.physicalChannel])
        for name in self.physicalChannel:
            DAQmxCreateTask("", byref(taskHandles[name]))
            DAQmxCreateAIVoltageChan(taskHandles[name], name, "", DAQmx_Val_Diff,
                                     self.limit[name][0], self.limit[name][1],
                                     DAQmx_Val_Volts, None)
        self.taskHandles = taskHandles

    def readAll(self):
        return dict([(name, self.read(name)) for name in self.physicalChannel])

    def read(self, name=None):
        if name is None:
            name = self.physicalChannel[0]
        taskHandle = self.taskHandles[name]
        DAQmxStartTask(taskHandle)
        data = np.zeros((self.nbSample[name][0],), dtype=np.float64)
        read = int32()
        DAQmxReadAnalogF64(taskHandle, self.nbSample[name][0], 10.0, DAQmx_Val_GroupByChannel, data,
                           self.nbSample[name][1], byref(read), None)
        DAQmxStopTask(taskHandle)
        return data


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


if __name__ == '__main__':
    import time
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from scipy import signal

    device = b'Dev1/ao0'
    rate = 2000.0
    sampsPerChanToAcquire = 8000
    frequency = 20
    amplitude = 0.5
    signalType = 'sinus'

    task = AnalogOutput(device, -1.0, 1.0)

    taskHandle = task.getTaskHandle()
    task.configClock(rate, sampsPerChanToAcquire)
    task.generateContinuousPulseTrain(rate, sampsPerChanToAcquire, frequency, signalType, amplitude)
    task.writeAnalog()

    multipleAI = MultiChannelAnalogInput(["Dev1/ai0", "Dev1/_ao0_vs_aognd"], [(-1.0, 1.0), (-1.0, 1.0)],
                                         [(sampsPerChanToAcquire, sampsPerChanToAcquire),
                                          (sampsPerChanToAcquire, sampsPerChanToAcquire)])
    multipleAI.configure()
    data = multipleAI.readAll()
    # print(data)

    # Wait...it is generating a signal
    # time.sleep(3)
    task.stop()
    task.clear()

    # New task to set the last value to 0, generate a CC 0 V signal
    value = 0.0
    task.createNewTask(device, -1.0, 1.0)
    taskHandle = task.getTaskHandle()

    task.start()
    task.WriteAnalogScalarF64(1, 10.0, value, None)
    task.stop()
    task.clear()

    # print(type(data))
    fig = plt.figure(1)
    # t = range(0, len(data['Dev1/ai0']))
    t = np.arange(len(data['Dev1/ai0'])) / rate

    carrier = data['Dev1/_ao0_vs_aognd']
    noisy_signal = data['Dev1/ai0']

    demod_x2 = noisy_signal * carrier

    # Filter
    frequency_filter = 0.5
    freq_filter_rad = frequency_filter * np.pi / 180
    # b, a = signal.butter(2, freq_filter_rad)
    b, a = signal.bessel(4, freq_filter_rad, 'low')
    zi = signal.lfilter_zi(b, a)
    z, _ = signal.lfilter(b, a, demod_x2, zi=zi * demod_x2[0])
    z2, _ = signal.lfilter(b, a, z, zi=zi * z[0])
    filtered_demod = signal.filtfilt(b, a, demod_x2) * 2

    plt.figure
    # plt.plot(t,noisy_signal,'r')
    # plt.plot(t,carrier,'g')
    # plt.plot(t, demod_x2, 'b')
    # plt.plot(t, filtered_demod,'k')
    # plt.show()  

    sp = np.fft.fft(carrier)
    freq = np.fft.fftfreq(carrier.size, d=1. / rate)
    plt.plot(freq, sp.real, freq, sp.imag)
    plt.show()

    # print(data['Dev1/ai0'])
    # plt.plot(t,data['Dev1/ai0'],'r')

    # plt.plot(t,data['Dev1/_ao0_vs_aognd'],'b')
    # plt.show()
