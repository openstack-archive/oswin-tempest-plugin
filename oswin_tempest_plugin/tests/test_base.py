# Copyright 2017 Cloudbase Solutions SRL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections

from oslo_log import log as logging
from tempest.common import compute
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
import tempest.test

from oswin_tempest_plugin import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


Server_tuple = collections.namedtuple(
    'Server_tuple',
    ['server', 'floating_ip', 'keypair', 'security_groups'])


class TestBase(tempest.test.BaseTestCase):
    """Base class for tests."""

    credentials = ['primary', 'admin']

    # Inheriting TestCases should change this version if needed.
    _MIN_HYPERV_VERSION = 6002

    # Inheriting TestCases should change this image ref if needed.
    _IMAGE_REF = CONF.compute.image_ref

    # Inheriting TestCases should change this flavor ref if needed.
    _FLAVOR_REF = CONF.compute.flavor_ref

    # Inheriting TestCases should change this ssh User if needed.
    _IMAGE_SSH_USER = CONF.validation.image_ssh_user

    # suffix to use for the newly created flavors.
    _FLAVOR_SUFFIX = ''

    @classmethod
    def skip_checks(cls):
        super(TestBase, cls).skip_checks()
        # check if the configured hypervisor_version is higher than
        # the test's required minimum Hyper-V version.

        # TODO(claudiub): instead of expecting a config option specifying
        # the hypervisor version, we could check nova's compute nodes for
        # their hypervisor versions.
        config_vers = CONF.hyperv.hypervisor_version
        if config_vers < cls._MIN_HYPERV_VERSION:
            msg = ('Configured hypervisor_version (%(config_vers)s) is not '
                   'supported. It must be higher than %(req_vers)s.' % {
                       'config_vers': config_vers,
                       'req_vers': cls._MIN_HYPERV_VERSION})
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(TestBase, cls).setup_clients()
        # Compute client
        cls.compute_fips_client = (
            cls.os_primary.compute_floating_ips_client)
        cls.keypairs_client = cls.os_primary.keypairs_client
        cls.servers_client = cls.os_primary.servers_client
        cls.admin_servers_client = cls.os_admin.servers_client
        cls.admin_flavors_client = cls.os_admin.flavors_client
        cls.admin_migrations_client = cls.os_admin.migrations_client
        cls.admin_hypervisor_client = cls.os_admin.hypervisor_client

        # Neutron network client
        cls.security_groups_client = (
            cls.os_primary.security_groups_client)
        cls.security_group_rules_client = (
            cls.os_primary.security_group_rules_client)

    def create_floating_ip(self, server):
        """Create a floating IP and associates to a server on Nova"""

        pool_name = CONF.network.floating_network_name
        floating_ip = (
            self.compute_fips_client.create_floating_ip(pool=pool_name))
        floating_ip = floating_ip['floating_ip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.compute_fips_client.delete_floating_ip,
                        floating_ip['id'])
        self.compute_fips_client.associate_floating_ip_to_server(
            floating_ip['ip'], server['id'])
        return floating_ip

    def create_keypair(self):
        name = data_utils.rand_name(self.__class__.__name__)
        body = self.keypairs_client.create_keypair(name=name)
        self.addCleanup(self.keypairs_client.delete_keypair, name)
        return body['keypair']

    def _get_image_ref(self):
        return self._IMAGE_REF

    def _flavor_cleanup(self, flavor_id):
        try:
            self.admin_flavors_client.delete_flavor(flavor_id)
            self.admin_flavors_client.wait_for_resource_deletion(flavor_id)
        except exceptions.NotFound:
            pass

    def _create_new_flavor(self, flavor_ref, flavor_updates):
        """Creates a new flavor based on the given flavor and flavor updates.

        :returns: the newly created flavor's ID.
        """
        flavor = self.admin_flavors_client.show_flavor(flavor_ref)['flavor']

        flavor_name = 'test_resize'
        if self._FLAVOR_SUFFIX:
            flavor_name += '_%s' % self._FLAVOR_SUFFIX

        new_flavor = self.admin_flavors_client.create_flavor(
            name=data_utils.rand_name(flavor_name),
            ram=flavor['ram'] + flavor_updates.get('ram', 0),
            disk=flavor['disk'] + flavor_updates.get('disk', 0),
            vcpus=flavor['vcpus'] + flavor_updates.get('vcpus', 0),
        )['flavor']

        self.addCleanup(self._flavor_cleanup, new_flavor['id'])

        # Add flavor extra_specs, if needed.
        extra_specs = flavor_updates.get('extra_specs')
        if extra_specs:
            self.admin_flavors_client.set_flavor_extra_spec(
                new_flavor['id'], **extra_specs)

        return new_flavor

    def _get_flavor_ref(self):
        return self._FLAVOR_REF

    def _create_server(self, flavor=None):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server.
        """
        clients = self.os_primary
        name = data_utils.rand_name(self.__class__.__name__ + "-server")
        image_id = self._get_image_ref()
        flavor = flavor or self._get_flavor_ref()
        keypair = self.create_keypair()
        tenant_network = self.get_tenant_network()
        security_group = self._create_security_group()
        # we need to pass the security group's name to the instance.
        sg_group_names = [{'name': security_group['name']}]

        body, _ = compute.create_test_server(
            clients, name=name,
            flavor=flavor,
            image_id=image_id,
            key_name=keypair['name'],
            tenant_network=tenant_network,
            security_groups=sg_group_names,
            wait_until='ACTIVE')

        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, body['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.servers_client.delete_server, body['id'])
        server = clients.servers_client.show_server(body['id'])['server']

        floating_ip = self.create_floating_ip(server)
        server_tuple = Server_tuple(
            server=server,
            keypair=keypair,
            floating_ip=floating_ip,
            security_groups=[security_group])

        return server_tuple

    def _get_server_as_admin(self, server):
        # only admins have access to certain instance properties.
        return self.admin_servers_client.show_server(
            server['id'])['server']

    def _create_security_group(self):
        sg_name = data_utils.rand_name(self.__class__.__name__)
        sg_desc = sg_name + " description"
        secgroup = self.security_groups_client.create_security_group(
            name=sg_name, description=sg_desc)['security_group']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.security_groups_client.delete_security_group,
            secgroup['id'])

        # Add rules to the security group
        self._create_loginable_secgroup_rule(secgroup)
        return secgroup

    def _create_loginable_secgroup_rule(self, secgroup):
        """Create loginable security group rule

        This function will create:
        1. egress and ingress tcp port 22 allow rule in order to allow ssh
        access for ipv4.
        3. egress and ingress ipv4 icmp allow rule, in order to allow icmpv4.
        """

        rulesets = [
            # ssh
            dict(protocol='tcp',
                 port_range_min=22,
                 port_range_max=22),
            # ping
            dict(protocol='icmp'),
        ]
        for ruleset in rulesets:
            for r_direction in ['ingress', 'egress']:
                ruleset['direction'] = r_direction
                self._create_security_group_rule(
                    secgroup, **ruleset)

    def _create_security_group_rule(self, secgroup, **kwargs):
        """Create a rule from a dictionary of rule parameters.

        Creates a rule in a secgroup.

        :param secgroup: the security group.
        :param kwargs: a dictionary containing rule parameters:
            for example, to allow incoming ssh:
            rule = {
                    direction: 'ingress'
                    protocol:'tcp',
                    port_range_min: 22,
                    port_range_max: 22
                    }
        """
        ruleset = dict(security_group_id=secgroup['id'],
                       tenant_id=secgroup['tenant_id'])
        ruleset.update(kwargs)

        sec_group_rules_client = self.security_group_rules_client
        sg_rule = sec_group_rules_client.create_security_group_rule(**ruleset)
        sg_rule = sg_rule['security_group_rule']

        return sg_rule

    def _wait_for_server_status(self, server, status='ACTIVE'):
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       status)

    def _get_server_client(self, server_tuple):
        """Get a SSH client to a remote server

        :returns: RemoteClient object
        """
        server = server_tuple.server
        ip_address = server_tuple.floating_ip['ip']
        private_key = server_tuple.keypair['private_key']

        # ssh into the VM
        username = self._IMAGE_SSH_USER
        linux_client = remote_client.RemoteClient(
            ip_address, username, pkey=private_key, password=None,
            server=server, servers_client=self.servers_client)
        linux_client.validate_authentication()

        return linux_client

    def _check_server_connectivity(self, server_tuple):
        # if server connectivity works, an SSH client can be opened.
        self._get_server_client(server_tuple)

    def _check_scenario(self, server_tuple):
        # NOTE(claudiub): This method is to be used when verifying a
        # particular scenario. If a scenario test case needs to perform
        # different validation steps (e.g.: metrics collection), it should
        # overwrite this method.
        self._check_server_connectivity(server_tuple)
