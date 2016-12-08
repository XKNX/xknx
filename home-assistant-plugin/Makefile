
help:
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "install             will copy plugin to plugindirectory .homeassistant/custom_components"
	@echo ""

install:
	@mkdir -p ~/.homeassistant/custom_components/switch
	@mkdir -p ~/.homeassistant/custom_components/climate
	@mkdir -p ~/.homeassistant/custom_components/xknx
	@cp custom_components/switch/xknx.py ~/.homeassistant/custom_components/switch
	@cp custom_components/climate/xknx.py ~/.homeassistant/custom_components/climate
	@cp custom_components/xknx/__init__.py ~/.homeassistant/custom_components/xknx
	@cp custom_components/xknx/xknx_wrapper.py ~/.homeassistant/custom_components/xknx
