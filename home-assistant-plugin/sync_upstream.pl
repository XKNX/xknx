#!/usr/bin/perl
use strict;
my ($ha_upstream, $local_xknx) = @ARGV;

if (not defined $ha_upstream) {
    die "ha_upstream (1) is not defined. Set it to the path to your HA repository."
}

if (not defined $local_xknx) {
    die "local_xknx (2) is not defined. Set it to the path of your XKNX repository."
}

my @FILES = split /\n/, `find $ha_upstream/homeassistant/components/ |grep knx|grep -v __pycache__`;

print `rm $local_xknx/home-assistant-plugin/custom_components/*/*.py`;
print `rm $local_xknx/home-assistant-plugin/custom_components/*.py`;

foreach(@FILES)
{
    if (-d $_)
    {
        print "Skipping $_\n";
    }
    else
    {
        my $orig = $_;
        s/^.*components\///g;
        s/knx.py/xknx.py/g;
        my $to = $local_xknx . "/home-assistant-plugin/custom_components/".$_;
        print "$orig -> $to\n";
        print `cp $orig $to`;
        print `sed -i '.bak' 's/homeassistant.components.knx/custom_components.xknx/g' $to`;
        print `sed -i '.bak' \"s/DEPENDENCIES = \\['knx'\\]/DEPENDENCIES = \\['xknx'\\]/g\" $to`;
        print `sed -i '.bak' \"s/DEFAULT_NAME = 'KNX/DEFAULT_NAME = 'XKNX/g\" $to`;
        print `sed -i '.bak' \"s/_KNX_/_XKNX_/g\" $to`;
        print `sed -i '.bak' \"s/DATA_KNX/DATA_XKNX/g\" $to`;
        print `sed -i '.bak' \"s/DOMAIN = \\\"knx\\\"/DOMAIN = \\\"xknx\\\"/g\" $to`;
    }
}