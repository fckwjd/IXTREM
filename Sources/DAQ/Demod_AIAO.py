import DAQ_MultipleChannel_Thread as daqmt
import DAQ_AnalogOutput as daqao

if __name__ == '__main__':
    import time
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from scipy import signal
    import numpy as np

    device = 'Dev1'
    ch_name = ['_ao0_vs_aognd', 'ai0']
    ao_device = 'Dev1/ao0'
    rate = 125000.0
    sampsPerChanToAcquire = 125000
    frequency = 10000
    amplitude = 8.
    signalType = 'sinus'
    dataByCh = None
    value = 0.0
    minVal = -1.0
    maxVal = 1.0

    # Initialize Acquisition and generation
    acquisition = daqmt.AIMultipleChannel(device, ch_name, sampsPerChanToAcquire, rate, minVal, maxVal)
    generate = daqao.AnalogOutput(ao_device, -10.0, 10.0)

    # Configure and start signal generation
    generate.configClock(rate, sampsPerChanToAcquire)
    generate.generateContinuousPulseTrain(rate, sampsPerChanToAcquire, frequency, signalType, amplitude)
    generate.writeAnalog()

    # Start Acquisition
    acquisition.StartTask()
    print('Please wait further instructions...')
    try:
        while True:
            # Acquire data
            data = acquisition.get_data(timeout=10.0)
            nb_data_ch = int(len(data) / len(ch_name))
            # Order data in dictionnary
            if dataByCh == None:
                dataByCh = dict(
                    [(name, data[nb_data_ch * idx:nb_data_ch * (idx + 1) - 1]) for idx, name in enumerate(ch_name)])
                # dataByCh0 = dict([(name, data[nb_data_ch*idx:nb_data_ch*(idx+1)-1]) for idx,name in enumerate(ch_name)])
                print('Ctrl + C to interrupt the acquisition')
            else:
                idx = 0
                for name in ch_name:
                    data_tmp = []
                    data_tmp = dataByCh[name]
                    data_tmp = np.append(data_tmp, data[nb_data_ch * idx:nb_data_ch * (idx + 1) - 1])
                    dataByCh[name] = data_tmp
                    idx += 1
    except KeyboardInterrupt:
        # Interrupt loop if Ctrl+C pressed
        pass
    print('Acquisition stopped')

    # Stop and clear acquisition and signal generation
    acquisition.StopTask()
    acquisition.ClearTask()
    generate.stop()
    generate.clear()

    # Set CC voltage to 0 afterwards
    print('Set CC voltage to 0')
    generate.createNewTask(ao_device, -1.0, 1.0)
    generate.start()
    generate.WriteAnalogScalarF64(1, 10.0, value, None)
    generate.stop()
    generate.clear()
    print('CC voltage Set')

    # Create time scale
    time = np.arange(len(dataByCh['ai0'])) / rate

    reference = dataByCh0['_ao0_vs_aognd']

    print('Calculate spectrum')
    sp = np.fft.fft(reference, len(reference))
    freq = np.fft.fftfreq(reference.size, d=1. / rate)
    magnitude = np.sqrt((sp.real / len(reference)) ** 2 + (sp.imag / len(reference)) ** 2) * 2
    phase = np.arctan2(sp.imag / len(reference), sp.real / len(reference))

    amplitude_ref = max(magnitude[freq >= 0])
    freq_ref = freq[np.argmax(magnitude[freq >= 0])]
    phase_ref = phase[np.argmax(magnitude[freq >= 0])]
    print(phase_ref)
    print(freq_ref)
    cos_ref = amplitude_ref * np.cos(2 * np.pi * freq_ref * time + phase_ref)
    sin_ref = amplitude_ref * np.sin(2 * np.pi * freq_ref * time + phase_ref)

    noisy_signal = dataByCh['ai0']

    print('Demodulate')
    # Demodulation
    In = noisy_signal * cos_ref
    Qn = noisy_signal * sin_ref

    # Filter
    frequency_filter = 0.5
    freq_filter_rad = frequency_filter * np.pi / 180
    # b, a = signal.butter(2, freq_filter_rad)
    b, a = signal.bessel(4, freq_filter_rad, 'low')
    zi = signal.lfilter_zi(b, a)

    Inz, _ = signal.lfilter(b, a, In, zi=zi * In[0])
    Inz2, _ = signal.lfilter(b, a, Inz, zi=zi * Inz[0])
    filtered_In = signal.filtfilt(b, a, In) * 2

    Qnz, _ = signal.lfilter(b, a, Qn, zi=zi * Qn[0])
    Qnz2, _ = signal.lfilter(b, a, Qnz, zi=zi * Qnz[0])
    filtered_Qn = signal.filtfilt(b, a, Qn) * 2

    Amplitude_demod = np.sqrt(filtered_In ** 2 + filtered_Qn ** 2) * 2
    Phase_demod = np.arctan2(filtered_Qn, filtered_In) * 180 / np.pi
    q = int(rate / frequency * 10)
    q = 2
    Amplitude_demod = signal.decimate(Amplitude_demod, q)
    Phase_demod = signal.decimate(Phase_demod, q)
    time_decim = signal.decimate(time, q)

    print('Plot data')
    # print(sp.real)
    # Plot data
    plt.figure(1)
    # plt.plot(time,dataByCh['ai0'],'g')
    # plt.plot(time,dataByCh['_ao0_vs_aognd'],'b')
    plt.plot(time_decim, Amplitude_demod, 'r')

    # plt.figure(2)
    # plt.plot(freq, magnitude, freq, phase)
    # plt.plot(time, filtered_In,'r')
    # plt.plot(time, filtered_Qn,'g')

    plt.figure(3)
    plt.plot(time_decim, Phase_demod, 'b')

    # plt.figure(4)
    # plt.plot(time,cos_ref,'g')

    plt.show()
