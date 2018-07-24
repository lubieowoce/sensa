import flags

def err_unsupported_action(action, state):
	raise Exception("Action " + str(action)+ " is not supported in state " + str(state) )


def bad_action(**kwargs):
	if flags.DEBUG:
		if 'msg' in kwargs:
			err_text = kwargs['msg']

		elif 'action' in kwargs and 'state' in kwargs:
			action = kwargs['action']
			state = kwargs['state']
			err_text = "Action " + str(action)+ " shouldn't happen in " + str(state)

		else:
			err_text = "Bad action"

		raise Exception(err_text)