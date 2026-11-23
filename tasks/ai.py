from datetime import date, timedelta
import re

def parse_task_text(text, today):
    description = text
    due_date = None
    recurrence = None
    day_of_month = None

    text_lower = text.lower()

    # Detect tomorrow
    if "tomorrow" in text_lower:
        due_date = today + timedelta(days=1)

    # Detect today
    elif "today" in text_lower:
        due_date = today

    # Detect monthly recurrence
    if "every month" in text_lower:
        recurrence = "monthly"

    # Detect weekly recurrence
    elif "every week" in text_lower:
        recurrence = "weekly"

    # Detect daily recurrence
    elif "every day" in text_lower:
        recurrence = "daily"

    match = re.search(
        r"\b(\d{1,2})(st|nd|rd|th)\b",
        text_lower
    )

    if match:
        day_of_month = int(match.group(1))

    return {
        "title": extract_title(text),
        "description": description,
        "due_date": due_date,
        "recurrence": recurrence,
        "day_od_mont": day_of_month
    }

def extract_title(text):
    title = text.strip()

    prefixes = [
        "remind me to",
        "remember to",
        "remind me"
    ]

    for prefix in prefixes:
        if title.lower().startswith(prefix):
            title = title[len(prefix):]
            break

    title = re.sub(
        r"\s+on\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)(?:\s+of\s+every\s+month)?",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b(tomorrow|today|every month|every week|every day)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(r"\s+", " ", title).strip()

    if title:
        title = title[0].upper() + title[1:]

    return title.strip().capitalize()
