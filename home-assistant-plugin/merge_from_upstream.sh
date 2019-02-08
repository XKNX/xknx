#!/bin/bash

if [[ -f .config ]]; then
    source .config
else
    echo "Please create the .config file containing the HA_UPSTREAM and the XKNX_REPO variables"
    exit 1
fi

if [[ ! -d ${XKNX_REPO}/home-assistant-plugin ]]; then
    echo "XKNX repo path is wrong"
    exit 1
fi

if [[ ! -d ${HA_UPSTREAM}/homeassistant ]]; then
    echo "HA upstream repo path is wrong"
    exit 1
fi

rm -f ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
cp ${HA_UPSTREAM}/homeassistant/components/knx/* ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/
sed -i '.bak' 's/homeassistant.components.knx/custom_components.xknx/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
sed -i '.bak' "s/DEPENDENCIES = \\['knx'\\]/DEPENDENCIES = \\['xknx'\\]/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
sed -i '.bak' "s/DEFAULT_NAME = 'KNX/DEFAULT_NAME = 'XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
sed -i '.bak' "s/_KNX_/_XKNX_/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
sed -i '.bak' "s/DATA_KNX/DATA_XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
sed -i '.bak' "s/DOMAIN = \"knx\"/DOMAIN = \"xknx\"/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py

rm -f ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py.bak