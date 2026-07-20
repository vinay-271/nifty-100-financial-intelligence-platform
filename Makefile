run:
	python -m src.main

test:
	pytest

coverage:
	pytest --cov=src --cov-report=term-missing

format:
	black src tests

lint:
	flake8 src tests

clean:
	rmdir /S /Q __pycache__
