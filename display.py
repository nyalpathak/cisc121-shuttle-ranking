"""Draw one saved Merge Sort step in the Gradio window."""

from html import escape


TITLES = {
    "start": "Input order",
    "split": "Split the group",
    "single": "One stop is already sorted",
    "pick": "Compare the front stops",
    "tail": "Append the remaining stops",
    "done": "Final ranking",
}


def group(title, stops, tone, front=False, added=0):
    """Label the front candidate and any stops just added to the merged list."""
    cards = []
    for index, stop in enumerate(stops):
        marker = ""
        if front and index == 0:
            marker = "Front"
        elif index >= len(stops) - added:
            marker = "Added"

        tag = ""
        card_style = "stop " + tone
        if marker:
            tag = f"<small>{marker}</small>"
            card_style += " marked"
        # A name such as "Hall <A>" should appear exactly as the user typed it.
        name = escape(stop["name"])
        count = stop["count"]
        cards.append(f'<li class="{card_style}">{tag}<span>{name}</span><b>{count}</b></li>')

    if cards:
        content = '<ol class="cards">' + "".join(cards) + "</ol>"
    else:
        content = '<p class="empty-group">Empty group</p>'
    return f'<section class="group"><h3>{title}</h3>{content}</section>'


def ordered_rows(stops, final):
    """Print the names and counts in order. Scale result bars to the largest count."""
    rows = []
    for position, stop in enumerate(stops, start=1):
        name = escape(stop["name"])
        count = stop["count"]
        bar = ""
        if final:
            largest = stops[0]["count"]
            width = 0
            if largest > 0:
                width = 100 * count / largest
            bar = (f'<span class="track" aria-hidden="true">'
                   f'<span style="width:{width:.2f}%"></span></span>')
        rows.append(
            f'<li><span class="position">{position:02d}</span>'
            f'<span class="stop-name">{name}{bar}</span><b class="count">{count}</b></li>'
        )

    heading = "As entered"
    if final:
        heading = "Dispatch order"
    return (f'<div class="list-label"><span>{heading}</span><span>People waiting</span></div>'
            f'<ol class="stop-list">{"".join(rows)}</ol>')


def render_step(steps, index):
    step = steps[index]
    kind = step["kind"]
    if kind == "start" or kind == "done":
        visual = ordered_rows(step["output"], final=(kind == "done"))
    elif kind == "single":
        visual = group("Sorted group", step["output"], "output")
    else:
        comparing = kind == "pick"
        left = group("Left group", step["left"], "left", front=comparing)
        right = group("Right group", step["right"], "right", front=comparing)
        visual = f'<div class="halves">{left}{right}</div>'
        if kind == "pick" or kind == "tail":
            added = 1
            if kind == "tail":
                added = len(step["left"]) + len(step["right"])
            visual += group("Merged after this step", step["output"], "output", added=added)

    note_style = "step-note"
    if kind == "done":
        note_style = "decision"
    return (
        '<article class="board">'
        f'<div class="progress-label">Step {index + 1} of {len(steps)}</div>'
        f'<progress value="{index + 1}" max="{len(steps)}" aria-label="Simulation progress"></progress>'
        f'<h2>{TITLES[kind]}</h2><p class="{note_style}">{escape(step["note"])}</p>'
        f'{visual}</article>'
    )


def message(title, detail, error=False):
    role = "status"
    style = "board"
    if error:
        role = "alert"
        style = "board error"
    return f'<article class="{style}" role="{role}"><h2>{escape(title)}</h2><p>{escape(detail)}</p></article>'
