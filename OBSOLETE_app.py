print("running main.py")

from types_util import *
from eeg_signal import Signal
from multisignal import MultiSignal
from read import read_edf
from filters import \
	lowpass_filter,  make_lowpass_tr, \
	highpass_filter, make_highpass_tr
from trans import Trans, TransChain
# import biosppy.signals.eeg as e 
import matplotlib.pyplot as plt




hdr, sig = read_edf('example_data/waves.edf')

data = [(hdr['signal_infos'][label], sig[label])  for label in hdr['labels']]
channels = chs = [Signal(info, sig) for info, sig in data]
# signal   = s   = Signal(channels[7:11]) # these have the same frequency
# signal   = s   = Signal(channels[7:9]) # these have the same frequency

# ms = s.as_column_matrix()
# e.eeg(ms, sampling_rate=200, show=True)

signal = chs[0]

lp_tr = make_lowpass_tr()
hp_tr = make_highpass_tr()

tc = TransChain([lp_tr, hp_tr])

signal2 = tc(signal)


plt.subplot(2, 1, 2)
plt.plot(signal.data, 'b-', label='data')
plt.plot(signal2.data, 'g-', linewidth=2, label='filtered data')
plt.xlabel('T')
plt.grid()
plt.legend()

# plt.subplots_adjust(hspace=0.35)
plt.show()