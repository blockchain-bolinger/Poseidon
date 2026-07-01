# Poseidon Testing Guide

## Recommended targets

- `main.py`: interaktiver TUI-Einstieg
- `cli.py`: headless CLI
- `web_ui.py`: FastAPI Web Remote Controller

## 1. Prepare environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Unit tests
```bash
pytest tests/ -q
python -m py_compile core/*.py services/*.py modules/*.py utils/*.py
```

## 3. Smoke targets
- `python main.py` starts TUI
- `python cli.py devices list` returns devices or empty list
- `python web_ui.py` starts FastAPI on loopback