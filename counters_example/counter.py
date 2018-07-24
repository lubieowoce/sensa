from utils.types import (
	Action, WidgetState
)

from pyrsistent import m

from utils import err_unsupported_action

INCREMENT = "INCREMENT"
DECREMENT = "DECREMENT"
SET_VALUE = "SET_VALUE"
# counter_actions = \
# 	v( m(type=INCREMENT, n=..., id=...) ,
# 	   m(type=DECREMENT, n=..., id=...) )
increment = lambda n, id: m(type=INCREMENT, n=n, id=id)
decrement = lambda n, id: m(type=DECREMENT, n=n, id=id)
set_value = lambda val, id: m(type=SET_VALUE, val=val, id=id)

def counter(id) -> WidgetState:
	return m(id=id, val=0)
	#TODO: id should be a prop, not state?

# reducer
def update_counter(state: WidgetState, action: Action) -> WidgetState:
	if action.id != state.id:
		# action targets another widget
		return state

	if action.type == INCREMENT:
		new_counter = state.val + action.n
		return state.set('val', new_counter)

	elif action.type == DECREMENT:
		new_counter = state.val - action.n
		return state.set('val', new_counter)
		
	elif action.type == SET_VALUE:
		return state.set('val', action.val)
	else:
		err_unsupported_action(state, action)
		return state


