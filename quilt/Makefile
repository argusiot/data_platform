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
	make build_package
	python3 -m pip install dist/argusquilt-*.whl

uninstall:
	pip3 uninstall argusquilt

clean:
	rm -rf argusquilt.egg-info build dist

