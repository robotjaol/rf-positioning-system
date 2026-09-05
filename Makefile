.PHONY: install run test demo

install:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

run:
	PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	PYTHONPATH=backend pytest -q

demo:
	python3 scripts/replay_demo.py --url http://127.0.0.1:8000
