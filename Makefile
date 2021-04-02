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
	@rm -f dist/*
	@python setup.py sdist
	@twine upload dist/*

pylint:
	@pylint --jobs=0 --rcfile=.pylintrc xknx *.py examples/*.py
	@pylint --jobs=0 --rcfile=.pylintrc --disable=no-self-use,protected-access,abstract-class-instantiated test/*

pydocstyle:
	@pydocstyle xknx test/*.py test/*.py *.py examples/*.py

coverage:
	pytest --cov-report html --cov xknx --verbose

clean:
	-rm -rf build dist xknx.egg-info
	-rm -rf .tox
	-rm -rf .coverage htmlcov

.PHONY: test build clean
