from langchain_ollama import ChatOllama

# llm = ChatOllama(model="ollama3:latest")#, base_url="http://localhost:11434")
# llm = ChatOllama(model="llama3:latest")

# llm = ChatOllama(model="gpt-oss:120b-cloud")#, base_url="http://localhost:11434")

llm = ChatOllama(
    model="gpt-oss:120b-cloud"
)

response = llm.invoke("What is the capital of France?")

print(response)

print("Response content:", response.content)