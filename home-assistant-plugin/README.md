Installation Instructions:
-------------

See documentation at [http://xknx.io/home_assistant](http://xknx.io/home_assistant)

Merge upstream in XKNX
-------------

Use the `merge_from_upstream.sh` script to update the KNX component to the latest HA version.
It will copy all the files from your HA installation into the local XKNX repository.

Please create a config file called `.config`. There is a template file called `.config.template`
which you can use as a starting point.

Merge XKNX changes into HA
-------------

Use the `merge_to_upstream.sh` script to update the HA KNX component to the current XKNX version.
It will copy all the files from your local XKNX repository to the HA repository.

Please create a config file called `.config`. There is a template file called `.config.template`
which you can use as a starting point.
