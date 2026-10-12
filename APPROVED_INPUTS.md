Build a tiny Python 3.13 standard-library title-to-task JSON tool.
Library in resume_app.py:
normalize_title(title) strips surrounding whitespace and raises ValueError for
empty or whitespace-only strings. Non-empty Unicode titles are accepted.
make_task(title) returns exactly {"title": normalized_title, "completed": false}.
CLI: python resume_app.py TITLE prints that task as JSON and exits 0.
Empty/whitespace-only TITLE or a missing TITLE exits 2. No UI, database,
network, installation, persistence, additional features or runtime dependencies.
Use standard-library unittest and observed TDD. Exactly three ordered cohesive
implementation tasks: T001 normalize_title and its tests, T002 make_task and its
tests depending on T001, T003 the CLI and its tests depending on T001/T002.
Commit each task with its canonical checkbox and actual execution evidence.
The design, these requirements, and all testing answers are authorized by the
user's full compatibility-test plan. Keep documents concise.
