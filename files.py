# from sensa_util import (err_unsupported_action)



from types_util import *
from pyrsistent import (m, pmap, v, pvector, thaw, freeze)

from eeg_signal import Signal
from read import read_edf

LOAD_FILE = "LOAD_FILE"
LOAD_FILE_EFF = "LOAD_FILE_EFF"

load_file     = lambda filename: m(type=LOAD_FILE, filename=filename)
load_file_eff = lambda filename: m(type=LOAD_FILE_EFF, filename=filename)

def handle_load_file(signals: Dict[str, Signal], command: PMap_[str, Any]) -> IO_[None]:
	new_signals = load_edf(command.filename)
	signals.update(new_signals)


def load_edf(filename: str) -> IO_[Dict[str, Signal]]:
	hdr, dat = read_edf(filename)
	data = [(label,  hdr['signal_infos'][label],  dat[label])  for label in hdr['labels']]
	signals = { label: Signal(info, sig) for label, info, sig in data }
	return signals

example_file = 'example_data/waves.edf'
# signal = chs[0]


