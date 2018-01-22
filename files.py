# from sensa_util import (err_unsupported_action)
from typing import (
	Any,
	Dict,
)
from types_util import (
	PMap_,
	IO_,
)
from sensa_util import impossible
from uniontype import union

from pyrsistent import m

from eeg_signal import Signal
from read_edf import read_edf


FileEffect, \
	Load_, \
= union(
'FileEff', [
	('Load', [('filename', str)]),
]
)


FileAction, \
	Load, \
= union(
'FileAction', [
	('Load', [('filename', str)]),
]
)





def handle_file_effect(signals: PMap_[str, Signal], command: FileEffect) -> IO_[PMap_[str, Signal]]:
	if command.is_Load():
		new_signals = load_edf(command.filename)
		return signals.update(new_signals)
	else:
		impossible("Invalid File command:" + command)
		return signals


def load_edf(filename: str) -> IO_[Dict[str, Signal]]:
	hdr, dat = read_edf(filename)
	data = [(label,  hdr['signal_infos'][label],  dat[label])  for label in hdr['labels']]
	signals = { label: Signal(info, sig) for label, info, sig in data }
	return signals

example_file_path = 'example_data/waves.edf'
# signal = chs[0]


