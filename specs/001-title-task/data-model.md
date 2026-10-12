# Data Model

Source: [PRD](../../docs/product/title-task-prd.md).

| Entity | Fields | Validation / relationship |
| --- | --- | --- |
| Input title | string | Supported library inputs are strings; CLI supplies one title argument |
| Normalized title | non-empty string | Input stripped with str.strip(); preserve internal whitespace and Unicode |
| Task | title: normalized string; completed: boolean false | Exactly these two fields; constructed from the normalized title |

Blank normalized titles raise ValueError in both library surfaces. CLI translates
blank input to exit 2. Missing CLI input exits 2 before task creation. A valid task
is returned or serialized once; no identity, persistence, updates, completion
transition, or external relationships exist.
