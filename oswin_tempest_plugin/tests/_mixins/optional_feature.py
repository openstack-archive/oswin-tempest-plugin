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
from oswin_tempest_plugin.tests._mixins import resize

CONF = config.CONF


class _OptionalFeatureMixin(resize._ResizeUtils):
    """Optional Feature mixin.

    Some features are optional, and can be turned on / off through resize
    with certain flavors.
    Examples of optional features: vNUMA, QoS, SR-IOV, PCI passthrough,
    RemoteFX.

    This mixin will add the following tests:
    * test_feature
    * test_resize_add_feature
    * test_resize_remove_feature

    The resize tests will create a new instance, resize it to a new flavor (
    turning on / off the optional feature), and check its network
    connectivity.

    The optional feature flavor is based on the test suite's configured
    _FLAVOR_REF (typically compute.flavor_ref or compute.flavor_ref_alt),
    with some updates. For example, if the vNUMA configuration is to be tested,
    the new flavor would contain the flavor extra_spec {'hw:numa_nodes="1"'}.
    Keep in mind that all the extra_spec keys and values have to be strings.
    """

    # NOTE(claudiub): This flavor dict contains updates to the base flavor
    # tempest is configured with. For example, _FEATURE_FLAVOR can be:
    # _BIGGER_FLAVOR = {'extra_specs': {'hw:numa_nodes': 1'}}
    # which means a flavor having that flavor extra_spec will be created, and
    # a created instance will be resize to / from it.

    _FEATURE_FLAVOR = {}

    def _get_flavor_ref(self):
        """Gets a new optional feature flavor ref.

        Creates a new flavor based on the test suite's configured _FLAVOR_REF,
        with some updates specific to the optional feature.

        :returns: nova flavor ID.
        """
        # NOTE(claudiub): Unless explicitly given another flavor,
        # _create_server will call this method to get the flavor reference
        # needed to spawn a new instance. Thus, any other test will spawn
        # instances with this Optional Feature.
        new_flavor = self._create_new_flavor(self._FLAVOR_REF,
                                             self._FEATURE_FLAVOR)
        return new_flavor['id']

    def test_feature(self):
        server_tuple = self._create_server()
        self._check_scenario(server_tuple)

    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    def test_resize_add_feature(self):
        new_flavor = self._get_flavor_ref()
        self._check_resize(new_flavor, self._FLAVOR_REF)

    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    def test_resize_remove_feature(self):
        new_flavor = self._get_flavor_ref()
        self._check_resize(self._FLAVOR_REF, new_flavor)
