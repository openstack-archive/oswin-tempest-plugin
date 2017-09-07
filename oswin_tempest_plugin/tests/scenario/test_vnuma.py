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

import testtools

from oswin_tempest_plugin import config
from oswin_tempest_plugin.tests._mixins import migrate
from oswin_tempest_plugin.tests._mixins import optional_feature
from oswin_tempest_plugin.tests._mixins import resize
from oswin_tempest_plugin.tests import test_base

CONF = config.CONF


class HyperVvNumaTestCase(migrate._MigrateMixin,
                          migrate._LiveMigrateMixin,
                          optional_feature._OptionalFeatureMixin,
                          resize._ResizeMixin,
                          resize._ResizeNegativeMixin,
                          test_base.TestBase):
    """Hyper-V vNUMA test suite.

    This test suite will spawn instances requiring NUMA placement.
    """

    _FEATURE_FLAVOR = {'extra_specs': {'hw:numa_nodes': '1'}}
    _BIGGER_FLAVOR = {'ram': 128, 'extra_specs': {'hw:numa_nodes': '1'}}

    # NOTE(claudiub): Hyper-V does not support asymmetric NUMA topologies.
    # The resize should fail in this case.
    _BAD_FLAVOR = {'ram': 64, 'extra_specs': {
        'hw:numa_nodes': '2', 'hw:numa_mem.0': '64', 'hw:numa_cpus.0': '0'}}

    @testtools.skipUnless(CONF.hyperv.available_numa_nodes > 1,
                          'At least 2 NUMA nodes are required.')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    def test_resize_negative(self):
        new_flavor = self._create_new_flavor(self._get_flavor_ref(),
                                             self._BAD_FLAVOR)

        # NOTE(claudiub): all NUMA nodes have to be properly defined.
        vcpus = [i for i in range(1, int(new_flavor['vcpus']))]
        extra_specs = {'hw:numa_mem.1': str(int(new_flavor['ram']) - 64),
                       'hw:numa_cpus.1': ','.join(vcpus)}
        self.admin_flavors_client.set_flavor_extra_spec(
            new_flavor['id'], **extra_specs)

        self._check_resize(new_flavor['id'], expected_fail=True)
