'''
Created on Jun 25, 2013

@author: wharron
'''

from setuptools import setup
import os
import json

def create_configuration_script():
    if os.path.exists(os.path.join('pyeQ', 'config.json')):
        return True
#    elif os.path.exists('license.txt'):
#        ### read license file
#        pass
    else:
        config = {}
        config['CLIENT_ID'] = raw_input('CLIENT_ID: ').strip()
        config['CLIENT_TAG'] = raw_input('CLIENT_TAG: ').strip()
        with open(os.path.join('pyeQ', 'config.json'), 'w') as f:
            json.dump(config, f)

setup(name='pyeQ',
      version='0.1',
      install_requires=['xmltodict', 'xmlbuilder', 'pytz'],
      data_files=[('pyeQ',['pyeQ/config.json'])],
      packages=['pyeQ'])

