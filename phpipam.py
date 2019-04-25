# -*- coding: utf-8 -*-
'''
A simple SaltStack extension module interacting with {php}IPAM.
Copyright (C) 2019 Davide Madrisan <davide.madrisan@gmail.com>

The PHPIPAM module requires a configuration profile to be configured
in either the minion or, as in our implementation, in the master
configuration file (/etc/salt/master.d/phpipam.conf).

This profile requires very little:

.. code-block:: yaml

    phpipam:
      url: https://ipam.mydomain.com
      auth:
        user: 'read_api_user'
        password: 'xxxxx'

This file should be saved as salt/_modules/phpipam.py.
'''

# Import Python libs
import logging
import requests

# Import Salt libs
import salt.config
import salt.exceptions

log = logging.getLogger(__name__)

__virtualname__ = 'phpipam'

def __virtual__():
    return True

class Api(object):
    '''
    Class for managing the {php}IPAM token for successive queries.
    '''
    def __init__(self, debug=False):
        self.debug = debug

        phpipam_config = self._config()
        try:
            self._phpipam_url = phpipam_config['url']
            auth = phpipam_config['auth']
            self._user = auth['user']
            self._password = auth['password']
        except KeyError as err:
            log.error('Failed to get the {php}IPAM configuration! %s: %s',
                      type(err).__name__, err)
            raise salt.exceptions.CommandExecutionError(
                "Cannot find the {php}IPAM configuration!")

        self._api_url = '{0}/api/lookup/'.format(self._phpipam_url)
        self._verify = phpipam_config.get('verify',
                                          '/etc/ssl/certs/ca-certificates.crt')
        self._token = self._get_token()

    def _config(self):
        '''
        Return the SaltStack configuration for {php}IPAM
        '''
        try:
            master_opts = salt.config.client_config('/etc/salt/master')
        except Exception as err:
            log.error('Failed to read configuration for {php}IPAM! %s: %s',
                      type(err).__name__, err)
            raise salt.exceptions.CommandExecutionError(err)

        phpipam_config = master_opts.get('phpipam', {})
        return phpipam_config

    def _get_token(self):
        '''
        Get an {php}IPAM for future queries
        '''
        resource = 'user'
        url = "{0}/{1}".format(self._api_url, resource)
        response = requests.request('POST',
                                    url,
                                    auth=(self._user, self._password),
                                    verify=self._verify)

        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        token = response.json()['data']['token']
        return token

    def token(self):
        '''
        Return the current API token
        '''
        return self._token

    def query(self, resource):
        '''
        Perform a query directly against the {php}IPAM REST API
        '''
        url = "{0}/{1}".format(self._api_url, resource)
        headers = {
            'token': self._token,
            'Content-Type': 'application/json'
        }
        response = requests.request('GET',
                                    url,
                                    headers=headers,
                                    verify=self._verify)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        json = response.json()
        if 'data' in json:
            return json['data']

        if 'message' in json:
            log.debug('Failed to get data from {php}IPAM: %s: %s',
                      url, json['message'])
        return {}

def get(key):
    '''
    Query a {php}IPAM server to get the IP address(es) associated to a hostname.

    CLI Example:

    .. code-block:: bash

            salt '*' phpipam.get HOSTNAME
    '''
    api = Api()
    resource = ('addresses/search_hostname_partial/{0}'
                .format(key))
    data = api.query(resource)

    ret = {}
    if not data:
        # The hostname has not been found in {php}IPAM
        return ret

    for entry in data:
        ipaddr   = entry.get('ip', None)
        hostname = entry.get('hostname', None)
        subnetId = entry.get('subnetId', None)
        if ipaddr and subnetId and hostname == key:
            subnet = api.query('subnets/{0}'.format(subnetId))
            if not subnet:
                continue

            subnet_netmask = (
                subnet.get('calculation', {}).get('Subnet netmask'))
            subnet_description = subnet.get('description')

            ret[str(data.index(entry))] = {
                'ipv4': ipaddr,
                'netmask': subnet_netmask,
                'description': subnet_description,
                'subnet_id': subnetId
            }

    return ret

def get_tags():
    '''
    Query a {php}IPAM server to get the list of all tags.

    CLI Example:

    .. code-block:: bash

            salt '*' phpipam.get_tags
    '''
    api = Api()
    resource = 'addresses/tags/'
    return api.query(resource)

def get_tag_id(tag):
    '''
    Query a {php}IPAM server to get the tag ID that corresponds to
    a given tag.

    CLI Example:

    .. code-block:: bash

            salt '*' phpipam.get_tag_id Offline
    '''
    for entry in get_tags():
        entry_type = entry.get('type', None)
        if entry_type == tag:
            return {
                'tag': tag,
                'tag_id': entry.get('id', None)
            }

    return {}

def get_addrs_by_tag(tag, exclude_gateway=False):
    '''
    Query a {php}IPAM server to get the IP addreses that corresponds to
    a given tag.
    The IP addreses of the hosts tagged as gateway can be expluded
    by setting exclude_gateway as True.

    CLI Example:

    .. code-block:: bash

            salt '*' phpipam.get_addrs_by_tag_id Offline
            salt '*' phpipam.get_addrs_by_tag_id Used True
    '''
    data = get_tag_id(tag)
    tag_id = data.get('tag_id', None)
    if not tag_id:
        return {}

    api = Api()
    resource = ('addresses/tags/{0}/addresses/'
                .format(tag_id))
    data = api.query(resource)

    is_valid = lambda data: (True if not exclude_gateway
                             else (data and not data.get('is_gateway', None)))
    details = {}
    ip_addrs = []

    for entry in data:
        ip_addr = entry.get('ip')
        if is_valid(entry):
            details[ip_addr] = {
                'description': entry.get('description'),
                'hostname': entry.get('hostname'),
                'is_gateway': entry.get('is_gateway')
            }
            ip_addrs.append(entry.get('ip'))

    return {
        'details': details,
        'ip_addrs': ip_addrs,
        'tag': tag
    }
