'''
Created on Jun 24, 2013

@author: wharron
'''

import os, json
from exceptions import pyeQConfigurationException
from base64 import b64decode, b64encode

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

class DotDict(dict):
    def __getattr__(self, attr):
        return self.__getitem__(attr)
    def __setattr__(self, key, val):
        self.__setitem__(key, val)

def read_configuration(config_file):
    try:
        with open(config_file, 'r') as f:
            PYEQCONFIG = DotDict(json.load(f))
    except IOError:
        raise pyeQConfigurationException('Could not load configuration file')
    except:
        raise pyeQConfigurationException('Invalid configuration file')

    if not PYEQCONFIG.get('CLIENT_ID', None):
        raise pyeQConfigurationException('CLIENT_ID is missing or empty')
    if not PYEQCONFIG.get('CLIENT_TAG', None):
        raise pyeQConfigurationException('CLIENT_TAG is missing or empty')
    if not PYEQCONFIG.get('URL', None):
        raise pyeQConfigurationException('CLIENT_TAG is missing or empty')
    if not PYEQCONFIG.get('COUNTRY', None):
        PYEQCONFIG.COUNTRY = 'usa'
    if not PYEQCONFIG.get('LANGUAGE', None):
        PYEQCONFIG.LANGUAGE = 'eng'
    return PYECONFIG

def save_config(config_file, PYEQCONFIG):
    with open(config_file, 'w') as f:
        json.dump(PYEQCONFIG, f)

