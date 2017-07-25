
all:
	@echo
	@echo "Available targets"
	@echo ""
	@echo "build           -- build python package"
	@echo ""
	@echo "upload-pypi     -- upload package to pypi"
	@echo ""
	@echo "upload-pypitest -- upload package to pypi-test"
	@echo ""
	@echo "test            -- execute test suite"
	@echo ""
	@echo "pylint          -- run pylint tests"
	@echo ""
	@echo "pydocstyle      -- run pydocstyle tests"
	@echo ""

test:
	@$(MAKE) -C test all

build:
	@python3 setup.py sdist
	@python3 setup.py egg_info

upload-pypitest:
	# python3 setup.py register -r pypitest
	@python3 setup.py sdist upload -r pypitest

upload-pypi:
	# python3 setup.py register -r pypi
	@python3 setup.py sdist upload -r pypi

pylint:
	@pylint -j 8 --rcfile=.pylintrc xknx test/*.py *.py examples/*.py

pydocstyle:
	 @pydocstyle xknx test home-assistant-plugin	

.PHONY: test build
