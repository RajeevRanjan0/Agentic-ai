from langgraph.graph import START, END, StateGraph

def clean_text(state):
    state['cleaned_text'] = state['raw_text'].strip().lower()
    return state

def count_words(state):
    state['word_split'] = state['cleaned_text'].split()
    state['word_count'] = len(state['word_split'])
    return state

def create_message(state):
    state['message'] = f"Your requirements has {state['word_count']} words."
    return state

graph = StateGraph(dict)
graph.add_node('clean_text', clean_text)
graph.add_node('count_words', count_words)
graph.add_node('create_message', create_message)

graph.add_edge(START, 'clean_text')
graph.add_edge('clean_text', 'count_words')
graph.add_edge('count_words', 'create_message')
graph.add_edge('create_message', END)

workflow_state = graph.compile()

print(workflow_state.get_graph().draw_mermaid())
# result = workflow_state.invoke({'raw_text': '   This is a sample text for testing.   '})
# print(result)  # Output: {'raw_text': '   This is a sample text for testing.   ', 'cleaned_text': 'this is a sample text for testing.', 'word_count': 7, 'message': 'Your requirements has 7 words.'}

png_data = workflow_state.get_graph().draw_mermaid_png()

with open("workflow_graph.png", "wb") as file:
    file.write(png_data)

# given requirements, to test and predict the output of the code.
result = workflow_state.invoke({'raw_text': """  i am checking the word count as per assignments. \n so let's run the example.py file and check the output. \n also predict the outcome of the code.  """})
print(result) # ideally 26 count should be the output.

# command prompt execution result:
r'''
(agentic-ai) PS C:\Users\rs108107\Desktop\Agentic-ai\src\agentic_ai> python -m uv run .\day3\example.py
{'raw_text': "  i am checking the word count as per assignments. \n so let's run the example.py file and check the output. \n also predict the outcome of the code.  ", 'cleaned_text': "i am checking the word count as per assignments. \n solet's run the example.py file and check the output. \n also predict the outcomeof the code.", 'word_split': ['i', 'am', 'checking', 'the', 'word', 'count', 'as', 'per', 'assignments.', 'so', "let's", 'run', 'the', 'example.py', 'file', 'and', 'check', 'the', 'output.', 'also', 'predict', 'the', 'outcome', 'of', 'the', 'code.'], 'word_count': 26, 'message': 'Your requirements has 26 words.'}
(agentic-ai) PS C:\Users\rs108107\Desktop\Agentic-ai\src\agentic_ai> 
'''