#!/usr/bin/perl
use strict;
my ($ha_upstream, $local_xknx) = @ARGV;

if (not defined $ha_upstream) {
    die "ha_upstream (1) is not defined. Set it to the path to your HA repository."
}

if (not defined $local_xknx) {
    die "local_xknx (2) is not defined. Set it to the path of your XKNX repository."
}

my @FILES = split /\n/, `find $local_xknx/home-assistant-plugin/custom_components |grep xknx|grep -v __pycache__|grep -v .gitignore`;

print `rm $ha_upstream/homeassistant/components/*/knx.py`;
print `rm $ha_upstream/homeassistant/components/knx.py`;

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
        s/xknx.py/knx.py/g;
        my $to = $ha_upstream . "/homeassistant/components/".$_;
        print "$orig -> $to\n";
        print `cp $orig $to`;
        print `sed -i '.bak' 's/custom_components.xknx/homeassistant.components.knx/g' $to`;
        print `sed -i '.bak' \"s/DEPENDENCIES = \\['xknx'\\]/DEPENDENCIES = \\['knx'\\]/g\" $to`;
        print `sed -i '.bak' \"s/DEFAULT_NAME = 'XKNX/DEFAULT_NAME = 'KNX/g\" $to`;
        print `sed -i '.bak' \"s/_XKNX_/_KNX_/g\" $to`;
        print `sed -i '.bak' \"s/DATA_XKNX/DATA_KNX/g\" $to`;
        print `sed -i '.bak' \"s/DOMAIN = \\\"xknx\\\"/DOMAIN = \\\"knx\\\"/g\" $to`;
    }
}