vagrantPyCloud
==============

A small app that gives you the basic functionality of the vagrant cloud:

* Creation of Boxes
* Uploading of different Box versions
* Uploading of different providers for versions
* Supports Vagrant requests

## Installation

Just needs python, [Flask](http://flask.pocoo.org/) and this code

## Configuration

The configuration for vagrant PyCloud is simple, there are only two things that need configuring; Site hostname and box 
root

### Hostname

Hostname is configured by chaning the `SERVER_NAME` variable. This is injected into the metadata files to allow easy 
migration of the metadata or chaning of a site's domain name

### Box Home

Once you've got the code you need to decide where the files will be stored, by default this is in a folder called `boxes` 
under the app root. This can be configured by changing the value of the `BOX_ROOT` varaible.

## WSGI deployment

The application may be easily deployed in a WSGI container. Simply point your WSGI server at the `vagrantPyCloud.wsgi`
file with PYTHON_PATH set up correctly. Or optionally install vagrantPyCloud to a virtualenv first, and configure the
`.wsgi` file accordingly.