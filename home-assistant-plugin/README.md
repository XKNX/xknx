Installation Instructions:
-------------

See documentation at [http://xknx.io/home_assistant](http://xknx.io/home_assistant)

Merge upstream in XKNX
-------------

Use the `merge_from_upstream.pl` script to update the KNX component to the latest HA version.
It will copy all the files from your HA installation into the local XKNX repository.

Please make sure you read the instructions in the `merge_from_upstream.pl` script first before
you do this as it will override all changes in the XKNX repository with those from HA.

Merge XKNX changes into HA
-------------

Use the `merge_to_upstream.pl` script to update the HA KNX component to the current XKNX version.
It will copy all the files from your local XKNX repository to the HA repository.

Please make sure you read the instructions in the `merge_to_upstream.pl` script first before
you do this as it will override all changes in the HA component that were made to the KNX 
component(s).
