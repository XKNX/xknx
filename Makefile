
all:
	@echo
	@echo "Available targets"
	@echo ""
	@echo "build           -- build python package"
	@echo ""
	@echo "pypi            -- upload package to pypi"
	@echo ""
	@echo "test            -- execute test suite"
	@echo ""
	@echo "pylint          -- run pylint tests"
	@echo ""
	@echo "pydocstyle      -- run pydocstyle tests"
	@echo ""
	@echo "coverage        -- create coverage report"
	@echo ""
	@echo "clean           -- cleanup working directory"

test:
	pytest

build:
	@python3 setup.py sdist
	@python3 setup.py egg_info

pypi:
	# python3 setup.py register -r pypi
	#@python3 setup.py sdist upload -r pypi
	@rm -f dist/*
	@python setup.py sdist
	@twine upload dist/*

pylint:
	@pylint -j 8 --rcfile=.pylintrc xknx test/*.py *.py examples/*.py

pydocstyle:
	 @pydocstyle xknx test/*.py test/*.py *.py examples/*.py

coverage:
	pytest --cov-report html --cov xknx --verbose

clean:
	-rm -rf build dist xknx.egg-info
	-rm -rf .tox
	-rm -rf .coverage htmlcov

.PHONY: test build clean
