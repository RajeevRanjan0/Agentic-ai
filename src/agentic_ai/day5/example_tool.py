from langgraph.graph import START, END, StateGraph
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv

from utility_file import calculate_price, display_total_price

load_dotenv()

class State(TypedDict):
    price: float
    quantity: int
    total: float
    answer: str

def calculate_total(price: float, quantity: int) -> float:
    return price * quantity

def use_tool(state: State):
    price = state['price']
    quantity = state['quantity']
    # total = calculate_total(price, quantity)
    total = calculate_price(quantity, price)
    state['total'] = total

    return state

def create_answer(state: State):
    state['answer'] = f"The total cost for {state['quantity']} items at ${state['price']} each is ${state['total']}."
    return state

graph = StateGraph(State)
graph.add_node('use_tool', use_tool)
graph.add_node('create_answer', create_answer)

graph.add_edge(START, 'use_tool')
graph.add_edge('use_tool', 'create_answer')
graph.add_edge('create_answer', END)

workflow_state = graph.compile()

result = workflow_state.invoke({'price': 20.0, 'quantity': 15})
print(result)  # Output: {'price': 20.0, 'quantity': 15, 'total': 300.0, 'answer': 'The total cost for 15 items at $20.0 each is $300.0.'}
print(result['answer'])  # Output: The total cost for 15 items at $20.0 each is $300.0.