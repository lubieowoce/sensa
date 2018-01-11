print("running main.py")

from types_util import *
from eeg_signal import Signal
from read import read_edf
import matplotlib.pyplot as plt


from files import load_edf, example_file

signals = load_edf(example_file)
signal = signals['C3']



# plt.subplot(2, 1, 2)
plt.plot(signal.data, 'b-', label='data')
plt.xlabel('T')
plt.grid()
plt.legend()

# plt.subplots_adjust(hspace=0.35)
plt.show()