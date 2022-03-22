from PyDAQmx import *
import numpy
import matplotlib.pyplot as plt

# Declaration of variable passed by reference
taskHandle = TaskHandle()
read = c_int32()
data = numpy.zeros((10000,), dtype=numpy.float64)
dataT = []
for i in range(5):
    try:
        # DAQmx Configure Code
        DAQmxCreateTask("", byref(taskHandle))
        DAQmxCreateAIVoltageChan(taskHandle, "cDAQ9191-187C90EMod1/ai0", "", DAQmx_Val_Cfg_Default, -10.0, 10.0,
                                 DAQmx_Val_Volts, None)
        DAQmxCfgSampClkTiming(taskHandle, "", 10000.0, DAQmx_Val_Rising, DAQmx_Val_ContSamps, 10000)

        # DAQmx Start Code
        DAQmxStartTask(taskHandle)

        # DAQmx Read Code
        # for i in range(1):
        DAQmxReadAnalogF64(taskHandle, 10000, 10.0, DAQmx_Val_GroupByChannel, data, 10000, byref(read), None)
        dataT.append(data)
    #    print ("Acquired %d points"%read.value)
    except DAQError as err:
        print("DAQmx Error: %s" % err)
    finally:
        if taskHandle:
            # DAQmx Stop Code
            DAQmxStopTask(taskHandle)
            DAQmxClearTask(taskHandle)

t = numpy.arange(0.0, 5.0, 0.0001)
print(len(dataT))
plt.figure()
plt.plot(t, dataT)
plt.show()
