import ollama

prompt_msg = [
    {"role": "user", "content": "What is the capital of India?"}
]

response = ollama.chat(model="llama3:latest", messages=prompt_msg)

# response = llm.invoke()

print("response: ", response)
print("response: ", response['message']['content'])