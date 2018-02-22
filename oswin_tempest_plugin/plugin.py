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

import os

from tempest import config
from tempest.test_discover import plugins

from oswin_tempest_plugin import config as project_config


class OSWinTempestPlugin(plugins.TempestPlugin):
    def load_tests(self):
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "oswin_tempest_plugin/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        """Add additional configuration options to tempest.

        This method will be run for the plugin during the register_opts()
        function in tempest.config

        :param conf: The conf object that can be used to register additional
            config options on.
        """

        for config_opt_group, config_opts in project_config.list_opts():
            config.register_opt_group(conf, config_opt_group, config_opts)

    def get_opt_lists(self):
        """Get a list of options for sample config generation.

        :return: A list of tuples with the group name and options in that
            group.
        :return type: list
        """
        return [(group.name, opts)
                for group, opts in project_config.list_opts()]

    def get_service_clients(self):
        metric_config = config.service_client_config('metric')
        metric_v1_params = {
            'name': 'metric_v1',
            'service_version': 'metric.v1',
            'module_path': 'oswin_tempest_plugin.services.gnocchi_client',
            'client_names': ['GnocchiClient'],
        }
        metric_v1_params.update(metric_config)

        return [metric_v1_params]
