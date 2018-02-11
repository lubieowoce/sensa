from typing import Any, Set, List, Dict, NamedTuple

from types_util import (
	Id, SignalId,
	PMap_,
)
from collections import namedtuple
from uniontype import union
from pyrsistent import s, m, pmap, pvector

from functools import reduce
from sensa_util import invert, impossible, Maybe, Nothing, Just
from eeg_signal import Signal
# Source, Trans, Sink?

import imgui as im
from eff import (
	Eff, effectful,
	ID, EFFECTS, SIGNAL_ID, ACTIONS,
	eff_operation,
)
from imgui_widget import window
from better_combo import str_combo_with_none

InputSlotId  = NamedTuple('InputSlotId',  [('node_id', Id), ('ix', int)])
OutputSlotId = NamedTuple('OutputSlotId', [('node_id', Id), ('ix', int)])

# Node:
#   Source : NodeId {InputSlotId  [0],  OutputSlotId [n]}
#   Trans  : NodeId {InputSlotId  [n] , OutputSlotId [k]}
#   Sink   : NodeId {InputSlotId  [n] , OutputSlotId [0]}
# Node: n_inputs: int, n_outputs: int

Node = NamedTuple('Node', [('n_inputs', int), ('n_outputs', int)])
# BoxSpec = Any
# Node = NamedTuple('Node', [('box', BoxSpec)])
# @property
# def n_inputs(node: Node) -> int:
# 	pass

Graph = namedtuple('Graph', ['nodes', 'links'])
# an isomorphic graph, where the nodes are pairs (node_id, [output|input]_slot_ix)
# would be tree like:
#   an output can be connected to multiple inputs,
#   but an input can be connected to only one output.
#   (for now - we might add 'variadic inputs',
#    or inputs that connect to any number of outputs) 
empty_graph = Graph(nodes=m(), links=s())



# node_boxes : Map[ NodeId, Id ]

# nodes : PMap_[Id, Node]

# links : Set[ (InputSlotId, OutputSlotId) ]

GraphAction, \
	AddNode, \
	RemoveNode, \
	Connect, \
	Disconnect, \
= union(
'GraphAction', [
	('AddNode',     [('id_', Id), ('node', Node)]),
	('RemoveNode',  [('id_', Id)]),
	('Connect',     [('source_slot', OutputSlotId), ('dest_slot', InputSlotId)]),
	('Disconnect',  [('source_slot', OutputSlotId), ('dest_slot', InputSlotId)]),
]
)


def update_graph(graph: Graph, action: GraphAction) -> Graph:
	nodes, links = graph.nodes, graph.links
	old_graph = graph

	if action.is_AddNode():
		new_graph = old_graph._replace(nodes=nodes.set(action.id_, action.node))

	elif action.is_RemoveNode():
		target_id = action.id_
		targets_links = {(src_slot, dst_slot) for (src_slot, dst_slot) in links
						 if src_slot.node_id == target_id or dst_slot.node_id == target_id}


		new_graph = old_graph._replace(nodes=nodes.remove(target_id),
									   links=links - targets_links)

	elif action.is_Connect():
		assert action.source_slot.node_id in nodes.keys()
		assert action.dest_slot.node_id in nodes.keys()

		assert action.source_slot in output_slots(graph)
		assert action.dest_slot in free_input_slots(graph)

		assert (action.source_slot, action.dest_slot) not in links

		new_graph = old_graph._replace(links=links.add( (action.source_slot, action.dest_slot) ))

	elif action.is_Disconnect():
		assert action.source_slot.node_id in nodes.keys()
		assert action.dest_slot.node_id in nodes.keys()
		assert (action.source_slot, action.dest_slot) in links

		new_graph = old_graph._replace(links=links.remove( (action.source_slot, action.dest_slot) ))

	else:
		impossible("Invalid graph action")


	return new_graph if new_graph is not old_graph else old_graph



test_actions = [
AddNode(0, Node(n_inputs=0, n_outputs=1)),
AddNode(1, Node(n_inputs=1, n_outputs=2)),
AddNode(2, Node(n_inputs=2, n_outputs=0)),
AddNode(3, Node(n_inputs=1, n_outputs=0)),

# Connect(OutputSlotId(node_id=0, ix=0), InputSlotId(node_id=1, ix=0)),
# Connect(OutputSlotId(node_id=0, ix=0), InputSlotId(node_id=3, ix=0)),
# Connect(OutputSlotId(node_id=1, ix=0), InputSlotId(node_id=2, ix=0)),
# Connect(OutputSlotId(node_id=1, ix=1), InputSlotId(node_id=2, ix=1)),
]
test_graph = reduce(update_graph, test_actions, empty_graph)



