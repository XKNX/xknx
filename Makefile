
all:
	@echo
	@echo "Available targets"
	@echo ""
	@echo "test  - execute test suite"
	@echo ""
	@echo "build - build python package"
	@echo "" 

test:
	@$(MAKE) -C test all

build:
	./build.sh

.PHONY: test build
