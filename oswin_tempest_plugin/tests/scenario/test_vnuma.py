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

from oswin_tempest_plugin.tests._mixins import migrate
from oswin_tempest_plugin.tests._mixins import optional_feature
from oswin_tempest_plugin.tests._mixins import resize
from oswin_tempest_plugin.tests import test_base


class HyperVvNumaTestCase(test_base.TestBase,
                          migrate._MigrateMixin,
                          optional_feature._OptionalFeatureMixin,
                          resize._ResizeMixin):
    """Hyper-V vNUMA test suite.

    This test suite will spawn instances requiring NUMA placement.
    """

    _FEATURE_FLAVOR = {'extra_specs': {'hw:numa_nodes': '1'}}
    _BIGGER_FLAVOR = {'ram': 128, 'extra_specs': {'hw:numa_nodes': '1'}}

    # NOTE(claudiub): Hyper-V does not support asymmetric NUMA topologies.
    _FEATURE_FLAVOR = {'ram': '128', 'extra_specs': {
        'hw:numa_nodes': '2', 'hw:numa_mem.0': '128'}}
