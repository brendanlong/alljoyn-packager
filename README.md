# AllJoyn Packager

This is a script to build AllJoyn packages using `fpm`.

## Dependencies

You will need [`fpm`](https://github.com/jordansissel/fpm) and AllJoyn's dependencies. `fpm` can generally be installed using Ruby's `gem`. You will also need [AllJoyn's dependencies](https://allseenalliance.org/framework/documentation/develop/building/linux).

### Fedora 23

    sudo dnf install ruby-devel rubygems
    gem install fpm

### Ubuntu

Update if this is a new VM:

    sudo apt-get update
    sudo apt-get upgrade

Then install the dependencies:

    sudo apt-get install ruby ruby-dev build-essential libgtk2.0-dev libssl-dev libxml2-dev libcap-dev xsltproc python scons
    sudo gem install fpm

## Running

To run:

    # Build standard packages for your distro and platform
    ./alljoyn-packager.py

    # Build debug packages
    ./alljoyn-packager.py -d

    # Explicitly build Debian packages
    ./alljoyn-packager.py -t deb

Your platform and package type should be auto-detected, but this has only been tested on `x86_64` and Fedora. Any [`-t` supported by `fpm`](https://github.com/jordansissel/fpm/wiki) should work.

`--platform` should be detected automatically, but has only been tested on `x86_64`. Set manually if necessary.

## Install

### Fedora

    sudo dnf install *.rpm

### Ubuntu

Currently you can only install one of alljoyn-c-devel and alljoyn-devel. Here's how you would install everything except alljoyn-c-devel:

    sudo dpkg -i alljoyn_*.deb alljoyn-daemon_*.deb alljoyn-devel*.deb alljoyn-c_*.deb
