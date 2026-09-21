from langgraph.graph import START, END, StateGraph
from typing import TypedDict

class MyState(TypedDict):
    a: int
    b: int
    c: int

def node1_process(state: MyState):
    state['a'] = 10
    state['b'] = 20

    return state

def node2_calculate(state: MyState):
    state['c'] = state['a'] + state['b']
    return state

graph = StateGraph(MyState)

graph.add_node('node1', node1_process)
graph.add_node('node2', node2_calculate)

graph.add_edge(START, 'node1')
graph.add_edge('node1', 'node2')
graph.add_edge('node2', END)

workflow_state = graph.compile()

# print(workflow_state)  # This will display the graph structure

# This will display the graph structure
# workflow_state.visualize()

result = workflow_state.invoke({'a': 0, 'b': 0, 'c': 0})

print(result)  # Output: {'a': 10, 'b': 20, 'c': 30}