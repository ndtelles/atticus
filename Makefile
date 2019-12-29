run:
	python3 -m atticus

type_check:
	mypy --disallow-untyped-defs --ignore-missing-imports ./atticus

lint:
	-pylint ./atticus

test:
	pytest --cov=atticus tests/

verify: type_check lint test