def output_slots(graph: Graph) -> Set[OutputSlotId]:
	return { OutputSlotId(id_, ix) for (id_, node) in graph.nodes.items()
									for ix in range(node.n_outputs) }

def used_output_slots(graph: Graph) -> Set[OutputSlotId]:
	return { src_slot for (src_slot, dst_slot) in graph.links }



def input_slots(graph: Graph) -> Set[OutputSlotId]:
	return { InputSlotId(id_, ix) for (id_, node) in graph.nodes.items()
									for ix in range(node.n_inputs) }

def filled_input_slots(graph: Graph) -> Set[InputSlotId]:
	return { dst_slot for (src_slot, dst_slot) in graph.links }


def free_input_slots(graph: Graph) -> Set[InputSlotId]:
	return input_slots(graph) - filled_input_slots(graph)


def node_inputs(graph: Graph, node_id: Id) -> List[OutputSlotId]:
	return [src_slot for (src_slot, dst_slot) in graph.links
			if dst_slot.node_id == node_id]


def graph_repr(graph: Graph) -> str:
	connections_repr = \
		["[ {s_id} ]({s_slot_ix}) -> ({d_slot_ix})[ {d_id} ]"\
		  .format(s_id=src.node_id, d_id=dst.node_id,
			  	  s_slot_ix=src.ix, d_slot_ix=dst.ix)
		 for (src, dst) in sorted(graph.links, key=lambda pair: (pair[1],pair[0]))]

	unused_nodes = set(graph.nodes.keys()) \
						- {slot.node_id for (src_slot, dst_slot) in graph.links
											for slot in (src_slot, dst_slot)}
	unused_repr = str(sorted(unused_nodes))

	return str.join('\n', connections_repr) + '\n\n' + unused_repr






def apply_maybe_fn(m_fn, *m_args):
	if any(m_arg.is_Nothing() for m_arg in m_args):
		return Nothing()
	if m_fn.is_Nothing():
		return Nothing()
	return Just(m_fn.val(*m_args))




def eval_outputs(graph: Graph, source_signals: Dict[SignalId, Signal], boxes: Dict[Id, Any]) -> Dict[Id, List[Maybe[Signal]]]:
	res = {}
	source_nodes = {id_: node for (id_, node) in graph.nodes.items()
					if node.n_inputs == 0}
	trans_nodes =  {id_: node for (id_, node) in graph.nodes.items()
					if node.n_inputs > 0 and node.n_outputs > 0}
	sink_nodes = {id_: node for (id_, node) in graph.nodes.items()
					if node.n_outputs == 0}

	for (id_, node) in source_nodes.items():
		eval_node = type(boxes[id_]).eval_node # hacky - should use something like interfaces/typeclasses
		m_output_values = apply_maybe_fn(eval_node(boxes[id_]), source_signals)
		res[id_] = pvector(m_output_values.val if m_output_values.is_Just()
						   else [Nothing() for _ in range(node.n_outputs)])


	# filters that only depend on source signals
	constant_trans_nodes = {id_: node for (id_, node) in trans_nodes.items()
							if all(src_slot.node_id in source_nodes.keys() for src_slot in node_inputs(graph, id_))}
	# filters that depend on at least one other filter
	variable_trans_nodes = {id_: node for (id_, node) in trans_nodes.items()
							if any(src_slot.node_id in trans_nodes.keys() for src_slot in node_inputs(graph, id_))}

	for node_group in (constant_trans_nodes, variable_trans_nodes, sink_nodes):
		for (id_, node) in node_group.items():
			input_values = [ res[src_slot.node_id][src_slot.ix] for src_slot in node_inputs(graph, id_)]
			eval_node = type(boxes[id_]).eval_node
			m_output_values = apply_maybe_fn(eval_node(boxes[id_]), input_values)
			res[id_] = pvector(m_output_values.val if m_output_values.is_Just()
							   else [Nothing() for _ in range(node.n_outputs)])

	return pmap(res)




