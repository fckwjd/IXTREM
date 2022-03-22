from PyDAQmx import *
import numpy
import matplotlib.pyplot as plt

# Declaration of variable passed by reference
taskHandle = TaskHandle()
read = int32()
data = numpy.zeros((20,), dtype=numpy.float64)

try:
    # DAQmx Configure Code
    DAQmxCreateTask("", byref(taskHandle))
    DAQmxCreateAIVoltageChan(taskHandle, "cDAQ9191-187C90EMod1/ai0,cDAQ9191-187C90EMod1/ai1", "", DAQmx_Val_Cfg_Default,
                             -10.0, 10.0, DAQmx_Val_Volts, None)
    DAQmxCfgSampClkTiming(taskHandle, "", 100000.0, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, 10)

    # DAQmx Start Code
    DAQmxStartTask(taskHandle)

    # DAQmx Read Code
    DAQmxReadAnalogF64(taskHandle, 10, 10.0, DAQmx_Val_GroupByChannel, data, 20, byref(read), None)

    print("Acquired %d points" % read.value)
except DAQError as err:
    print("DAQmx Error: %s" % err)
finally:
    if taskHandle:
        # DAQmx Stop Code
        DAQmxStopTask(taskHandle)
        DAQmxClearTask(taskHandle)
X = data[0:9]
Y = data[10:19]
plt.plot(X, Y)
plt.show()
