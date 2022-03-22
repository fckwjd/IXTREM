# -*- coding: utf-8 -*-
from PyDAQmx import *
from PyDAQmx.DAQmxCallBack import *
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *
import threading


class CallbackTaskSynchronous(Task):
    """This class is in charge of acquirering data continuously from a DAQmx device"""

    def __init__(self, dev_name=None, ch_name_ai=None, ch_name_ao=None, data_len=1000, data_nb=100, rate=50000.0,
                 max_value=10.0, value_ao=10.0):
        Task.__init__(self)
        self.ch_nb = 0
        if dev_name is None:
            dev_name = "Dev1"
        # Check and set the AI channel name
        if ch_name_ai is None:
            ch_name_ai = "ai0"
            self.phys_chan_ai = dev_name + "/" + ch_name_ai
            self.ch_nb = 1
        elif type(ch_name_ai) is list:
            self.phys_chan_ai = ""
            idx = 0
            for name in ch_name_ai:
                if idx == len(ch_name_ai) - 1:
                    self.phys_chan_ai = self.phys_chan_ai + dev_name + "/" + name
                else:
                    self.phys_chan_ai = self.phys_chan_ai + dev_name + "/" + name + ','
                    idx = idx + 1
            self.ch_nb = len(ch_name_ai)
        elif type(ch_name_ai) is str:
            self.phys_chan_ai = dev_name + "/" + ch_name_ai
            self.ch_nb = 1
        # Check and set the AO channel name
        if ch_name_ao is None:
            self.isAOchan = False
        elif type(ch_name_ao) is list:
            self.isAOchan = True
            self.phys_chan_ao = ""
            idx = 0
            for name in ch_name_ao:
                if idx == len(ch_name_ao) - 1:
                    self.phys_chan_ao = self.phys_chan_ao + dev_name + "/" + name
                else:
                    self.phys_chan_ao = self.phys_chan_ao + dev_name + "/" + name + ','
                    idx = idx + 1
            self.ch_nb = len(ch_name_ao)
        elif type(ch_name_ao) is str:
            self.isAOchan = True
            self.phys_chan_ao = dev_name + "/" + ch_name_ao

        self.isRunning = True
        self.data_nb = data_nb
        self._data = numpy.zeros(self.data_nb * self.ch_nb)
        self.rate = rate
        self.read = c_int32()
        self.maxvalue_ai = max_value
        self.minvalue_ai = -max_value
        self.maxvalue_ao = max_value
        self.minvalue_ao = -max_value

        taskHandle = TaskHandle(0)
        try:
            DAQmxCreateTask("", byref(taskHandle))
            self.taskHandle = taskHandle
            DAQmxCreateAIVoltageChan(self.taskHandle, self.phys_chan_ai, "", DAQmx_Val_Diff, self.minvalue_ai,
                                     self.maxvalue_ai, DAQmx_Val_Volts, None)
            if self.isAOchan:
                DAQmxCreateAOVoltageChan(self.taskHandle, self.phys_chan_ao
                self.minvalue_ao, self.maxvalue_ao, DAQmx_Val_Volts, None)
                DAQmxCfgSampClkTiming(self.taskHandle, None, self.rate, DAQmx_Val_Rising, DAQmx_Val_ContSamps,
                                      self.data_nb)
                self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer, self.data_nb, 0)
                self.AutoRegisterDoneEvent(0)
                self._data_lock = threading.Lock()
                self._newdata_event = threading.Event()
            except:
            self.isRunning = False

    def EveryNCallback(self):
        try:
            with self._data_lock:
                self.ReadAnalogF64(self.data_nb, 10.0, DAQmx_Val_GroupByChannel, self._data, self.data_nb * self.ch_nb,
                                   byref(self.read), None)
                if isAOchan:
                    self.WriteAnalogScalarF64(1, 10.0, value_a0, None)
                self._newdata_event.set()
        except:
            # self.isRunning = False
            None
        return 0  # The function should return an integer

    def DoneCallback(self, status):
        print("Status", status.value)
        return 0  # The function should return an integer

    def get_data(self, blocking=True, timeout=None):
        if blocking:
            if not self._newdata_event.wait(timeout):
                raise ValueError("timeout waiting for data from device")
        with self._data_lock:
            self._newdata_event.clear()
            return self._data.copy()

    def getIsRunning(self):
        return self.isRunning

    def setIsRunning(self, isRunning):
        self.isRunning = isRunning
