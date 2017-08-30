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

import time

from oslo_log import log as logging
from tempest.lib import exceptions as lib_exc

from oswin_tempest_plugin.clients import wsman
from oswin_tempest_plugin import config
from oswin_tempest_plugin import exceptions
from oswin_tempest_plugin.tests._mixins import migrate
from oswin_tempest_plugin.tests._mixins import resize
from oswin_tempest_plugin.tests import test_base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class HyperVClusterTest(migrate._MigrateMixin,
                        migrate._LiveMigrateMixin,
                        resize._ResizeMixin,
                        test_base.TestBase):

    """The test suite for the Hyper-V Cluster.

    This test suite will test the functionality of the Hyper-V Cluster Driver
    in OpenStack. The tests will force a failover on its newly created
    instance, and asserts the following:

    * the instance moves to another host.
    * the nova instance's host is properly updated.
    * the instance's network connection still works.
    * different nova operations can be performed properly.

    This test suite relies on the fact that there are at least 2 compute nodes
    available, that they are clustered, and have WSMan configured.

    The test suite contains the following tests:

    * test_check_clustered_vm
    * test_check_migration
    * test_check_resize
    * test_check_resize_negative
    """

    _BIGGER_FLAVOR = {'disk': 1}

    @classmethod
    def skip_checks(cls):
        super(HyperVClusterTest, cls).skip_checks()

        # check if the cluster Tests can be run.
        if not CONF.hyperv.cluster_enabled:
            msg = 'Hyper-V cluster tests are disabled.'
            raise cls.skipException(msg)

        if not CONF.hyperv_host_auth.username:
            msg = ('No Hyper-V host username has been provided. '
                   'Skipping cluster tests.')
            raise cls.skipException(msg)

        if not CONF.compute.min_compute_nodes >= 2:
            msg = 'Expected at least 2 compute nodes.'
            raise cls.skipException(msg)

    def _failover_server(self, server_name, host_ip):
        """Triggers the failover for the given server on the given host."""

        resource_name = "Virtual Machine %s" % server_name
        cmd = "Test-ClusterResourceFailure -Name '%s'" % resource_name
        # NOTE(claudiub): we issue the failover command twice, because on
        # the first failure, the Hyper-V Cluster will prefer the current
        # node, and will try to reactivate the VM on the it, and it will
        # succeed. On the 2nd failure, the VM will failover to another
        # node. Also, there needs to be a delay between commands, so the
        # original failover has time to finish.
        wsman.run_hv_host_wsman_ps(host_ip, cmd)
        time.sleep(CONF.hyperv.failover_sleep_interval)
        wsman.run_hv_host_wsman_ps(host_ip, cmd)

    def _wait_for_failover(self, server, original_host):
        """Waits for the given server to failover to another host.

        :raises TimeoutException: if the given server did not failover to
            another host within the configured "CONF.hyperv.failover_timeout"
            interval.
        """
        LOG.debug('Waiting for server %(server)s to failover from '
                  'compute node %(host)s',
                  dict(server=server['id'], host=original_host))

        start_time = int(time.time())
        timeout = CONF.hyperv.failover_timeout
        while True:
            elapsed_time = int(time.time()) - start_time
            admin_server = self._get_server_as_admin(server)
            current_host = admin_server['OS-EXT-SRV-ATTR:host']
            if current_host != original_host:
                LOG.debug('Server %(server)s failovered from compute node '
                          '%(host)s in %(seconds)s seconds.',
                          dict(server=server['id'], host=original_host,
                               seconds=elapsed_time))
                return

            if elapsed_time >= timeout:
                msg = ('Server %(server)s did not failover in the given '
                       'amount of time (%(timeout)s s).')
                raise lib_exc.TimeoutException(
                    msg % dict(server=server['id'], timeout=timeout))

            time.sleep(CONF.hyperv.failover_sleep_interval)

    def _get_hypervisor(self, hostname):
        hypervisors = self.admin_hypervisor_client.list_hypervisors(
            detail=True)['hypervisors']
        hypervisor = [h for h in hypervisors if
                      h['hypervisor_hostname'] == hostname]

        if not hypervisor:
            raise exceptions.NotFoundException(resource=hostname,
                                               res_type='hypervisor')
        return hypervisor[0]

    def _create_server(self, flavor=None):
        server_tuple = super(HyperVClusterTest, self)._create_server(flavor)
        server = server_tuple.server
        admin_server = self._get_server_as_admin(server)

        server_name = admin_server['OS-EXT-SRV-ATTR:instance_name']
        hostname = admin_server['OS-EXT-SRV-ATTR:host']
        host_ip = self._get_hypervisor(hostname)['host_ip']

        self._failover_server(server_name, host_ip)
        self._wait_for_failover(server, hostname)

        return server_tuple

    def test_clustered_vm(self):
        server_tuple = self._create_server()
        self._check_scenario(server_tuple)