def get_inputs(graph: Graph, output_values: Dict[Id, List[Maybe[Signal]]]) -> Dict[Id, List[Maybe[Signal]]]:
	return \
		{ id_: [ output_values[src_slot.node_id][src_slot.ix]
			    for src_slot in node_inputs(graph, id_) ]
		  for (id_, node) in  graph.nodes.items() }



SELECTED_SLOTS_CONNECT = {
	'source': None,
	'dest':   None,
}

SELECTED_SLOTS_DISCONNECT = {
	'source': None,
	'dest':   None,
}

@effectful(ACTIONS)
def graph_window(graph: Graph):
	emit = eff_operation('emit')

	with window(name="Graph"):


		# maybe use im.selectable?

		# sources

		labels = sorted([str((slot.node_id, slot.ix)) for slot in output_slots(graph)]) 
		prev_o_source = SELECTED_SLOTS_CONNECT['source']
		prev_o_source_txt = str((prev_o_source.node_id, prev_o_source.ix)) if prev_o_source != None else None

		changed, o_source_txt = str_combo_with_none("src##connect", prev_o_source_txt, labels)
		if changed:
			o_source = OutputSlotId(*eval(o_source_txt)) if o_source_txt != None else None
			SELECTED_SLOTS_CONNECT['source'] = o_source


		# dests

		labels = sorted([str((slot.node_id, slot.ix)) for slot in free_input_slots(graph)]) 
		prev_o_dest = SELECTED_SLOTS_CONNECT['dest']
		prev_o_dest_txt = str((prev_o_dest.node_id, prev_o_dest.ix)) if prev_o_dest != None else None

		changed, o_dest_txt = str_combo_with_none("dst##connect", prev_o_dest_txt, labels)
		if changed:
			o_dest = InputSlotId(*eval(o_dest_txt)) if o_dest_txt != None else None
			SELECTED_SLOTS_CONNECT['dest'] = o_dest

		# buttons
		conn = im.button("Connect")
		if conn and SELECTED_SLOTS_CONNECT['source'] != None and SELECTED_SLOTS_CONNECT['dest'] != None:
			emit(Connect(SELECTED_SLOTS_CONNECT['source'], SELECTED_SLOTS_CONNECT['dest']))
			SELECTED_SLOTS_CONNECT['source'] = None
			SELECTED_SLOTS_CONNECT['dest']   = None



		# -----------------------------


		# sources

		labels = sorted([str((slot.node_id, slot.ix)) for slot in used_output_slots(graph)]) 
		prev_o_source = SELECTED_SLOTS_DISCONNECT['source']
		prev_o_source_txt = str((prev_o_source.node_id, prev_o_source.ix)) if prev_o_source != None else None

		changed, o_source_txt = str_combo_with_none("src##disconnect", prev_o_source_txt, labels)
		if changed:
			o_source = OutputSlotId(*eval(o_source_txt)) if o_source_txt != None else None
			SELECTED_SLOTS_DISCONNECT['source'] = o_source


		# dests

		labels = sorted([str((slot.node_id, slot.ix)) for slot in filled_input_slots(graph)]) 
		prev_o_dest = SELECTED_SLOTS_DISCONNECT['dest']
		prev_o_dest_txt = str((prev_o_dest.node_id, prev_o_dest.ix)) if prev_o_dest != None else None

		changed, o_dest_txt = str_combo_with_none("dst##disconnect", prev_o_dest_txt, labels)
		if changed:
			o_dest = InputSlotId(*eval(o_dest_txt)) if o_dest_txt != None else None
			SELECTED_SLOTS_DISCONNECT['dest'] = o_dest

		conn = im.button("Disconnect")
		if conn and SELECTED_SLOTS_DISCONNECT['source'] != None and SELECTED_SLOTS_DISCONNECT['dest'] != None:
			emit(Disconnect(SELECTED_SLOTS_DISCONNECT['source'], SELECTED_SLOTS_DISCONNECT['dest']))
			SELECTED_SLOTS_DISCONNECT['source'] = None
			SELECTED_SLOTS_DISCONNECT['dest']   = None


		# ----------------------------------

		im.text(graph_repr(graph))


# repl
from sensa_util import chain as ch
pg = ch(graph_repr, print)