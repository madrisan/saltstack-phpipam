# SaltStack Extension Module for {php}IPAM

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/fcd8aa3c6a034c519ea795c892c5424c)](https://www.codacy.com/app/madrisan/saltstack-phpipam?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=madrisan/saltstack-phpipam&amp;utm_campaign=Badge_Grade)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://spdx.org/licenses/Apache-2.0.html)

![](images/phpipam_logo.png?raw=true)

A SaltStack extension module for interacting with a
[{php}IPAM](https://phpipam.net/), an open-source web IP address management application (IPAM).

This module requires a configuration profile to be configured in either the minion or, as in our implementation, in the master configuration file (`/etc/salt/master.d/phpipam.conf`).

This profile requires very little:

    phpipam:
      url: https://ipam.mydomain.com
      auth:
        user: 'read_api_user'
        password: 'xxxxx'

Where `url` is the URL of the *phpipam* server and `auth.user` and `auth.password` the credential of a user account created in the *phpipam* application. If authentication is successfull, an API token will be received and transparently included in the header of all the API requests.

This Python module should be saved as `salt/_modules/phpipam.py`.

## API documentation

URL: <https://phpipam.net/api/api_documentation/>

## Implemented Methods

### phpimap.get

Query a *phpipam* server to get the IP address(es) associated to a *hostname*.
An optional CIDR can be set. In this case only the address(es) that belong to this network will be returned.

    salt '*' phpipam.get HOSTNAME
    salt '*' phpipam.get HOSTNAME 10.0.20.0/24

### phpimap.get_tags

Query a *phpipam* server to get the list of all tags.

    salt '*' phpipam.get_tags

### get_tag_id

Query a *phpipam* server to get the tag ID that corresponds to a given *tag*.

    salt '*' phpipam.get_tag_id Offline

### get_addrs_by_tag

Query a *phpipam* server to get the IP addreses that corresponds to a given *tag*.
The IP addreses of the hosts tagged as gateway can be expluded by setting *exclude_gateway* as *True*.

    salt '*' phpipam.get_addrs_by_tag_id Offline
    salt '*' phpipam.get_addrs_by_tag_id Used True
