import re


def break_down_task(task):

    description = task.description

    parts = re.split(
        r",|\band\b",
        description,
        flags=re.IGNORECASE
    )

    subtasks = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        subtasks.append({
            "title": part,
            "description": part,
            "priority": task.priority,
            "completed": False
        })

    return subtasks