code_coverage:
	python3 -m coverage run -m --branch --source=. pytest -v tests && \
	python3 -m coverage report -m

code_coverage_vagrant_friendly_html:
	python3 -m coverage run -m --branch --source=. pytest -v tests && \
	rm -rf /tmp/htmlcov ; mkdir /tmp/htmlcov
	python3 -m coverage html --directory=/tmp/htmlcov
	rm -rf /vagrant/htmlcov; mv /tmp/htmlcov /vagrant
	echo "Browser link: file:///Users/ppanse/my-Vagrant-VMs/<this_VM_dir>/htmlcov/index.html"
test:
	python3 -m pytest -s -v tests

build_package:
	python3 setup.py bdist_wheel
	echo "A distributable wheel file is generated under dist/"

install:
	make clean  # Ensure that all old wheel files are removed
	make build_package  # Build new whl file
	python3 -m pip install dist/argusquilt-*.whl  # Install wheel file

uninstall:
	pip3 uninstall argusquilt

clean:
	rm -rf argusquilt.egg-info build dist


integration_test:
	cd integration_tests ; python3 it_main.py

release_for_parag_env:
	# /quilt_deployment/ is a local directory mounted into Vagrant which
	# stores released files. This becomes a 'poor man's artefactory'
	# release.
	make clean
	make build_package
	cp dist/argusquilt-*.whl /quilt_deployment/
