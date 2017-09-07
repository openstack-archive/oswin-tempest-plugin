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


class RemoteFxTestCase(optional_feature._OptionalFeatureMixin,
                       test_base.TestBase):
    """RemoteFX test suite.

    This test suit will spawn instances with RemoteFX enabled.
    """

    # RemoteFX is supported in Windows / Hyper-V Server 2012 R2 and newer.
    _MIN_HYPERV_VERSION = 6003

    _FEATURE_FLAVOR = {'extra_specs': {'os_resolution': '1920x1200',
                                       'os_monitors': '1',
                                       'os_vram': '1024'}}

    @classmethod
    def skip_checks(cls):
        super(RemoteFxTestCase, cls).skip_checks()
        # the CONF.hyperv.remotefx_enabled config option needs to be enabled.
        if not CONF.hyperv.remotefx_enabled:
            msg = ('The config option "hyperv.remotefx_enabled" is False. '
                   'Skipping.')
            raise cls.skipException(msg)
