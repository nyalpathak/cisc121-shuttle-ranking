"""Input rules, stable Merge Sort, and the campus shuttle decision."""

from dataclasses import dataclass, field


MAX_STOPS = 12
MAX_COUNT = 999
MAX_NAME = 40
MAX_TEXT = 2000

EXAMPLE = """Stauffer Library, 18
West Campus, 32
Athletics Centre, 32
Union Street, 7"""


@dataclass(frozen=True)
class Stop:
    name: str
    count: int


@dataclass
class Step:
    """A snapshot of one operation. Rows are shown in their list order."""

    kind: str
    note: str
    left: list[Stop] = field(default_factory=list)
    right: list[Stop] = field(default_factory=list)
    output: list[Stop] = field(default_factory=list)


def parse_stops(text: str | None) -> list[Stop]:
    """Read one 'stop name, count' per line and report the first bad row."""
    text = text or ""
    if len(text) > MAX_TEXT:
        raise ValueError(f"Use at most {MAX_TEXT} characters for one run.")

    stops = []
    first_seen = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(stops) == MAX_STOPS:
            raise ValueError(f"Use up to {MAX_STOPS} stops. Remove the extra row on line {line_number}.")

        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(f"Line {line_number} needs one comma, for example Library, 18.")
        name = " ".join(parts[0].split())
        count_text = parts[1].strip()
        if not name or len(name) > MAX_NAME:
            raise ValueError(f"Line {line_number} needs a stop name of 1–{MAX_NAME} characters.")
        if not count_text.isascii() or not count_text.isdecimal():
            raise ValueError(f"Line {line_number} needs a whole number from 0 to {MAX_COUNT}.")
        count = int(count_text)
        if count > MAX_COUNT:
            raise ValueError(f"Line {line_number} exceeds {MAX_COUNT} people. Check the estimate.")

        # A second estimate for the same stop would give it two places in the ranking.
        key = name.casefold()
        previous_line = first_seen.get(key)
        if previous_line is not None:
            raise ValueError(f"Line {line_number} repeats the stop on line {previous_line}. Keep one estimate per stop.")
        first_seen[key] = line_number
        stops.append(Stop(name, count))

    if not stops:
        raise ValueError("Enter at least one stop, for example Library, 18.")
    return stops


def merge(left: list[Stop], right: list[Stop], steps: list[Step]) -> list[Stop]:
    """Combine two ranked groups, recording each choice for the viewer."""
    merged = []
    left_index = right_index = 0
    while left_index < len(left) and right_index < len(right):
        left_stop, right_stop = left[left_index], right[right_index]
        # Save the groups before advancing a pointer so both candidates stay visible.
        left_before = left[left_index:]
        right_before = right[right_index:]
        # Choosing left on a tie keeps earlier input rows ahead of later ones.
        if left_stop.count >= right_stop.count:
            chosen, other = left_stop, right_stop
            left_index += 1
        else:
            chosen, other = right_stop, left_stop
            right_index += 1
        merged.append(chosen)

        if left_stop.count == right_stop.count:
            note = (f"Both stops have {left_stop.count} waiting. Take {chosen.name} from the left "
                    "because it appeared earlier in the input.")
        else:
            note = (f"{chosen.name} has {chosen.count} waiting and {other.name} has "
                    f"{other.count}. Take {chosen.name} next.")
        # Later appends must not change a step that the user can revisit.
        steps.append(Step("pick", note, left_before, right_before, merged.copy()))

    # At most one group has any stops left. Its tail is already in order.
    left_tail, right_tail = left[left_index:], right[right_index:]
    merged.extend(left_tail)
    merged.extend(right_tail)
    side = "left" if left_tail else "right"
    note = f"Only the {side} group has stops left. Append them in the order shown."
    steps.append(Step("tail", note, left_tail, right_tail, merged.copy()))
    return merged


def merge_sort(stops: list[Stop], steps: list[Step]) -> list[Stop]:
    """Return a new list ordered by descending crowd count."""
    if len(stops) <= 1:
        if stops:
            steps.append(Step("single", "A group with one stop needs no comparisons.", output=stops.copy()))
        return stops.copy()

    middle = len(stops) // 2
    left_half = stops[:middle]
    right_half = stops[middle:]
    steps.append(Step("split", "Divide this group at the middle. Work through the left half first.",
                      left=left_half, right=right_half))
    left = merge_sort(left_half, steps)
    right = merge_sort(right_half, steps)
    return merge(left, right, steps)


def dispatch_decision(ranked: list[Stop]) -> str:
    """Explain the decision using the completed, nonempty ranking."""
    first = ranked[0]
    if first.count == 0:
        return "Keep the extra shuttle on standby. Every stop reported zero people waiting."
    if len(ranked) > 1 and first.count == ranked[1].count:
        return (f"Send the extra shuttle to {first.name}. The highest count is {first.count}. "
                "Of the stops tied for first, this one was entered earliest.")
    return f"Send the extra shuttle to {first.name}. Its count of {first.count} is the highest reported."


def build_steps(text: str) -> list[Step]:
    stops = parse_stops(text)
    steps = [Step("start", "Read the stops in the order entered. The numbers are people waiting.",
                  output=stops)]
    ranked = merge_sort(stops, steps)
    steps.append(Step("done", dispatch_decision(ranked), output=ranked))
    return steps
