
all:
	@echo
	@echo "Available targets"
	@echo ""
	@echo "test  - execute test suite"
	@echo ""
	@echo "build - build python package"
	@echo "" 
	@echo "pylint -- run pylint tests"
	@echo ""

test:
	@$(MAKE) -C test all

build:
	python3 setup.py sdist
	python3 setup.py egg_info

upload-pypitest:
	# python3 setup.py register -r pypitest
	python3 setup.py sdist upload -r pypitest

upload-pypi:
	# python3 setup.py register -r pypi
	python3 setup.py sdist upload -r pypi

pylint:
	pylint --rcfile=.pylintrc xknx test/*.py


.PHONY: test build
