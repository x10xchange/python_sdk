format:
	isort --profile black ./examples ./tests ./x10
	black --target-version py310 --line-length 120 ./examples ./tests ./x10

lint:
	safety check \
		-i 51457 \
		-i 64227 \
		-i 64396 \
		-i 64459 \
		-i 64642 \
		-i 65693 \
		-i 66742 \
		-i 67599 \
		-i 67895 \
		-i 70612 \
		-i 70630 \
		-i 71064 \
		-i 71545 \
		-i 71591 \
		-i 71608 \
		-i 73456 \
		-i 74251 \
		-i 76752
	black --check --diff --target-version py310 --line-length 120 ./examples ./tests ./x10
	flake8 ./examples ./tests ./x10
	mypy

test:
	tox

bump:
	poetry version patch
