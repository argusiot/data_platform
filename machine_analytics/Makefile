code_coverage:
	coverage run -m --branch --source=. pytest -v tests && \
	coverage report -m

code_coverage_vagrant_friendly_html:
	coverage run -m --branch --source=. pytest -v tests && \
	rm -rf /tmp/htmlcov ; mkdir /tmp/htmlcov
	coverage html --directory=/tmp/htmlcov
	rm -rf /vagrant/htmlcov; mv /tmp/htmlcov /vagrant
	echo "Browser link: file:///Users/ppanse/my-Vagrant-VMs/test-VM/htmlcov/index.html"
test:
	pytest -s -v tests
