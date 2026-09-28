"""Gradio chat UI for the SQLite-backed Day 7 graph.

Run from the project root:
    uv run python .\\src\\agentic_ai\\day7\\example_chatbot_gradio_ui.py
"""

import inspect
import uuid

import gradio as gr

# Works when this file is run directly from its directory or by file path.
from example_chatbot_bknd_services import graph


CHATBOT_PARAMS = inspect.signature(gr.Chatbot.__init__).parameters
CHATBOT_SUPPORTS_MESSAGES = "type" in CHATBOT_PARAMS


def format_history_old(history: list[dict[str, str]]) -> list:
    """Format history for the Chatbot API in the installed Gradio version."""
    if CHATBOT_SUPPORTS_MESSAGES:
        return history

    # Older Gradio Chatbot versions expect (user, assistant) tuples.
    pairs = []
    pending_user = None

    for item in history:
        if item["role"] == "user":
            if pending_user is not None:
                pairs.append((pending_user, None))
            pending_user = item["content"]
        elif item["role"] == "assistant":
            pairs.append((pending_user, item["content"]))
            pending_user = None

    if pending_user is not None:
        pairs.append((pending_user, None))

    return pairs

def format_history(history: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return the messages format expected by the installed Gradio Chatbot."""
    return [
        {"role": item["role"], "content": str(item["content"])}
        for item in history
        if item.get("role") in {"user", "assistant"} and "content" in item
    ]


def get_thread_history(thread_id: str) -> list[dict[str, str]]:
    """Load persisted chat history for a thread."""
    thread_id = (thread_id or "").strip()
    if not thread_id:
        return []

    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("chat_history", [])

    return [
        {
            "role": item["role"],
            "content": str(item["content"]),
        }
        for item in messages
        if item.get("role") in {"user", "assistant"}
    ]


def load_thread(thread_id: str) -> tuple[list, str, bool]:
    """Load a thread when the user clicks the Load thread button."""
    thread_id = (thread_id or "").strip()

    if not thread_id:
        return [], "Enter a thread ID to load its conversation.", False

    try:
        history = get_thread_history(thread_id)
        status = (
            f"Loaded **{len(history)} messages** from thread `{thread_id}`."
            if history
            else f"Thread `{thread_id}` is ready. Send a message to begin."
        )
        return format_history(history), status, False
    except Exception as exc:
        return [], f"Could not load this thread: {exc}", False


def start_new_thread() -> tuple[str, list, str, bool]:
    """Create a new thread ID and clear the displayed conversation."""
    thread_id = uuid.uuid4().hex[:8]
    return thread_id, [], f"New thread `{thread_id}` is ready.", False


def respond(
    message: str,
    thread_id: str,
    stopped: bool,
) -> tuple[list, str, bool]:
    """Send a message to the graph and return the updated conversation."""
    message = (message or "").strip()
    thread_id = (thread_id or "").strip()

    if not thread_id:
        return [], "Enter a thread ID before sending a message.", stopped

    if not message:
        try:
            history = get_thread_history(thread_id)
            return format_history(history), "Type a message before sending.", stopped
        except Exception as exc:
            return [], f"Could not load this thread: {exc}", stopped

    if stopped:
        try:
            history = get_thread_history(thread_id)
        except Exception:
            history = []
        return (
            format_history(history),
            "This conversation has ended. Start a new thread to continue.",
            True,
        )

    # Like the original Streamlit UI, "bye" and "quit" end the UI session
    # without invoking the graph. The goodbye exchange is therefore not saved.
    if message.lower() in {"bye", "quit"}:
        try:
            history = get_thread_history(thread_id)
            history.extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "Goodbye!"},
                ]
            )
            return (
                format_history(history),
                "Conversation ended. Start a new thread to continue. "
                "This goodbye exchange is not saved to graph history.",
                True,
            )
        except Exception as exc:
            return [], f"Could not load this thread: {exc}", True

    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph.invoke({"user_message": message}, config=config)
        history = get_thread_history(thread_id)
        return (
            format_history(history),
            f"Reply received · thread `{thread_id}`",
            False,
        )
    except Exception as exc:
        try:
            history = get_thread_history(thread_id)
        except Exception:
            history = []

        return (
            format_history(history),
            f"Something went wrong: {exc}",
            False,
        )


CSS = """
.gradio-container {
    max-width: 1000px !important;
    margin: 0 auto !important;
}
#app-header {
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    border-radius: 18px;
    color: white;
    background: linear-gradient(120deg, #4338ca, #7c3aed);
}
#app-header h1 {
    margin: 0;
    font-size: 1.8rem;
}
#app-header p {
    margin: 0.45rem 0 0;
    opacity: 0.92;
}
#chat-panel {
    border-radius: 16px;
}
#status {
    min-height: 2.5rem;
}
"""


with gr.Blocks(title="Day 7 Chatbot") as demo:
    gr.HTML(
        """
        <div id="app-header">
            <h1>💬 Day 7 Chatbot</h1>
            <p>SQLite-backed conversation memory · Each thread keeps its own history</p>
        </div>
        """
    )

    with gr.Row():
        thread_id = gr.Textbox(
            label="Thread ID",
            value="student-1",
            placeholder="Enter an ID to load or continue a conversation",
            scale=4,
        )
        load_button = gr.Button("Load thread", variant="secondary", scale=1)
        new_button = gr.Button("＋ New thread", variant="primary", scale=1)

    chatbot_options = {
        "label": "Conversation",
        "height": 480,
        "elem_id": "chat-panel",
    }

    # Pass optional Chatbot arguments only when this Gradio version supports them.
    if "type" in CHATBOT_PARAMS:
        chatbot_options["type"] = "messages"
    if "show_copy_button" in CHATBOT_PARAMS:
        chatbot_options["show_copy_button"] = True
    if "placeholder" in CHATBOT_PARAMS:
        chatbot_options["placeholder"] = (
            "Your conversation will appear here. Send a message to get started."
        )

    chatbot = gr.Chatbot(**chatbot_options)

    status = gr.Markdown(
        "Enter a message below. Type **bye** or **quit** to end the conversation.",
        elem_id="status",
    )
    stopped = gr.State(False)

    with gr.Row():
        message = gr.Textbox(
            label="Message",
            placeholder="Ask a question…",
            lines=2,
            scale=6,
            show_label=False,
        )
        send_button = gr.Button("Send ➤", variant="primary", scale=1)

    gr.Markdown(
        "Tip: Use **Load thread** to open a previous conversation. "
        "Different thread IDs have separate histories."
    )

    load_button.click(
        fn=load_thread,
        inputs=thread_id,
        outputs=[chatbot, status, stopped],
    )

    new_button.click(
        fn=start_new_thread,
        outputs=[thread_id, chatbot, status, stopped],
    )

    submit_event = message.submit(
        fn=respond,
        inputs=[message, thread_id, stopped],
        outputs=[chatbot, status, stopped],
    )
    submit_event.then(fn=lambda: "", outputs=message)

    send_event = send_button.click(
        fn=respond,
        inputs=[message, thread_id, stopped],
        outputs=[chatbot, status, stopped],
    )
    send_event.then(fn=lambda: "", outputs=message)

    demo.load(
        fn=load_thread,
        inputs=thread_id,
        outputs=[chatbot, status, stopped],
    )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CSS)