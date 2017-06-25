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

CONF = config.CONF


class _MigrateMixin(object):
    """Cold migration mixin.

    This mixin will add a cold migration test. It will perform the
    following operations:

    * Spawn instance.
    * Cold migrate the instance.
    * Check the server connectivity.
    """

    def _migrate_server(self, server_tuple):
        server = server_tuple.server
        self.admin_servers_client.migrate_server(server['id'])
        self._wait_for_server_status(server, 'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])

    @testtools.skipUnless(CONF.compute.min_compute_nodes >= 2,
                          'Expected at least 2 compute nodes.')
    def test_migration(self):
        server_tuple = self._create_server()
        self._migrate_server(server_tuple)
        self._check_server_connectivity(server_tuple)
