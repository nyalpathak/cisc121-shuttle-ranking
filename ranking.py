"""Read crowd estimates and rank shuttle stops with Merge Sort."""

MAX_STOPS = 12
MAX_COUNT = 999
MAX_NAME = 40
MAX_TEXT = 2000

EXAMPLE = """Stauffer Library, 18
West Campus, 32
Athletics Centre, 32
Union Street, 7"""


def parse_stops(text):
    """Turn each nonblank 'name, count' line into a dictionary."""
    if text is None:
        text = ""
    if len(text) > MAX_TEXT:
        raise ValueError(f"Use at most {MAX_TEXT} characters for one run.")

    stops = []
    first_seen = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "":
            continue
        if len(stops) == MAX_STOPS:
            raise ValueError(f"Use up to {MAX_STOPS} stops. Remove the extra row on line {line_number}.")

        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(f"Line {line_number} needs one comma, for example Library, 18.")
        name = " ".join(parts[0].split())
        count_text = parts[1].strip()
        if name == "" or len(name) > MAX_NAME:
            raise ValueError(f"Line {line_number} needs a stop name of 1–{MAX_NAME} characters.")
        if not count_text.isascii() or not count_text.isdecimal():
            raise ValueError(f"Line {line_number} needs a whole number from 0 to {MAX_COUNT}.")
        count = int(count_text)
        if count > MAX_COUNT:
            raise ValueError(f"Line {line_number} exceeds {MAX_COUNT} people. Check the estimate.")

        # Keep the original line number so a duplicate can point to both estimates.
        key = name.casefold()
        previous_line = first_seen.get(key)
        if previous_line is not None:
            raise ValueError(
                f"Line {line_number} repeats the stop on line {previous_line}. Keep one estimate per stop."
            )
        first_seen[key] = line_number
        stops.append({"name": name, "count": count})

    if len(stops) == 0:
        raise ValueError("Enter at least one stop, for example Library, 18.")
    return stops


def explain_pick(chosen, other):
    if chosen["count"] == other["count"]:
        return (
            f"Both stops have {chosen['count']} waiting. Take {chosen['name']} from the left "
            "because it appeared earlier in the input."
        )
    return (
        f"{chosen['name']} has {chosen['count']} waiting and {other['name']} has "
        f"{other['count']}. Take {chosen['name']} next."
    )


def merge(left, right, steps):
    """Walk through two already-ranked halves, adding the busier front stop each time."""
    merged = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        # Save the two groups as they looked before this choice, for the Back button.
        left_before = left[left_index:]
        right_before = right[right_index:]
        left_stop = left[left_index]
        right_stop = right[right_index]

        # The left half came earlier in the input, so it wins equal counts.
        if left_stop["count"] >= right_stop["count"]:
            merged.append(left_stop)
            left_index += 1
            note = explain_pick(left_stop, right_stop)
        else:
            merged.append(right_stop)
            right_index += 1
            note = explain_pick(right_stop, left_stop)

        steps.append({
            "kind": "pick", "note": note,
            "left": left_before, "right": right_before, "output": merged.copy(),
        })

    # One half has run out. The other half is already in dispatch order.
    left_tail = left[left_index:]
    right_tail = right[right_index:]
    if left_tail:
        side = "left"
        merged.extend(left_tail)
    else:
        side = "right"
        merged.extend(right_tail)
    steps.append({
        "kind": "tail",
        "note": f"Only the {side} group has stops left. Append them in the order shown.",
        "left": left_tail, "right": right_tail, "output": merged.copy(),
    })
    return merged


def merge_sort(stops, steps):
    """Return stops from busiest to quietest and save each step for the screen."""
    if len(stops) <= 1:
        if stops:
            steps.append({
                "kind": "single", "note": "A group with one stop needs no comparisons.",
                "output": stops.copy(),
            })
        return stops.copy()

    middle = len(stops) // 2
    left_half = stops[:middle]
    right_half = stops[middle:]
    steps.append({
        "kind": "split", "note": "Divide this group at the middle. Work through the left half first.",
        "left": left_half, "right": right_half,
    })
    left = merge_sort(left_half, steps)
    right = merge_sort(right_half, steps)
    return merge(left, right, steps)


def dispatch_decision(ranked):
    name = ranked[0]["name"]
    count = ranked[0]["count"]
    if count == 0:
        return "Keep the extra shuttle on standby. Every stop reported zero people waiting."
    if len(ranked) > 1 and count == ranked[1]["count"]:
        return (
            f"Send the extra shuttle to {name}. The highest count is {count}. "
            "Of the stops tied for first, this one was entered earliest."
        )
    return f"Send the extra shuttle to {name}. Its count of {count} is the highest reported."


def build_steps(text):
    stops = parse_stops(text)
    steps = [{
        "kind": "start", "note": "Read the stops in the order entered. The numbers are people waiting.",
        "output": stops,
    }]
    ranked = merge_sort(stops, steps)
    steps.append({"kind": "done", "note": dispatch_decision(ranked), "output": ranked})
    return steps
