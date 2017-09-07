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

from oswin_tempest_plugin import config
from oswin_tempest_plugin.tests._mixins import optional_feature
from oswin_tempest_plugin.tests import test_base

CONF = config.CONF


class SecureBootTestCase(optional_feature._OptionalFeatureMixin,
                         test_base.TestBase):
    """Secure boot test suite.

    This test suite will spawn instances requiring secure boot to be
    enabled.

    This test suite will require a Generation 2 VHDX image, with a
    Linux guest OS (it tests connectivity via SSH).

    The configured image must contain the following properties:
    * os_type=linux
    * hw_machine_type=hyperv-gen2

    Hyper-V Secure Boot was first introduced in Windows / Hyper-V Server 2012
    R2, but support for Linux guests was introduced in Windows / Hyper-V
    Server 2016, which is why this test suite will require compute nodes
    with the OS version 10.0 or newer.
    """

    _MIN_HYPERV_VERSION = 10000

    # NOTE(amuresan):Images supporting secure boot usually require more disk
    #                space. We're trying to use the largest of the configured
    #                flavors.

    _FLAVOR_REF = CONF.compute.flavor_ref_alt
    _IMAGE_REF = CONF.hyperv.secure_boot_image_ref
    _IMAGE_SSH_USER = CONF.hyperv.secure_boot_image_ssh_user
    _FEATURE_FLAVOR = {'extra_specs': {'os:secure_boot': 'required'}}

    # TODO(amuresan): the secure_boot_image_ref should be reused in
    # more than one test case so we don't have to add a different
    # image for every test.

    @classmethod
    def skip_checks(cls):
        super(SecureBootTestCase, cls).skip_checks()
        # check if the needed image ref has been configured.
        if not cls._IMAGE_REF:
            msg = ('The config option "hyperv.secure_boot_image_ref" '
                   'has not been set. Skipping secure boot tests.')
            raise cls.skipException(msg)

        if not cls._IMAGE_SSH_USER:
            msg = ('The config option "hyperv.secure_boot_image_ssh_user" '
                   'has not been set. Skipping.')
            raise cls.skipException(msg)
