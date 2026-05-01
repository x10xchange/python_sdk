format:
	isort --profile black ./examples ./tests ./x10
	black --target-version py310 --line-length 120 ./examples ./tests ./x10

lint:
	black --check --diff --target-version py310 --line-length 120 ./examples ./tests ./x10
	flake8 ./examples ./tests ./x10
	mypy ./examples ./x10

test:
	tox

bump:
	poetry version minor
