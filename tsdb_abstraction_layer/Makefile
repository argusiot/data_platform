init:
	pip3 install -r requirements.txt

test:
	# Without PYTHONHASHSEED=0, the TimeseriesID::fqid() method does not return
	# a stable hash value. We want that value to be stable for tests to pass.
	# FIXME: Experiment with PYTHONHASHSEED on CircleCI so we can re-enable the
	# TimeseriesID::fqid() test.
	# PYTHONHASHSEED=0 pytest -v tests
	python3 -m pytest -v tests

code_coverage:
	python3 -m coverage run -m --branch --source=. pytest -v tests && \
	python3 -m coverage report -m

install:
	pip3 install .

uninstall:
	python3 -m pip uninstall argus_tal

do_post_query:
	curl -d @experiments/post_query http://34.221.154.248:4242/api/query/exp | python -m json.tool

clean:
	rm -rf argus_tal.egg-info build dist
