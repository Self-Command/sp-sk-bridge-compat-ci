import argparse
import json
import sys


def normalize_title(title):
    normalized = title.strip()
    if not normalized:
        raise ValueError("title must not be empty")
    return normalized


def make_task(title):
    return {"title": normalize_title(title), "completed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    args = parser.parse_args(["--", *sys.argv[1:]])
    try:
        task = make_task(args.title)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(task))


if __name__ == "__main__":
    main()
