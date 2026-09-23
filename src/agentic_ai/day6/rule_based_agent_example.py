from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")


class PasswordAgent:
    """Simple agent pattern based on your example.

    The agent decides if the user wants a password-reset tool or a normal answer,
    then executes the appropriate action.
    """

    def decide_action(self, question: str) -> str:
        prompt = f"""You are a routing agent.
        Decide the next action for this request.
        Return only TOOL for password reset or password access questions.
        Return only ANSWER for all other questions.

        User question: {question}
        """

        response = llm.invoke(prompt)
        print(f"LLM response: {response}")
        action = response.content.strip().upper()
        print(f"action: {action}")
        
        if action not in ["TOOL", "ANSWER"]:
            action = "ANSWER"

        return action

    def run_tool(self) -> str:
        return "Tool executed: open password reset page."

    def run_answer(self) -> str:
        return "Direct answer: your request was received."

    def run(self, question: str):
        action = self.decide_action(question)

        if action == "TOOL":
            result = self.run_tool()
            return {
                "agent": "PasswordAgent",
                "question": question,
                "action": "TOOL",
                "result": result,
            }

        result = self.run_answer()
        return {
            "agent": "PasswordAgent",
            "question": question,
            "action": "ANSWER",
            "result": result,
        }


if __name__ == "__main__":
    agent = PasswordAgent()

    examples = [
        "Can I reset my password?",
        "What is the weather today?",
        "I forgot my login password",
    ]

    for question in examples:
        print(f"\nQuestion: {question}")
        print(agent.run(question))
