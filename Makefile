load:
	python -m src.main

test:
	pytest

report:
	python -m src.main

clean:
	rmdir /S /Q __pycache__
