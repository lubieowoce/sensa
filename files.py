# from utils import (err_unsupported_action)
from typing import (
	Any,
	Tuple, Dict,
)
from utils.types import (
	PMap_,
	IO_,
)
from utils import impossible
from sumtype import sumtype

from eff import (
	Eff, effectful,
	EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
from utils.types import (
	SignalId,
)

from eff import (
	Eff, effectful,
	SIGNAL_ID, 
	eff_operation,
	get_signal_ids,
)

from debug_util import debug_log

from pyrsistent import m

from eeg_signal import Signal
from read_edf import read_edf


class FileAction(sumtype):
	def Load(filename: str): ...


class FileEffect(sumtype):
	def Load(filename: str): ...




@effectful(SIGNAL_ID)
def handle_file_effect(signals: PMap_[SignalId, Signal],
					   signal_names: PMap_[SignalId, str],
					   command: FileEffect) -> IO_[ Tuple[ PMap_[SignalId, Signal],
														   PMap_[SignalId, str]    ] ]:

	if command.is_Load():
		new_signals = load_edf(command.filename)
		n_signals = len(new_signals)

		# assign each signal a unique signal_id

		# first, map ids to signal names
		new_signal_names = {sig_id: name
							for (sig_id, name)
							in zip(get_signal_ids(n_signals),
								   sorted(new_signals.keys())) # sorted so that ids are assigned deterministaclly
						   }
		# then, map the ids to the correct signals
		new_signals = {sig_id: new_signals[sig_name]
					   for (sig_id, sig_name) in new_signal_names.items()}


		return (signals.update(new_signals), signal_names.update(new_signal_names))
	else:
		impossible("Invalid File command:" + command)
		return (signals, signal_names)


def load_edf(filename: str) -> IO_[Dict[str, Signal]]:
	hdr, dat = read_edf(filename)
	data = [(label,  hdr['signal_infos'][label],  dat[label])  for label in hdr['labels']]
	signals = { label: Signal(info, sig) for label, info, sig in data }
	return signals

example_file_path = 'example_data/waves.edf'
# signal = chs[0]


