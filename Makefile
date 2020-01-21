run:
	python3 -m atticus

type_check:
	mypy --disallow-untyped-defs --ignore-missing-imports ./atticus

lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 ./atticus --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings.
	flake8 ./atticus --count --exit-zero --max-complexity=10 --statistics

test:
	pytest --cov=atticus tests/

verify: type_check lint test
