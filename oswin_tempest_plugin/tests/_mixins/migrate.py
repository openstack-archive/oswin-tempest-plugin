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

from tempest.common import waiters
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
        self._check_scenario(server_tuple)


class _LiveMigrateMixin(object):
    """Live migration mixin.

    This mixin will add a live migration test. It will perform the
    following operations:

    * Spawn instance.
    * Live migrate the instance.
    * Check the server connectivity.
    """

    # TODO(amuresan): Different mixins may be used at the same time.
    #                 Each of them may override some fields such as
    #                 'max_microversion'. This has to be sorted out.
    max_microversion = '2.24'

    def _live_migrate_server(self, server_tuple, destination_host=None,
                             state='ACTIVE', volume_backed=False):
        server = server_tuple.server
        admin_server = self._get_server_as_admin(server)
        current_host = admin_server['OS-EXT-SRV-ATTR:host']

        block_migration = (CONF.compute_feature_enabled.
                           block_migration_for_live_migration and
                           not volume_backed)

        self.admin_servers_client.live_migrate_server(
            server['id'],
            host=destination_host,
            block_migration=block_migration,
            disk_over_commit=False)

        waiters.wait_for_server_status(self.admin_servers_client, server['id'],
                                       state)

        admin_server = self._get_server_as_admin(server)
        after_migration_host = admin_server['OS-EXT-SRV-ATTR:host']

        migration_list = (self.admin_migrations_client.list_migrations()
                          ['migrations'])

        msg = ("Live Migration failed. Migrations list for Instance "
               "%s: [" % server['id'])
        for live_migration in migration_list:
            if live_migration['instance_uuid'] == server['id']:
                msg += "\n%s" % live_migration
        msg += "]"

        if destination_host:
            self.assertEqual(destination_host, after_migration_host, msg)
        else:
            self.assertNotEqual(current_host, after_migration_host, msg)

    @testtools.skipUnless(CONF.compute_feature_enabled.live_migration,
                          'Live migration option enabled.')
    def test_live_migration(self):
        server_tuple = self._create_server()
        self._live_migrate_server(server_tuple)
        self._check_scenario(server_tuple)
