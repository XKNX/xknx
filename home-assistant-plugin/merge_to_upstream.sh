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

rm -f ${HA_UPSTREAM}/homeassistant/components/knx/*
cp ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/* ${HA_UPSTREAM}/homeassistant/components/knx/
sed -i '.bak' 's/custom_components.xknx/homeassistant.components.knx/g' ${HA_UPSTREAM}/homeassistant/components/knx/*.py
sed -i '.bak' "s/DEPENDENCIES = \\['xknx'\\]/DEPENDENCIES = \\['knx'\\]/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
sed -i '.bak' "s/DEFAULT_NAME = 'XKNX/DEFAULT_NAME = 'KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
sed -i '.bak' "s/_XKNX_/_KNX_/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
sed -i '.bak' "s/DATA_XKNX/DATA_KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
sed -i '.bak' "s/DOMAIN = \"xknx\"/DOMAIN = \"knx\"/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py

rm -f ${HA_UPSTREAM}/homeassistant/components/knx/*.py.bak