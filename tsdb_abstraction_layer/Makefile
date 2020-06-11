init:
	pip install -r requirements.txt

test:
	# Without PYTHONHASHSEED=0, the TimeseriesID::fqid() method does not return
	# a stable hash value. We want that value to be stable for tests to pass.
	PYTHONHASHSEED=0 pytest -v tests

install:
	python3 setup.py install

uninstall:
	python3 -m pip uninstall argus_tal
