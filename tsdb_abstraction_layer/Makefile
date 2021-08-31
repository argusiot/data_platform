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

build_package:
	python3 setup.py bdist_wheel
	echo "A distributable wheel file is generated under dist/"

install:
	make clean
	make build_package
	python3 -m pip install dist/argustal-*.whl

uninstall:
	pip3 uninstall argustal

clean:
	rm -rf argustal.egg-info build dist

release_for_parag_env:
	# /quilt_deployment/ is a local directory mounted into Vagrant which
	# stores released files. This becomes a 'poor man's artefactory'
	# release.
	make clean
	make build_package
	cp dist/argustal-*.whl /quilt_deployment/
