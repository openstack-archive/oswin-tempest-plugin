# Copyright 2017 Cloudbase Solutions
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

try:
    # NOTE(claudiub): ceilometer might not be installed, it is not mandatory.
    from ceilometer.tests.tempest.service import client as telemetry_client
except Exception:
    telemetry_client = None

from oslo_log import log as logging
from tempest import clients

from oswin_tempest_plugin import config
from oswin_tempest_plugin.tests import test_base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ClientManager(clients.Manager):

    def __init__(self, *args, **kwargs):
        super(ClientManager, self).__init__(*args, **kwargs)

        self._set_telemetry_clients()

    def _set_telemetry_clients(self):
        self.telemetry_client = telemetry_client.TelemetryClient(
            self.auth_provider, **telemetry_client.Manager.telemetry_params)


class MetricsCollectionTestCase(test_base.TestBase):
    """Adds metrics collection scenario tests.

    This test suite verifies that the instance metrics are properly published
    and collected and have non-zero values. The verification is done via the
    ceilometer API.

    setup:
        1. spins a new instance.
        2. waits until the instance was created succesfully (ACTIVE status).
        3. wait an interval of time which represents the polling period of the
        ceilometer-polling agent.

    Waiting for the ceilometer-polling agent to poll the resources is crucial,
    otherwise the test suite will fail due to the fact that no samples
    would be found published before checking the samples.

    The test suite's polled_metrics_delay must have a greater value than the
    ceilometer agent's polling interval. This can be done in two ways:
        a. Configure tempest's polled_metric_delay, by adding the
        following line in tempest.conf, in the hyperv section:
        polled_metrics_delay = <desired value>
        b. Set the interval value in pipeline.yaml on the compute node to
        the desired value and restart the ceilometer polling agent. The
        interval value is set either for the 'meter_source' or for each
        of the following: 'cpu_source', 'disk_source', 'network_source'.

    Note: If the polled_metrics_delay value is too low, the tests might not
    find any samples and fail because of this. As a recommandation,
    polled_metrics_delay's value should be:
        polled_metric_delay = <pipeline.yaml interval value> + <15-20 seconds>

    tests:
        1. test_metrics - tests values for the following metrics:
            - cpu
            - network.outgoing.bytes
            - disk.read.bytes

    assumptions:
        1. Ceilometer agent on the compute node is running.
        2. Ceilometer agent on the compute node has the polling interval
        defined in pipeline.yaml lower than the polled_metrics_delay defined
        in this test suite.
        3. The compute nodes' nova-compute and neutron-hyperv-agent services
        have been configured to enable metrics collection.
    """

    client_manager = ClientManager

    @classmethod
    def skip_checks(cls):
        super(MetricsCollectionTestCase, cls).skip_checks()

        if (not CONF.service_available.ceilometer or
                not CONF.telemetry.deprecated_api_enabled):
            raise cls.skipException("Ceilometer API support is required.")

        if not CONF.hyperv.collected_metrics:
            raise cls.skipException("Collected metrics not configured.")

    @classmethod
    def setup_clients(cls):
        super(MetricsCollectionTestCase, cls).setup_clients()

        # Telemetry client
        cls.telemetry_client = cls.os_primary.telemetry_client

    def _telemetry_check_samples(self, resource_id, meter_name):
        LOG.info("Checking %(meter_name)s for resource %(resource_id)s" % {
            'meter_name': meter_name, 'resource_id': resource_id})

        samples = self.telemetry_client.list_samples(meter_name)
        self.assertNotEmpty(samples,
                            'Telemetry client returned no samples.')

        resource_samples = [s for s in samples if
                            s['resource_id'] == resource_id]
        self.assertNotEmpty(
            resource_samples,
            'No meter %(meter_name)s samples for resource '
            '%(resource_id)s found.' % {'meter_name': meter_name,
                                        'resource_id': resource_id})

        non_zero_valued_samples = [s for s in resource_samples if
                                   s['counter_volume'] > 0]
        self.assertNotEmpty(
            non_zero_valued_samples,
            'All meter %(meter_name)s samples for resource '
            '%(resource_id)s are 0.' % {'meter_name': meter_name,
                                        'resource_id': resource_id})

    def _get_instance_cpu_resource_id(self, server):
        return server['id']

    def _get_instance_disk_resource_id(self, server):
        return server['id']

    def _get_instance_port_resource_id(self, server):
        # Note(claudiub): the format for the instance_port_resource_id is:
        # %(OS-EXT-SRV-ATTR:instance_name)s-%(instance_id)s-%(port_id)s
        # the instance returned by self.servers_client does not contain the
        # OS-EXT-SRV-ATTR:instance_name field. Which means that the resource_id
        # must be found in ceilometer's resources.
        start_res_id = server['id']
        resources = self.telemetry_client.list_resources()
        res_ids = [r['resource_id'] for r in resources
                   if r['resource_id'].startswith('instance-') and
                   start_res_id in r['resource_id']]

        self.assertEqual(1, len(res_ids))
        return res_ids[0]

    def _check_scenario(self, server_tuple):
        server = server_tuple.server
        LOG.info("Waiting %s seconds for the ceilometer compute agents to "
                 "publish the samples.", CONF.hyperv.polled_metrics_delay)
        time.sleep(CONF.hyperv.polled_metrics_delay)

        # TODO(claudiub): Add more metrics.

        if 'cpu' in CONF.hyperv.collected_metrics:
            cpu_res_id = self._get_instance_cpu_resource_id(server)
            self._telemetry_check_samples(cpu_res_id, 'cpu')

        if 'network.outgoing.bytes' in CONF.hyperv.collected_metrics:
            port_res_id = self._get_instance_port_resource_id(server)
            self._telemetry_check_samples(port_res_id,
                                          'network.outgoing.bytes')

        if 'disk.read.bytes' in CONF.hyperv.collected_metrics:
            disk_resource_id = self._get_instance_disk_resource_id(server)
            self._telemetry_check_samples(disk_resource_id, 'disk.read.bytes')

    def test_metrics(self):
        server_tuple = self._create_server()
        self._check_scenario(server_tuple)
