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
from oswin_tempest_plugin.tests._mixins import resize
from oswin_tempest_plugin.tests import test_base

CONF = config.CONF


class _BaseDiskTestMixin(migrate._MigrateMixin,
                         resize._ResizeMixin,
                         resize._ResizeNegativeMixin):
    """Image types / formats test suite.

    This test suite will spawn instances with a configured image and will
    check their network connectivity. The purpose of this test suite is to
    cover different image formats and types (VHD, VHDX, Generation 2 VMs).
    """

    _CONF_OPTION_NAME = ''

    _BIGGER_FLAVOR = {'disk': 1}
    _BAD_FLAVOR = {'disk': -1}

    @classmethod
    def skip_checks(cls):
        super(_BaseDiskTestMixin, cls).skip_checks()
        # check if the needed image ref has been configured.
        if not cls._IMAGE_REF:
            msg = ('The config option "%s" has not been set. Skipping.' %
                   cls._CONF_OPTION_NAME)
            raise cls.skipException(msg)

    def test_disk(self):
        server_tuple = self._create_server()
        self._check_scenario(server_tuple)

    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    def test_resize_negative(self):
        # NOTE(claudiub): This test will try to downsize a VM's disk, which is
        # unsupported. The configured flavor might have disk set to 1GB.
        # The nova-api does not allow disks to be resized on 0 GB.
        flavor = self._get_flavor_ref()
        new_flavor = self._create_new_flavor(flavor, self._BIGGER_FLAVOR)
        self._check_resize(flavor, new_flavor['id'], expected_fail=True)


class VhdDiskTest(_BaseDiskTestMixin, test_base.TestBase):

    _IMAGE_REF = CONF.hyperv.vhd_image_ref
    _CONF_OPTION_NAME = 'hyperv.vhd_image_ref'
    _FLAVOR_SUFFIX = 'vhd'

    # TODO(claudiub): validate that the images really are VHD / VHDX.


class VhdxDiskTest(_BaseDiskTestMixin, test_base.TestBase):

    _IMAGE_REF = CONF.hyperv.vhdx_image_ref
    _CONF_OPTION_NAME = 'hyperv.vhdx_image_ref'
    _FLAVOR_SUFFIX = 'vhdx'


class Generation2DiskTest(_BaseDiskTestMixin, test_base.TestBase):

    # Generation 2 VMs have been introduced in Windows / Hyper-V Server 2012 R2
    _MIN_HYPERV_VERSION = 6003

    _IMAGE_REF = CONF.hyperv.gen2_image_ref
    _CONF_OPTION_NAME = 'hyperv.gen2_image_ref'
    _FLAVOR_SUFFIX = 'gen2'

    # TODO(claudiub): Add validation that the given gen2_image_ref really has
    # the 'hw_machine_type=hyperv-gen2' property.
