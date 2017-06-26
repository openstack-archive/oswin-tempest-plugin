# Copyright 2013 Cloudbase Solutions Srl
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

from oslo_log import log as logging
from winrm import protocol

from oswin_tempest_plugin import exceptions

LOG = logging.getLogger(__name__)

protocol.Protocol.DEFAULT_TIMEOUT = "PT3600S"


def run_wsman_cmd(host, username, password, cmd, fail_on_error=False):
    url = 'https://%s:5986/wsman' % host
    LOG.debug('Connecting to: %s', host)
    p = protocol.Protocol(endpoint=url,
                          transport='plaintext',
                          server_cert_validation='ignore',
                          username=username,
                          password=password)

    shell_id = p.open_shell()
    LOG.debug('Running command on host %(host)s: %(cmd)s',
              {'host': host, 'cmd': cmd})
    command_id = p.run_command(shell_id, cmd)
    std_out, std_err, return_code = p.get_command_output(shell_id, command_id)

    p.cleanup_command(shell_id, command_id)
    p.close_shell(shell_id)

    LOG.debug('Results from %(host)s: return_code: %(return_code)s, std_out: '
              '%(std_out)s, std_err: %(std_err)s',
              {'host': host, 'return_code': return_code, 'std_out': std_out,
               'std_err': std_err})

    if fail_on_error and return_code:
        raise exceptions.WSManException(
            cmd=cmd, host=host, return_code=return_code,
            std_out=std_out, std_err=std_err)

    return (std_out, std_err, return_code)


def run_wsman_ps(host, username, password, cmd, fail_on_error=False):
    cmd = ("powershell -NonInteractive -ExecutionPolicy RemoteSigned "
           "-Command \"%s\"" % cmd)
    return run_wsman_cmd(host, username, password, cmd, fail_on_error)
