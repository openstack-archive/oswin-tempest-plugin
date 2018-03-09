# Copyright 2018 Cloudbase Solutions Srl
#
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

from oslo_serialization import jsonutils as json
from tempest.lib.common import rest_client

from oswin_tempest_plugin import config

CONF = config.CONF


class GnocchiClient(rest_client.RestClient):

    uri_prefix = 'v1'

    def deserialize(self, body):
        return json.loads(body.replace("\n", ""))

    def _helper_list(self, uri):
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyList(resp, body)

    def list_resources(self):
        uri = '%s/resource/generic' % self.uri_prefix
        return self._helper_list(uri)

    def list_samples(self, resource_id, meter_name):
        """Returns a list of samples for the given resource and meter.

        :returns: list, each item being a list containing the following values
            in this order: timestamp, granularity, value.
        """
        uri = '%s/resource/generic/%s/metric/%s/measures' % (
            self.uri_prefix, resource_id, meter_name)
        return self._helper_list(uri)
