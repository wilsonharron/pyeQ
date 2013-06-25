'''
Created on Jun 24, 2013

@author: wharron
'''


import xmltodict
import urllib2

from config import PYEQCONFIG
from pyeQ.exceptions import pyeQConnectionExcption, pyeQException,\
    pyeQNotFoundException
from xmlbuilder import XMLBuilder
from config import save_config
from datetime import datetime

import pytz
import pytz.reference
from collections import OrderedDict

TRUE = {'true', 'True', 'TRUE', 'yes', 'y', 'Y', 'YES', '1', 't', 'T', True}

class pyeQ(object):
    def __init__(self):
        self.URL = PYEQCONFIG.URL
        self.CLIENT_ID = PYEQCONFIG.CLIENT_ID
        self.CLIENT_TAG = PYEQCONFIG.CLIENT_TAG
        self.CLIENT_ID_TAG = '{0}-{1}'.format(self.CLIENT_ID, self.CLIENT_TAG)
        self.COUNTRY = PYEQCONFIG.COUNTRY
        self.LANG = PYEQCONFIG.LANGUAGE
        if not PYEQCONFIG.get('AUTH', None):
            self.get_user_auth()
            
        self.tz = pytz.reference.LocalTimezone()
    
    def query_eyeq(self, queryxml):
        try:
            response = urllib2.urlopen(self.URL, str(queryxml))
        except urllib2.URLError:
            raise pyeQConnectionExcption('Could not connect to {0}'.format(self.URL))
        response = xmltodict.parse(response)
        if response['RESPONSES']['RESPONSE']['@STATUS'] != 'OK':
            print str(queryxml), response
            status = response['RESPONSES']['RESPONSE']['@STATUS']
            message = response['RESPONSES'].get('MESSAGE', '')
            if status == 'NO_MATCH':
                raise pyeQNotFoundException()
            raise pyeQException('query failed: {0} ({1})'.format(status, message))
        return response['RESPONSES']['RESPONSE']
    
    def __query_xml(self):
        x = XMLBuilder('QUERIES')
        with x.AUTH:
            x.CLIENT(self.CLIENT_ID_TAG)
            x.USER(self.USER)
        x.COUNTRY(self.COUNTRY)
        x.LANG(self.LANG)
        return x
    
    def get_user_auth(self):
        x = XMLBuilder('QUERIES')
        with x.QUERY(cmd='REGISTER'):
            x.CLIENT(self.CLIENT_ID_TAG)
        response = self.query_eyeq(x)
        self.USER = response['USER']
        PYEQCONFIG.USER = self.USER
        save_config()
    
    def provider_lookup(self, zipcode):
        x = self.__query_xml()
        with x.QUERY(CMD='TVPROVIDER_LOOKUP'):
            x.POSTALCODE(zipcode)
        return self.query_eyeq(x)

    def provider_channels(self, provider_id):
        if isinstance(provider_id, dict):
            provider_id = provider_id.get('GN_ID', None)
            if not provider_id:
                raise pyeQException('INVALID PROVIDER ID')
        x = self.__query_xml()
        with x.QUERY(CMD='TVCHANNEL_LOOKUP'):
            x.MODE('TVPROVIDER')
            x.GN_ID(provider_id)
        response = self.query_eyeq(x)
        return response['TVCHANNEL']
    
    def grid_lookup(self, channels, start=None, end=None, mode=None, gnid=None, page=None, tvprogram_image=False, ipg_image=False):
        modes = {'CONTRIBUTOR', 'AV_WORK', 'SERIES', 'SEASON'}
        if isinstance(channels, str):
            channels = [channels]
        x = self.__query_xml()
        if mode is not None and mode.upper() not in modes:
            raise pyeQException('unsupported mode: {0}'.format(mode))
        if mode is not None and gnid is None:
            raise pyeQException('{0} requires a gnid'.format(mode))
        
        if page is not None and len(page) != 2:
            raise pyeQException('invalid range')
        
        with x.QUERY(CMD='TVGRID_LOOKUP'):
            with x.TVCHANNEL:
                for c in channels:
                    x.GN_ID(str(c))
            if start:
                try:
                    start = start.astimezone(pytz.utc)
                except:
                    start = self.tz.localize(start)
                    start = start.astimezone(pytz.utc)
                x.DATE(start.strftime('%Y-%m-%dT%H:%M'), TYPE='START')
            if end:
                try:
                    end = end.astimezone(pytz.utc)
                except:
                    end = end.tz.localize(end)
                    end = end.astimezone(pytz.utc)
                x.DATE(end.strftime('%Y-%m-%dT%H:%M'), TYPE='END')
            if mode is not None:
                x.MODE(mode.upper())
                x.GN_ID(gnid)
            extended = []
            if tvprogram_image in TRUE:
                extended.append('TVPROGRAM_IMAGE')
            if ipg_image in TRUE:
                extended.append('IPG_IMAGE')
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
            
            if page:
                with x.RANGE:
                    x.START(str(page[0]))
                    x.END(str(page[1]))
        
        response = self.query_eyeq(x)['TVGRID']
        if isinstance(response['TVPROGRAM'], OrderedDict):
            response['TVPROGRAM'] = [response['TVPROGRAM']]
        programs = {v['GN_ID']: v for v in response['TVPROGRAM']}
        if isinstance(response['TVAIRING'], OrderedDict):
            response['TVAIRING']=[response['TVAIRING']]
        for airing in response['TVAIRING']:
            program = programs[airing['@TVPROGRAM_GN_ID']]
            if 'AIRINGS' not in program:
                program['AIRINGS'] = []
            airing['@START'] = pytz.utc.localize(datetime.strptime(airing['@START'], '%Y-%m-%dT%H:%M'))
            airing['@END'] = pytz.utc.localize(datetime.strptime(airing['@END'], '%Y-%m-%dT%H:%M'))
            program['AIRINGS'].append({'CHANNEL':airing['@TVCHANNEL_GN_ID'],
                                       'START':airing['@START'],
                                        'END':airing['@END']})
        return programs.values(), (response['RANGE']['COUNT'], response['RANGE']['START'], response['RANGE']['END'])
    
    def tvgrid_search(self, title, channels = None, start = None, end = None, page=None, tvprogram_image=False, ipg_image=False):
        if isinstance(channels, str):
            channels = [channels]
        x = self.__query_xml()
                
        if page is not None and len(page) != 2:
            raise pyeQException('invalid range')
        
        with x.QUERY(CMD='TVGRID_SEARCH'):
            if channels is not None:
                with x.TVCHANNEL:
                    for c in channels:
                        x.GN_ID(str(c))
            x.TEXT(title, TYPE='TVPROGRAM_TITLE')
            if start:
                try:
                    start = start.astimezone(pytz.utc)
                except:
                    start = self.tz.localize(start)
                    start = start.astimezone(pytz.utc)
                x.DATE(start.strftime('%Y-%m-%dT%H:%M'), TYPE='START')
            if end:
                try:
                    end = end.astimezone(pytz.utc)
                except:
                    end = end.tz.localize(end)
                    end = end.astimezone(pytz.utc)
                x.DATE(end.strftime('%Y-%m-%dT%H:%M'), TYPE='END')
            extended = []
            if tvprogram_image in TRUE:
                extended.append('TVPROGRAM_IMAGE')
            if ipg_image in TRUE:
                extended.append('IPG_IMAGE')
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
            
            if page:
                with x.RANGE:
                    x.START(page[0])
                    x.END(page[1])
        
        response = self.query_eyeq(x)['TVGRID']
        if isinstance(response['TVPROGRAM'], OrderedDict):
            response['TVPROGRAM'] = [response['TVPROGRAM']]
        programs = {v['GN_ID']: v for v in response['TVPROGRAM']}
        for airing in response['TVAIRING']:
            program = programs[airing['@TVPROGRAM_GN_ID']]
            if 'AIRINGS' not in program:
                program['AIRINGS'] = []
            program['AIRINGS'].append({'CHANNEL':airing['@TVCHANNEL_GN_ID'],
                                       'START':pytz.utc.localize(datetime.strptime(airing['@START'], '%Y-%m-%dT%H:%M')),
                                        'END':pytz.utc.localize(datetime.strptime(airing['@END'], '%Y-%m-%dT%H:%M'))})
        return programs.values(), (response['RANGE']['COUNT'], response['RANGE']['START'], response['RANGE']['END'])


    def channel_lookup(self, channelid):
        x = self.__query_xml()
        with x.QUERY(cmd='TVCHANNEL_FETCH'):
            x.GN_ID(channelid)
            with x.OPTION:
                x.PARAMETER('SELECT_EXTENDED')
                x.VALUE('IMAGE,LINK')
        return self.query_eyeq(x)['TVCHANNEL']
    
    def tvprogram_fetch(self, tvprogramid, image=True, contributer_image=False, ipgcategory_image=False, link=False):
        extended = ['AV_WORK']
        if image in TRUE:
            extended.append('TVPROGRAM_IMAGE')
        if contributer_image in TRUE:
            extended.append('CONTRIBUTOR_IMAGE')
        if ipgcategory_image in TRUE:
            extended.append('IPGCATEGORY_IMAGE')
        if link in TRUE:
            extended.append('LINK')
        x = self.__query_xml()
        with x.QUERY(cmd='TVPROGRAM_FETCH'):
            x.GN_ID(tvprogramid)
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
                with x.OPTION:
                    x.PARAMETER('IMAGE_SIZE')
                    x.VALUE(','.join(['LARGE', 'MEDIUM', 'SMALL']))
        return self.query_eyeq(x)['TVPROGRAM']
    
    def __get_image_url(self, mode, gnid, sizes=None):
        x = self.__query_xml()
        if sizes is None:
            sizes = ['THUMBNAIL', 'MEDIUM']
        with x.QUERY(cmd='URL_GET'):
            x.MODE(mode)
            if isinstance(gnid, str):
                gnid = [gnid]
            if isinstance(sizes, str):
                size = [sizes]
            for id in gnid:
                x.GN_ID(id)
            with x.OPTION:
                x.PARAMETER('IMAGE_SIZE')
                x.VALUE(','.join(size))
        return self.query_eyeq(x)
    
    def get_channel_logos(self, channelids):
        return self.__get_image_url('TVCHANNEL_IMAGE', channelids)
    
    def get_avwork_images(self, avwork_ids, sizes=None):
        return self.__get_image_url('AV_WORK_IMAGE', avwork_ids, sizes)
    
    def get_contributer_images(self, contributor_ids, sizes=None):
        return self.__get_image_url('CONTRIBUTOR_IMAGES', contributor_ids, sizes)
    
    def get_ipg_category_image(self, ipg_ids, sizes=None):
        if sizes is None:
            sizes = ['THUMBNAIL', 'MEDIUM']
        x = self.__query_xml()
        with x.QUERY(cmd='URL_GET'):
            x.mode('IPGCATEGORY_IMAGE')
            for ipgid in ipg_ids:
                if ipgid[0] == 'L1':
                    x.IPG_CATEGORY_L1_ID(ipgid[1])
                else:
                    x.IPG_CATEGORY_L2_ID(ipgid[1])
        return self.query_eyeq(x)
    
    def ipg_category_list(self):
        x = self.__query_xml()
        with x.QUERY('FIELDVALUES'):
            x.FIELDNAME('IPGCATEGORY_L1')
        L1 = self.query_eyeq(x)['IPGCATEGORY_L1']
        L1 = {v['@ID'] : v['#text'] for v in L1 }
        x = self.__query_xml()
        with x.QUERY('FIELDVALUES'):
            x.FIELDNAME('IPGCATEGORY_L2')
        L2 = self.query_eyeq(x)['IPGCATEGORY_L2']
        L2 = {v['@ID'] : v['#text'] for v in L2 }
        
        return L1, L2

    def __fieldvalues(self, fieldname):
        x = self.__query_xml()
        with x.QUERY('FIELDVALUES'):
            x.FIELDNAME(fieldname)
            x.MEDIASPACE('VIDEO')
        return self.query_eyeq(x)
    
    def production_list(self):
        return self.__fieldvalues('PRODUCTION_TYPE')
    
    def epgproduction_list(self):
        return self.__fieldvalues('EPGPRODUCTION_TYPE')
    
    def contribution_list(self):
        return self.__fieldvalues('CONTRIBUTION_TYPE')
    
    def origin_list(self):
        return self.__fieldvalues('ORIGIN')
    
    def avwork_fetch(self, avwork, image=True, videoproperties=True, contributor_image=True, link=True, image_gallery=False):
        extended = []
        if image in TRUE:
            extended.append('IMAGE')
        if videoproperties in TRUE:
            extended.append('VIDEOPROPERTIES')
        if contributor_image in TRUE:
            extended.append('CONTRIBUTOR_IMAGE')
        if link:
            extended.append('LINK')
        if image_gallery in TRUE:
            extended.append('IMAGE_GALLERY')
        x = self.__query_xml()
        with x.QUERY(cmd='AV_WORK_FETCH'):
            x.GN_ID(avwork)
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
        response = self.query_eyeq(x)
        return response['AV_WORK']            
    
    def avwork_search(self, title, 
                      best=False, 
                      image=True, 
                      contributor=False, 
                      videodiscset=False,
                      videodiscset_coverart=False, 
                      link=True,
                      image_gallery=False,
                      filters=None):
        extended = []
        if image in TRUE:
            extended.append('IMAGE')
        if contributor in TRUE:
            extended.append('CONTRIBUTOR_IMAGE')
        if videodiscset in TRUE:
            extended.append('VIDEODISCSET')
        if videodiscset_coverart in TRUE:
            extended.append('VIDEODISCSET_COVERART')
        if link in TRUE:
            extended.append('LINK')
        if image_gallery in TRUE:
            extended.append('IMAGE_GALLERY')
        
        x = self.__query_xml()
        with x.QUERY(cmd='AV_WORK_SEARCH'):
            if best:
                x.MODE('SINGLE_BEST')
            x.TEXT(title, TYPE='TITLE')
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
            if filters:
                for f in filters:
                    x.FILTER(f['ID'], TYPE=f['TYPE'], MODE=f['MODE'])
        response = self.query_eyeq(x)
        return response['AV_WORK']
    
    def series(self, gnid=None, title=None, best=True, image=True, contributor=True, link=True):
        extended = []
        if not gnid and not title:
            raise pyeQException('neither a gn_id nor a title specified')
        if image in TRUE:
            extended.append('IMAGE')
        if contributor in TRUE:
            extended.append('CONTRIBUTOR_IMAGE')
        if link in TRUE:
            extended.append('LINK')
        x = self.__query_xml()
        if gnid:
            cmd = 'SERIES_FETCH'
        else:
            cmd = 'SERIES_SEARCH'
        with x.QUERY(cmd=cmd):
            if not gnid and best:
                x.MODE('SINGLE_BEST')
            if not gnid:
                x.TEXT(title, TYPE='TITLE')
            else:
                x.GN_ID(gnid)
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
        return self.query_eyeq(x)['SERIES']

    def season(self, seasonid, image=True, contributor=True, link=True):
        extended = []
        if image in TRUE:
            extended.append('IMAGE')
        if contributor in TRUE:
            extended.append('CONTRIBUTOR_IMAGE')
        if link in TRUE:
            extended.append('LINK')
        x = self.__query_xml()
        with x.QUERY(cmd='SEASON_FETCH'):
            x.GN_ID(seasonid)
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
        return self.query_eyeq(x)['SEASON']

    def contributor_fetch(self, gn_id, image=True, mediagraphy=True, mediagraphy_images=False):
        extended = []
        if image in TRUE:
            extended.append('IMAGE')
        if mediagraphy in TRUE:
            extended.append('FULL_MEDIAGRAPHY')
        if mediagraphy_images in TRUE:
            extended.append('MEDIAGRAPHY_IMAGES')
        x = self.__query_xml()
        with x.QUERY(cmd='CONTRIBUTOR_FETCH'):
            x.GN_ID(gn_id)
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
        return self.query_eyeq(x)['CONTRIBUTOR']
    
    def contributor_search(self, name, best=False, image=True, mediagraphy=False, mediagraphy_images=False):
        extended = []
        if image in TRUE:
            extended.append('IMAGE')
        if mediagraphy in TRUE:
            extended.append('FULL_MEDIAGRAPHY')
        if mediagraphy_images in TRUE:
            extended.append('MEDIAGRAPHY_IMAGES')
        x = self.__query_xml()
        with x.query(cmd='CONTRIBUTOR_SEARCH'):
            if best in TRUE:
                x.MODE('SINGLE_BEST')
            x.TEXT(name, TYPE='NAME')
            if extended:
                with x.OPTION:
                    x.PARAMETER('SELECT_EXTENDED')
                    x.VALUE(','.join(extended))
        return self.query_eyeq(x)['CONTRIBUTOR']
        