"""ChatGPT-style Gradio UI for the SQLite-backed Day 7 graph.

Run from the project root:
    uv run python .\\src\\agentic_ai\\day7\\example_chatbot_gradio_ui.py
"""

import uuid
from collections.abc import Mapping

import gradio as gr

# Works when this file is run directly from its directory or by file path.
# from example_chatbot_bknd_services import graph
from example_chatbot_bknd_services import (
    DEFAULT_MODEL,
    Ollama_model_list,
    graph,
)


def get_thread_history(thread_id: str) -> list[dict[str, str]]:
    """Load a thread's saved chat history from the graph."""
    thread_id = (thread_id or "").strip()
    if not thread_id:
        return []

    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    values = getattr(state, "values", {}) or {}
    messages = values.get("chat_history", []) or []

    return [
        {"role": item["role"], "content": str(item["content"])}
        for item in messages
        if isinstance(item, Mapping)
        and item.get("role") in {"user", "assistant"}
        and "content" in item
    ]


def get_thread_ids() -> list[str]:
    """List saved thread IDs using the graph's checkpointer."""
    checkpointer = getattr(graph, "checkpointer", None)
    list_checkpoints = getattr(checkpointer, "list", None)

    if not callable(list_checkpoints):
        return []

    try:
        checkpoints = list_checkpoints(None)
    except TypeError:
        checkpoints = list_checkpoints({})

    thread_ids = []
    seen = set()

    for checkpoint in checkpoints:
        config = getattr(checkpoint, "config", {}) or {}
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")

        if thread_id and thread_id not in seen:
            seen.add(thread_id)
            thread_ids.append(str(thread_id))

    return thread_ids


def get_thread_title(thread_id: str) -> str:
    """Create a readable sidebar label from the first user message."""
    try:
        history = get_thread_history(thread_id)
        first_user_message = next(
            (item["content"] for item in history if item["role"] == "user"),
            "",
        )
        title = " ".join(first_user_message.split())

        if title:
            if len(title) > 32:
                title = title[:29] + "..."
            return title

    except Exception:
        pass

    return f"Conversation {thread_id}"


def make_thread_choices(thread_ids: list[str]) -> list[tuple[str, str]]:
    """Build (visible label, thread ID) choices for the sidebar."""
    return [
        (get_thread_title(thread_id), thread_id)
        for thread_id in thread_ids
    ]


def load_thread(thread_id: str | None) -> tuple[list, str, bool]:
    """Load the selected conversation into the main chat window."""
    thread_id = (thread_id or "").strip()

    if not thread_id:
        return [], "Select a conversation or create a new one.", False

    try:
        history = get_thread_history(thread_id)
        if history:
            return history, f"Conversation loaded · `{thread_id}`", False
        return [], f"New conversation · `{thread_id}`", False
    except Exception as exc:
        return [], f"Could not load conversation: {exc}", False


def refresh_conversations(
    selected_thread_id: str | None,
) -> tuple[object, list, str, bool]:
    """Refresh the sidebar list and load the selected conversation."""
    try:
        thread_ids = get_thread_ids()
    except Exception as exc:
        return (
            gr.update(),
            [],
            f"Could not list saved conversations: {exc}",
            False,
        )

    selected_thread_id = (selected_thread_id or "").strip()

    if selected_thread_id and selected_thread_id not in thread_ids:
        thread_ids.insert(0, selected_thread_id)

    if not thread_ids:
        thread_ids = ["student-1"]

    choices = make_thread_choices(thread_ids)
    selected = (
        selected_thread_id
        if selected_thread_id in thread_ids
        else thread_ids[0]
    )

    history, status, stopped = load_thread(selected)
    return gr.update(choices=choices, value=selected), history, status, stopped


def start_new_thread() -> tuple[object, list, str, bool]:
    """Create and select a fresh conversation."""
    thread_id = uuid.uuid4().hex[:8]

    try:
        thread_ids = get_thread_ids()
    except Exception:
        thread_ids = []

    if thread_id not in thread_ids:
        thread_ids.insert(0, thread_id)

    choices = make_thread_choices(thread_ids)
    return (
        gr.update(choices=choices, value=thread_id),
        [],
        f"New conversation · `{thread_id}`. Send a message to begin.",
        False,
    )


