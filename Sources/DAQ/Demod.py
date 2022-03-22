import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

nbsample = 10000
frequency = 100
frequency_mod = 10
amplitude = 1

time = []
carrier = []
modulate = []
sampleperperiod = nbsample / frequency
sampleperperiod_mod = nbsample / frequency_mod
for idx in range(nbsample - 1):
    if idx == 0:
        carrier = [0]
        time = [0]
        modulate = [0]
    else:
        carrier.append(amplitude * np.sin(2 * np.pi * idx / sampleperperiod))
        modulate.append(amplitude * np.sin(2 * np.pi * idx / sampleperperiod_mod))
        time.append(idx / sampleperperiod)
# c = carrier * modulate
carrier = np.array(carrier)
modulate = np.array(modulate)
noise = np.random.randn(len(carrier)) * 0.9

mod_signal = carrier * (1 + 0.3 * modulate)
noisy_signal = mod_signal + noise

demod_x2 = noisy_signal * carrier

# Filter
frequency_filter = 0.5
freq_filter_rad = frequency_filter * np.pi / 180
print(freq_filter_rad)
# b, a = signal.butter(2, freq_filter_rad)
b, a = signal.bessel(4, freq_filter_rad, 'low')
zi = signal.lfilter_zi(b, a)
z, _ = signal.lfilter(b, a, demod_x2, zi=zi * demod_x2[0])
z2, _ = signal.lfilter(b, a, z, zi=zi * z[0])
filtered_demod = signal.filtfilt(b, a, demod_x2) * 2

plt.figure
plt.plot(time, noisy_signal, 'r')
# plt.plot(time, demod_x2, 'b')
plt.plot(time, filtered_demod, 'k')
plt.show()
