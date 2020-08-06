init:
	pip install -r requirements.txt

test:
	# Without PYTHONHASHSEED=0, the TimeseriesID::fqid() method does not return
	# a stable hash value. We want that value to be stable for tests to pass.
	# FIXME: Experiment with PYTHONHASHSEED on CircleCI so we can re-enable the
	# TimeseriesID::fqid() test.
	# PYTHONHASHSEED=0 pytest -v tests
	pytest -v tests

code_coverage:
	coverage run -m --branch --source=. pytest -v tests && \
	coverage report -m

install:
	python3 setup.py install

uninstall:
	python3 -m pip uninstall argus_tal

do_post_query:
	curl -d @experiments/post_query http://34.221.154.248:4242/api/query/exp | python -m json.tool
