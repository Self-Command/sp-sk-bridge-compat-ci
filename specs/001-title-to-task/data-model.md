# Data Model: Title-to-task

Source: [PRD](../../docs/product/title-task-prd.md); [contract](contracts/title-task.md).

| Entity | Fields | Validation / relationship |
| --- | --- | --- |
| Input title | title: string | Non-string inputs outside contract |
| Normalized title | text: string | str.strip() result must be non-empty; otherwise ValueError |
| Task | title: normalized string; completed: boolean False | Exactly these two keys; derived from normalized title |

Surrounding whitespace is removed; interior whitespace, case, accents, emoji, and remaining
characters are preserved without Unicode normalization. No IDs, stored records, relationships
beyond title-to-task derivation, or lifecycle transitions exist. Each valid call creates an
incomplete task; there is no completion/update feature.
