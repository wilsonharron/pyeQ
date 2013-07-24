pyeQ
====

Python wrapper for the Gracenote eyeQ API

requirements:
============

* pytz - https://pypi.python.org/pypi/pytz
* xmltodict - https://pypi.python.org/pypi/xmltodict
* xmlbuilder - https://pypi.python.org/pypi/xmlbuilder

installation:
============

python setup.py install

usage:
======

Make sure to have a developer account at http://developer.gracenote.com and sign up for an API Key (eyeQ and VideoExplore).

Put the provided CLIENT_ID and CLIENT_TAG into config.json

(You can also change your region from USA and/or language from ENG)

The URL and USER entries will be automatically populated

```
import pyeQ
config_file = 'config.json'
pq = pyeQ.pyeQ(config_filename)

providers = pq.provider_lookup('94608') # <--- 94608 == zipcode for gracenote!
channels = pq.provider_channels(providers[0]['GN_ID']) # <--- list of channels for first provider returned...

```

For the usage of this wrapper, take a look at the eyeQ/Video Explore API documentation on http://developer.gracenote.com

