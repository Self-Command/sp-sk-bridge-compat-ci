"""Public, fixed product contracts; no application implementation is supplied."""
from pathlib import Path
import json

PRODUCT = '''Build a tiny Python 3.13 standard-library CLI task manager. Interface:
python -m task_app --store PATH add TITLE
python -m task_app --store PATH list
python -m task_app --store PATH complete ID
python -m task_app --store PATH delete ID
Successful commands exit 0 and print JSON. Add and complete print the affected task
object with integer positive id, string title, boolean completed. List prints a JSON
array in insertion order. Delete prints JSON of your choice. IDs increase and are
not reused after deletion. No concurrency or network. The stored JSON object has
version: 1 and tasks: an array; additional metadata is allowed for monotonic IDs.
Trim title whitespace and accept 1 through 100 Unicode code points. Empty,
whitespace-only and 101-code-point titles exit 2 without changing the store.
Missing complete/delete IDs exit 2 without changing the store. Complete is
idempotent. Data survives separate CLI processes. A missing store lists as empty.
Malformed JSON, unsupported store version and malformed task records must cause
every command to exit 2 without overwriting the original bytes. Errors go to
stderr. User has approved the entire scope. No further product ambiguity remains.
Keep the implementation small (one package and pytest tests). Core logic uses TDD.
No login, UI, service, install-time network dependency or external data upload.
'''

CONSTITUTION = '''# Compatibility fixture constitution
Canonical spec, plan and tasks are binding. Preserve product requirements during
implementation. Use Python 3.13, the standard library and pytest. Business behavior
uses TDD with observed failing and passing tests. Commit each completed task.
Do not overwrite corrupt data. Do not merge, push, publish or discard work.
Finish by keeping the feature branch. A requirements conflict must return to the
design owner through the bridge blocked state. Requirement docs are not editable
while the bridge is executing. Only task completion checkboxes may change.
'''

MAIN_TASKS = [
    'Implement JSON repository and data validation in task_app/store.py with tests/test_store.py. Preserve corrupt bytes, reject unsupported versions and malformed task records. Use monotonically increasing positive integer IDs. Run python -m pytest tests/test_store.py; commit only after tests pass.',
    'Implement task creation, listing, completion and deletion business rules in task_app/core.py with tests/test_core.py. Trim 1–100 Unicode-code-point titles, reject missing IDs, preserve list order, complete idempotently. Run python -m pytest tests/test_store.py tests/test_core.py; commit after passing.',
    'Implement argparse JSON CLI in task_app/__main__.py, package initializer task_app/__init__.py and tests/test_cli.py. Meet every documented interface, process persistence and error-exit rule. Run python -m pytest; commit after passing.',
]


def write(path, text):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def create(root, kind='main'):
    root=Path(root)
    feature='specs/001-'+kind
    write(root/'.specify/memory/constitution.md', CONSTITUTION)
    write(root/'.specify/feature.json', json.dumps({'feature_directory':feature})+'\n')
    if kind == 'main':
        spec='# CLI task manager specification\n\n'+PRODUCT
        plan='''# Implementation plan
Python 3.13 standard library, pytest; no external runtime packages. Module package
task_app with store.py, core.py and __main__.py. All product interface and error
rules are in spec.md and binding. TDD per behavior, commit per task, whole-suite
verification and fresh-context branch review. Storage failures never silently
destroy the original. Use a feature branch; finish by keeping it.
'''
        entries=MAIN_TASKS
    elif kind == 'smoke':
        write(root/'.specify/memory/constitution.md',CONSTITUTION.replace('and pytest','and unittest').replace('Do not overwrite corrupt data. ',''))
        spec='# Tiny calculator\ncalculator.add(a, b) accepts integers and returns their sum. Check (2,3)->5, (-2,2)->0 and (0,0)->0. No CLI, persistence or other feature.\n'
        plan='# Calculator plan\nOne calculator.py module and one unittest test file, using only the Python standard library. TDD, verify, commit, review, keep branch.\n'
        entries=['Implement calculator.add(a, b) in calculator.py with exactly three unittest cases in tests/test_calculator.py: (2,3) gives 5, (-2,2) gives 0, (0,0) gives 0. Write and run the failing tests first, then implement. Verify with python -m unittest discover -s tests -v and commit after passing.']
    elif kind == 'resume':
        spec='''# Resume product
resume_app.normalize_title(title) strips surrounding whitespace and raises
ValueError for empty input. resume_app.make_task(title) returns exactly
{"title": normalized_title, "completed": false}. Running python resume_app.py TITLE
prints that object as JSON and exits 0. Empty input exits 2. Use pytest and TDD.
'''
        plan='# Resume plan\nSingle resume_app.py module, three ordered tasks with independent acceptance tests. Each task commits and verifies; tasks must not be repeated or skipped on resume.\n'
        entries=[
            'Implement normalize_title(title) in resume_app.py and tests/test_normalize.py. Trim and reject empty titles. Run python -m pytest tests/test_normalize.py; commit after passing.',
            'Add make_task(title) in resume_app.py and tests/test_make_task.py. Return exactly the normalized title and completed False. Run python -m pytest; commit after passing.',
            'Add JSON command line interface to resume_app.py and tests/test_resume_cli.py. python resume_app.py TITLE prints the make_task result, empty exits 2. Run python -m pytest; commit after passing.',
        ]
    else:
        spec='# Marker specification\nmarker.answer() must return the integer 42. python marker.py must print 42. Test with pytest.\n'
        plan='# Marker plan\nImplement marker.py and tests/test_marker.py, using TDD and a commit after verification.\n'
        value=99 if kind == 'conflict' else 42
        entries=[f'Implement marker.answer() returning exactly {value}, and python marker.py printing {value}, in marker.py. Write tests/test_marker.py first and observe failure, then implementation. Run python -m pytest; commit after passing.']
        if kind == 'conflict':
            plan += 'Task acceptance requires the value 99, which conflicts directly with spec.md requiring 42. No authority to change spec.md has been supplied.\n'
    write(root/feature/'spec.md', spec)
    write(root/feature/'plan.md', plan)
    task_text='# Tasks\n\nSpec: spec.md. Plan: plan.md. Constitution: .specify/memory/constitution.md.\n\n'
    task_text+='\n'.join(f'- [ ] T{i:03d} {entry}' for i,entry in enumerate(entries,1))+'\n'
    write(root/feature/'tasks.md',task_text)
    return feature
