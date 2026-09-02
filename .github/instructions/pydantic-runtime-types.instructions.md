---
name: Pydantic Runtime Types
description: "Use when editing Python Pydantic models, postponed annotations, validators, or schema serialization. Prevents unresolved runtime model types and requires focused diagnostics after changes."
applyTo: "libs/core/**/*.py"
---
# Pydantic Runtime Types

- Keep every type used by a Pydantic field available at runtime. Do not move model imports into `TYPE_CHECKING` when Pydantic must resolve them to build or validate a schema.
- If postponed annotations are enabled, verify that the model can be instantiated and deserialized at runtime; editor or mypy success alone is insufficient.
- When Pylance reports a condition is always true or false, inspect the preceding narrowing and remove only the redundant condition. Preserve checks that protect runtime values from `None`.
- After changing a Pydantic model, run focused Pylance diagnostics and the nearest model tests before broader checks.
