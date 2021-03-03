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
