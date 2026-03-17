# Configuration Notes

This project currently uses configuration files in **3 locations**:

1. Root (shared source of truth):
   - `config.py`
   - `config_private.py`
2. `examples/` compatibility wrappers:
   - `examples/config.py`
   - `examples/config_private.py`
3. `connectors/` compatibility wrapper:
   - `connectors/config_private.py`

## What To Edit

- For normal usage, edit only the **root files**:
  - `config.py`
  - `config_private.py`
- The files under `examples/` and `connectors/` are wrappers that load values from root.

## When You Might Touch All 3 Locations

You may need to update all 3 locations only if you change structure, for example:
- renaming config variables,
- changing module/file names,
- changing import strategy.

In those cases, keep wrappers aligned with the root schema so scripts keep working when launched as:
- `python examples/...`
- `python connectors/...`
