# Testing

## Prerequisites

Install dev dependencies from repo root:

```bash
pip install -r requirements-dev.txt
```

## Run all tests

```bash
python -m pytest
```

## Run specific test files

```bash
python -m pytest tests/test_utils.py
python -m pytest tests/test_retrieval.py
```

## Coverage

Example coverage command used in this repo:

```bash
python -m pytest \
  --cov=common \
  --cov=examples.list_all_files \
  --cov=examples.list_all_vector_stores \
  --cov=examples.delete_all_files \
  --cov=examples.delete_all_vs \
  --cov-report=term-missing
```

## Test layout

- `tests/conftest.py`: shared fixtures and SDK stubs.
- `tests/fakes.py`: fake helpers for pagination/delete flows.
- `tests/test_utils.py`: utility tests for `common` helpers.
- `tests/test_retrieval.py`: tests for retrieval reference extraction.
- `tests/test_files_scripts.py`: utility scripts for files.
- `tests/test_vector_store_scripts.py`: utility scripts for vector stores.
- `tests/test_connectors_common.py`: connector-related common utilities.
- `tests/test_additional_coverage.py`: extra branch/regression coverage.

`pytest.ini` contains base pytest configuration.

## Quality checks

The repository includes `run_quality.sh` to run formatting/lint checks:

```bash
./run_quality.sh
```

It runs `black` and `pylint` across Python files.