def respond_old(
    message: str,
    thread_id: str | None,
    selected_model: str,
    stopped: bool,
) -> tuple[list, str, bool, object]:
    """Send the user's message to the graph and refresh the sidebar."""
    message = (message or "").strip()
    thread_id = (thread_id or "").strip()

    if not thread_id:
        thread_id = uuid.uuid4().hex[:8]

    if not message:
        history, status, stopped = load_thread(thread_id)
        return history, "Type a message before sending.", stopped, gr.update()

    if stopped:
        history, _, _ = load_thread(thread_id)
        return (
            history,
            "This conversation has ended. Select or create a conversation to continue.",
            True,
            gr.update(),
        )

    # End the UI conversation without sending "bye" or "quit" to the graph.
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
                history,
                "Conversation ended. Create or select a conversation to continue.",
                True,
                gr.update(),
            )
        except Exception as exc:
            return [], f"Could not load conversation: {exc}", True, gr.update()

    try:
        # config = {"configurable": {"thread_id": thread_id}}
        config = {
            "configurable": {
                "thread_id": thread_id,
                "model": selected_model,
            }
        }
        # graph.invoke({"user_message": message}, config=config)
        graph.invoke({"user_message": message}, config=config)

        history = get_thread_history(thread_id)

        thread_ids = get_thread_ids()
        if thread_id not in thread_ids:
            thread_ids.insert(0, thread_id)

        return (
            history,
            f"Reply received · `{thread_id}`",
            False,
            gr.update(
                choices=make_thread_choices(thread_ids),
                value=thread_id,
            ),
        )
    except Exception as exc:
        try:
            history = get_thread_history(thread_id)
        except Exception:
            history = []

        return history, f"Something went wrong: {exc}", False, gr.update()


def respond(
    message: str,
    thread_id: str | None,
    selected_model: str,
    stopped: bool,
):
    """Show the submitted message immediately, then run the graph."""
    message = (message or "").strip()
    thread_id = (thread_id or "").strip() or uuid.uuid4().hex[:8]
    selected_model = selected_model or DEFAULT_MODEL

    try:
        history = get_thread_history(thread_id)
    except Exception:
        history = []

    thread_ids = get_thread_ids()
    if thread_id not in thread_ids:
        thread_ids.insert(0, thread_id)

    thread_update = gr.update(
        choices=make_thread_choices(thread_ids),
        value=thread_id,
    )

    if not message:
        yield history, "Type a message before sending.", stopped, thread_update, ""
        return

    if stopped:
        yield (
            history,
            "This conversation has ended. Select or create a conversation to continue.",
            True,
            thread_update,
            "",
        )
        return

    if message.lower() in {"bye", "quit"}:
        history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "Goodbye!"},
            ]
        )
        yield (
            history,
            "Conversation ended. Create or select a conversation to continue.",
            True,
            thread_update,
            "",
        )
        return

    # Optimistically show the user's message and clear the textbox immediately.
    visible_history = history + [{"role": "user", "content": message}]
    yield visible_history, "Thinking…", False, thread_update, ""

    try:
        config = {
            "configurable": {
                "thread_id": thread_id,
                "model": selected_model,
            }
        }
        graph.invoke({"user_message": message}, config=config)

        final_history = get_thread_history(thread_id)
        yield (
            final_history,
            f"Reply received · `{thread_id}`",
            False,
            thread_update,
            "",
        )
    except Exception as exc:
        yield (
            visible_history,
            f"Something went wrong: {exc}",
            False,
            thread_update,
            "",
        )

CSS = """
html,
body,
#root {
    height: 100%;
    margin: 0;
    overflow: hidden !important;
}

.gradio-container {
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 100% !important;
    height: 100vh !important;
    height: 100dvh !important;
    overflow: hidden !important;
}

#app-header {
    padding: 1rem 1.4rem;
    margin-bottom: 0.8rem;
    border-radius: 16px;
    color: white;
    background: linear-gradient(120deg, #4338ca, #7c3aed);
}

#app-header h1 {
    margin: 0;
    font-size: 1.6rem;
}

#app-header p {
    margin: 0.35rem 0 0;
    opacity: 0.92;
}

#sidebar {
    min-width: 220px;
}

#conversation-list {
    min-height: 0;
}

/* Leaves room for the header, model selector, composer, and status. */
#chat-panel {
    height: clamp(180px, calc(100dvh - 520px), 560px) !important;
    min-height: 180px !important;
    max-height: calc(100dvh - 520px) !important;
    overflow-y: auto !important;
}

#status {
    min-height: 2rem;
}

/* On narrow screens, allow normal page scrolling instead of clipping controls. */
@media (max-width: 760px) {
    html,
    body,
    #root,
    .gradio-container {
        height: auto !important;
        min-height: 100vh !important;
        overflow: auto !important;
    }

    #chat-panel {
        height: 55vh !important;
        min-height: 220px !important;
        max-height: 55vh !important;
    }
}
"""

