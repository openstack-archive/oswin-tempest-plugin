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

from tempest.lib import exceptions


class ResizeException(exceptions.TempestException):
    message = ("Server %(server_id)s failed to resize to the given "
               "flavor %(flavor)s")


class NotFoundException(exceptions.TempestException):
    message = "Resource %(resource)s (%(res_type)s) was not found."


class WSManException(exceptions.TempestException):
    message = ('Command "%(cmd)s" failed on host %(host)s failed with the '
               'return code %(return_code)s. std_out: %(std_out)s, '
               'std_err: %(std_err)s')
