# from util import (err_unsupported_action)

from types_util import *
from pyrsistent import (m, pmap, v, pvector, thaw, freeze)

from signal import Signal
from read import read_edf


LOAD_FILE = "LOAD_FILE"
LOAD_FILE_EFF = "LOAD_FILE_EFF"

load_file     = lambda filename: m(type=LOAD_FILE, filename=filename)
load_file_eff = lambda filename: m(type=LOAD_FILE_EFF, filename=filename)

def handle_load_file(signals: Dict[str, Signal], command: PMap_[str, Any]):
	hdr, dat = read_edf(command.filename)
	data = [(label,  hdr['signal_infos'][label],  dat[label])  for label in hdr['labels']]
	new_signals = { label: Signal(info, sig) for label, info, sig in data }
	signals.update(new_signals)


example_file = 'example_data/waves.edf'
# signal = chs[0]


