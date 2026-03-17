# Configuration Notes

This project uses a **single shared configuration** in repo root:

- `config.py`
- `config_private.py`

## What To Edit

- Edit only root config files:
  - `config.py`
  - `config_private.py`

## How to run scripts

Run scripts as modules from repo root so imports resolve correctly:
- `python -m examples.example01`
- `python -m connectors.list_connectors`
