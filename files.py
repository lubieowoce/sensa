# from utils import (err_unsupported_action)
from typing import (
	Any,
	Tuple, Dict,
)
from utils.types import (
	SignalId,
	PMap_,
	IO_,
)
from sumtype import sumtype

from eff import (
	Eff, effectful,
	SIGNAL_ID, 
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



@effectful
async def handle_file_effect(
		signals: PMap_[SignalId, Signal],
		signal_names: PMap_[SignalId, str],
		command: FileEffect
	) -> Eff[[SIGNAL_ID],  IO_[  Tuple[ PMap_[SignalId, Signal], PMap_[SignalId, str] ]  ]]:

	if command.is_Load():
		new_signals = load_edf(command.filename)
		n_signals = len(new_signals)

		# assign each signal a unique signal_id

		# first, map ids to signal names
		new_signal_names = {sig_id: name
							for (sig_id, name)
							in zip(await get_signal_ids(n_signals),
								   # sorted so that ids are assigned deterministically
								   sorted(new_signals.keys()))
						   }
		# then, map the ids to the correct signals
		new_signals = {sig_id: new_signals[sig_name]
					   for (sig_id, sig_name) in new_signal_names.items()}


		return (signals.update(new_signals), signal_names.update(new_signal_names))
	else:
		command.impossible()
		return (signals, signal_names)


def load_edf(filename: str) -> IO_[Dict[str, Signal]]:
	hdr, dat = read_edf(filename)
	data = [(label,  hdr['signal_infos'][label],  dat[label])  for label in hdr['labels']]
	signals = { label: Signal(info, sig) for label, info, sig in data }
	return signals

example_file_path = 'example_data/waves.edf'
# signal = chs[0]


