# AllJoyn Packager

This is a script to build AllJoyn packages using `fpm`.

## Dependencies

You will need [`fpm`](https://github.com/jordansissel/fpm) and AllJoyn's dependencies. `fpm` can generally be installed using Ruby's `gem`.

### Fedora 23

    sudo dnf install ruby-devel rubygems
    gem install fpm

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
