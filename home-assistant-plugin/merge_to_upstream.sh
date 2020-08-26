#!/bin/bash

source helper.sh

if [ "$MACHINE" == "Linux" ]; 
then
    rm -Rf ${HA_UPSTREAM}/homeassistant/components/knx/*
    cp -R ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/* ${HA_UPSTREAM}/homeassistant/components/knx/
    sed -i 's/custom_components.xknx/homeassistant.components.knx/g' ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i 's/"domain": "xknx"/"domain": "knx"/g' ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json
    LINE_NUMBER=`grep -n "requirements" ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json | cut -d":" -f1`
    sed -i "${LINE_NUMBER}s/.*/  \"requirements\": [\"xknx==${RELEASE}\"],/" ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json
    sed -i "s/DEPENDENCIES = \\['xknx'\\]/DEPENDENCIES = \\['knx'\\]/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i "s/DEFAULT_NAME = 'XKNX/DEFAULT_NAME = 'KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i "s/_XKNX_/_KNX_/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i "s/DATA_XKNX/DATA_KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i "s/DOMAIN = \"xknx\"/DOMAIN = \"knx\"/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py 
else
    rm -f ${HA_UPSTREAM}/homeassistant/components/knx/*
    cp ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/* ${HA_UPSTREAM}/homeassistant/components/knx/
    sed -i '.bak' 's/custom_components.xknx/homeassistant.components.knx/g' ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i '.bak' 's/"domain": "xknx"/"domain": "knx"/g' ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json
    LINE_NUMBER=`grep -n "requirements" ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json | cut -d":" -f1`
    sed -i '.bak' "${LINE_NUMBER}s/.*/  \"requirements\": [\"xknx==${RELEASE}\"],/" ${HA_UPSTREAM}/homeassistant/components/knx/manifest.json
    sed -i '.bak' "s/DEPENDENCIES = \\['xknx'\\]/DEPENDENCIES = \\['knx'\\]/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i '.bak' "s/DEFAULT_NAME = 'XKNX/DEFAULT_NAME = 'KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i '.bak' "s/_XKNX_/_KNX_/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i '.bak' "s/DATA_XKNX/DATA_KNX/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
    sed -i '.bak' "s/DOMAIN = \"xknx\"/DOMAIN = \"knx\"/g" ${HA_UPSTREAM}/homeassistant/components/knx/*.py
fi

