format:
	black .

lint:
	ruff check .

type:
	mypy .

test:
	pytest
