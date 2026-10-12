"""Create incomplete tasks from titles through the library or CLI."""

import argparse
import json
import sys


def normalize_title(title):
    """Trim surrounding whitespace and reject blank titles."""
    normalized = title.strip()
    if not normalized:
        raise ValueError("Title must not be blank")
    return normalized


def make_task(title):
    """Create an incomplete task with a normalized title."""
    return {"title": normalize_title(title), "completed": False}


def main():
    parser = argparse.ArgumentParser(description="Create an incomplete task")
    parser.add_argument("title")
    args = parser.parse_args(["--", *sys.argv[1:]])
    try:
        task = make_task(args.title)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(task))


if __name__ == "__main__":
    main()
