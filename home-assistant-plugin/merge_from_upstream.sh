#!/bin/bash

source helper.sh

if [ "$MACHINE" == "Linux" ]; 
then
    rm -Rf ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*
    cp -r ${HA_UPSTREAM}/homeassistant/components/knx/* ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/
    sed -i 's/homeassistant.components.knx/custom_components.xknx/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i 's/"domain": "knx"/"domain": "xknx"/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json
    LINE_NUMBER=`grep -n "requirements" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json | cut -d":" -f1`
    sed -i "${LINE_NUMBER}s/.*/  \"requirements\": [],/" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json
    sed -i 's/"requirements": ["xknx==.*]"/"domain": "xknx"/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json
    sed -i "s/DEPENDENCIES = \\['knx'\\]/DEPENDENCIES = \\['xknx'\\]/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i "s/DEFAULT_NAME = 'KNX/DEFAULT_NAME = 'XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i "s/_KNX_/_XKNX_/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i "s/DATA_KNX/DATA_XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i "s/DOMAIN = \"knx\"/DOMAIN = \"xknx\"/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py

    rm -f ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.bak
else
    rm -f ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*
    cp ${HA_UPSTREAM}/homeassistant/components/knx/* ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/
    sed -i '.bak' 's/homeassistant.components.knx/custom_components.xknx/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i '.bak' 's/"domain": "knx"/"domain": "xknx"/g' ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json
    LINE_NUMBER=`grep -n "requirements" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json | cut -d":" -f1`
    sed -i '.bak' "${LINE_NUMBER}s/.*/  \"requirements\": [],/" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/manifest.json
    sed -i '.bak' "s/DEPENDENCIES = \\['knx'\\]/DEPENDENCIES = \\['xknx'\\]/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i '.bak' "s/DEFAULT_NAME = 'KNX/DEFAULT_NAME = 'XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i '.bak' "s/_KNX_/_XKNX_/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i '.bak' "s/DATA_KNX/DATA_XKNX/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py
    sed -i '.bak' "s/DOMAIN = \"knx\"/DOMAIN = \"xknx\"/g" ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.py

    rm -f ${XKNX_REPO}/home-assistant-plugin/custom_components/xknx/*.bak
fi

