"""Turn a saved Merge Sort step into labelled HTML for Gradio."""

from html import escape

from ranking import Step, Stop


TITLES = {
    "start": "Input order",
    "split": "Split the group",
    "single": "One stop is already sorted",
    "pick": "Compare the front stops",
    "tail": "Append the remaining stops",
    "done": "Final ranking",
}


def group(title: str, stops: list[Stop], tone: str, front=False, added=0) -> str:
    """Draw one row of stop cards. A text label accompanies each highlight."""
    cards = []
    for index, stop in enumerate(stops):
        marker = ""
        if front and index == 0:
            marker = "Front"
        if index >= len(stops) - added:
            marker = "Added"
        tag = f'<small>{marker}</small>' if marker else ""
        marked = " marked" if marker else ""
        cards.append(
            f'<li class="stop {tone}{marked}">{tag}'
            f'<span>{escape(stop.name)}</span><b>{stop.count}</b></li>'
        )
    content = '<ol class="cards">' + "".join(cards) + '</ol>'
    if not stops:
        content = '<p class="empty-group">Empty group</p>'
    return f'<section class="group"><h3>{title}</h3>{content}</section>'


def ordered_rows(stops: list[Stop], final: bool) -> str:
    """Show positions and exact counts. Final bars use the busiest stop as their scale."""
    rows = []
    for position, stop in enumerate(stops, start=1):
        bar = ""
        if final:
            width = 100 * stop.count / stops[0].count if stops[0].count else 0
            bar = (f'<span class="track" aria-hidden="true">'
                   f'<span style="width:{width:.2f}%"></span></span>')
        rows.append(
            f'<li><span class="position">{position:02d}</span>'
            f'<span class="stop-name">{escape(stop.name)}{bar}</span>'
            f'<b class="count">{stop.count}</b></li>'
        )
    heading = "Dispatch order" if final else "As entered"
    return (f'<div class="list-label"><span>{heading}</span><span>People waiting</span></div>'
            f'<ol class="stop-list">{"".join(rows)}</ol>')


def render_step(steps: list[Step], index: int) -> str:
    step = steps[index]
    if step.kind == "start" or step.kind == "done":
        visual = ordered_rows(step.output, final=step.kind == "done")
    elif step.kind == "single":
        visual = group("Sorted group", step.output, "output")
    else:
        compare = step.kind == "pick"
        groups = (group("Left group", step.left, "left", front=compare)
                  + group("Right group", step.right, "right", front=compare))
        visual = f'<div class="halves">{groups}</div>'
        if step.kind != "split":
            added = 1 if compare else len(step.left) + len(step.right)
            visual += group("Merged after this step", step.output, "output", added=added)

    note_class = "decision" if step.kind == "done" else "step-note"
    return (
        '<article class="board">'
        f'<div class="progress-label">Step {index + 1} of {len(steps)}</div>'
        f'<progress value="{index + 1}" max="{len(steps)}" aria-label="Simulation progress"></progress>'
        f'<h2>{TITLES[step.kind]}</h2><p class="{note_class}">{escape(step.note)}</p>'
        f'{visual}</article>'
    )


def message(title: str, detail: str, error=False) -> str:
    role = "alert" if error else "status"
    style = " error" if error else ""
    return (f'<article class="board{style}" role="{role}">'
            f'<h2>{escape(title)}</h2><p>{escape(detail)}</p></article>')
