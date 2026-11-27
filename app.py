"""Gradio entry point for the campus shuttle Merge Sort simulator."""

from pathlib import Path

import gradio as gr

from display import message, render_step
from ranking import EXAMPLE, MAX_COUNT, MAX_STOPS, build_steps


def show(steps, index=0, notice=""):
    """Show one step and enable the buttons that can move away from it."""
    if steps:
        last = len(steps) - 1
        index = max(0, min(index, last))
        picture = render_step(steps, index)
        can_go_back = index > 0
        can_go_forward = index < last
    else:
        index = 0
        picture = notice or message("Ready for a new run", "Choose Start simulation to rank the edited stop counts.")
        can_go_back = False
        can_go_forward = False
    return (
        (steps, index), picture,
        gr.Button(interactive=can_go_back),
        gr.Button(interactive=can_go_forward),
        gr.Button(interactive=can_go_forward),
    )


def start(text):
    try:
        steps = build_steps(text)
    except ValueError as error:
        return show([], notice=message("Check your input", str(error), error=True))
    return show(steps)


def editing():
    # The textbox has changed. Its previous ranking no longer describes the input.
    return show([])


def previous_step(session):
    steps, index = session
    return show(steps, index - 1)


def next_step(session):
    steps, index = session
    return show(steps, index + 1)


def show_result(session):
    steps = session[0]
    return show(steps, len(steps) - 1)


def build_app():
    example_steps = build_steps(EXAMPLE)
    with gr.Blocks(title="Shuttle Stop Crowd Ranking", analytics_enabled=False) as app:
        # Gradio gives each browser session its own copy of the trace and cursor.
        session = gr.State((example_steps, 0))
        gr.HTML(
            '<header class="masthead"><h1>Shuttle stop crowd ranking</h1>'
            '<p>Use Merge Sort to decide where to send an extra campus shuttle.</p></header>'
        )
        with gr.Row(elem_id="workspace"):
            with gr.Column(scale=2, min_width=265, elem_id="controls"):
                entry = gr.Textbox(
                    value=EXAMPLE, label="Stop counts", lines=5, max_lines=14,
                    info=f"Enter 1–{MAX_STOPS} stops, one per line. Use a name, a comma, and a count from 0 to {MAX_COUNT}.",
                )
                start_button = gr.Button("Start simulation", variant="primary")
                gr.HTML('<p class="input-help">Use Next step to explore the sample, or edit the rows and choose Start simulation.</p>')
            with gr.Column(scale=4, min_width=310, elem_id="viewer"):
                picture = gr.HTML(render_step(example_steps, 0), elem_id="picture")
                with gr.Row(elem_id="navigation"):
                    back = gr.Button("Back", interactive=False, min_width=65)
                    forward = gr.Button("Next step", variant="primary", min_width=94)
                    finish = gr.Button("Show result", min_width=112)

        outputs = [session, picture, back, forward, finish]
        # Process input edits, restarts and navigation in the order they arrive.
        entry.change(editing, None, outputs, show_progress="hidden", concurrency_id="simulation")
        start_button.click(start, entry, outputs, show_progress="hidden", concurrency_id="simulation")
        back.click(previous_step, session, outputs, show_progress="hidden", concurrency_id="simulation")
        forward.click(next_step, session, outputs, show_progress="hidden", concurrency_id="simulation")
        finish.click(show_result, session, outputs, show_progress="hidden", concurrency_id="simulation")
    return app


if __name__ == "__main__":
    theme = gr.themes.Base(primary_hue="teal", neutral_hue="slate", font=["Inter", "system-ui", "sans-serif"])
    build_app().launch(theme=theme, css_paths=Path(__file__).with_name("style.css"), footer_links=[])