try:
    INITIAL_THREAD_IDS = get_thread_ids()
except Exception:
    INITIAL_THREAD_IDS = []

if not INITIAL_THREAD_IDS:
    INITIAL_THREAD_IDS = ["student-1"]

INITIAL_CHOICES = make_thread_choices(INITIAL_THREAD_IDS)
INITIAL_THREAD_ID = INITIAL_THREAD_IDS[0]

with gr.Blocks(title="Day 7 Chatbot") as demo:
    gr.HTML(
        """
        <div id="app-header">
            <h1>💬 Day 7 Chatbot</h1>
            <p>SQLite-backed memory · Select a conversation or start a new one</p>
        </div>
        """
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, min_width=240, elem_id="sidebar"):
            gr.Markdown("### Conversations")
            model_select = gr.Dropdown(
                label="Model",
                choices=Ollama_model_list,
                value=DEFAULT_MODEL,
                interactive=True,
            )
            new_button = gr.Button("＋ New conversation", variant="primary")
            refresh_button = gr.Button("↻ Refresh conversations")
            thread_select = gr.Dropdown(
                label="Chat history",
                choices=INITIAL_CHOICES,
                value=INITIAL_THREAD_ID,
                interactive=True,
                elem_id="conversation-list",
            )
            gr.Markdown(
                "Choose a conversation to continue it. "
                "Each conversation has separate saved history."
            )

        with gr.Column(scale=4):
            
            chatbot_options = {
                "label": "Conversation",
                "height": 560,
                "elem_id": "chat-panel",
            }

            # Keep this compatibility check for your installed Gradio version.
            chatbot_parameters = getattr(
                gr.Chatbot.__init__,
                "__signature__",
                None,
            )
            if chatbot_parameters:
                supported_parameters = chatbot_parameters.parameters
                if "show_copy_button" in supported_parameters:
                    chatbot_options["show_copy_button"] = True
                if "placeholder" in supported_parameters:
                    chatbot_options["placeholder"] = (
                        "Your conversation will appear here. Send a message to begin."
                    )

            chatbot = gr.Chatbot(**chatbot_options)

            status = gr.Markdown(
                "Select a conversation or send a message to begin.",
                elem_id="status",
            )
            stopped = gr.State(False)

            with gr.Row():
                message = gr.Textbox(
                    placeholder="Message the chatbot…",
                    lines=1,
                    show_label=False,
                    scale=6,
                )
                send_button = gr.Button("➤", variant="primary", scale=1)

            # gr.Markdown("Type **bye** or **quit** to end the current conversation.")

    thread_select.change(
        fn=load_thread,
        inputs=thread_select,
        outputs=[chatbot, status, stopped],
    )

    # model_select = gr.Dropdown(
    #     label="Model",
    #     choices=Ollama_model_list,
    #     value=DEFAULT_MODEL,
    #     interactive=True,
    # )
    

    refresh_button.click(
        fn=refresh_conversations,
        inputs=thread_select,
        outputs=[thread_select, chatbot, status, stopped],
    )

    new_button.click(
        fn=start_new_thread,
        outputs=[thread_select, chatbot, status, stopped],
    )

    submit_event = message.submit(
        fn=respond,
        inputs=[message, thread_select, model_select, stopped],
        outputs=[chatbot, status, stopped, thread_select, message],
    )
    submit_event.then(fn=lambda: "", outputs=message)

    send_event = send_button.click(
        fn=respond,
        inputs=[message, thread_select, model_select, stopped],
        outputs=[chatbot, status, stopped, thread_select, message],
    )
    send_event.then(fn=lambda: "", outputs=message)

    demo.load(
        fn=load_thread,
        inputs=thread_select,
        outputs=[chatbot, status, stopped],
    )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CSS)
    # demo.launch(theme=gr.themes.Soft(), css=CSS, show_api=True)