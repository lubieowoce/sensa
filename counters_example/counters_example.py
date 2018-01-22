from types_util import (
	Any,
	PMap_,
	Action,
)
from pyrsistent import (m, pmap, pvector)


from id_eff import IdEff, id_and_effects, run_id_eff, get_ids
from counter import (
	counter, update_counter,
	SET_VALUE,
	INCREMENT,
	DECREMENT,
)

from counter_list import (
	update_counter_list,
	ADD_COUNTER,
	REMOVE_COUNTER,
	CLEAR_COUNTERS,
)




@id_and_effects
def initial_state() -> IdEff[PMap_[str, Any]]:
	n_counters = 4
	cos = [counter(id) for id in get_ids(n_counters)]
	return m(counters=    pmap(   {co.id: co for co in cos}),
			 counter_list=pvector([co.id     for co in cos])  )


state, current_id, _ = run_id_eff(initial_state, id=current_id)()




@id_and_effects
def update(state: PMap_[str, Any], action: Action) -> IdEff[PMap_[str, Any]]:
	# state = { counters: {id: counter},
	#           counter_list: [id]       }
	if action.type in [ADD_COUNTER, REMOVE_COUNTER, CLEAR_COUNTERS]:
		return update_counter_list(state, action)

	elif action.type in [INCREMENT, DECREMENT, SET_VALUE]:
		id = action.id
		return state.transform(['counters', id],
							   lambda counter: update_counter(counter, action))
	else:
		return state