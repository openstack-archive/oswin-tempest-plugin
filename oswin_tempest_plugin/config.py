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

from oslo_config import cfg
from oslo_config import types
from tempest import config

CONF = config.CONF


hyperv_group = cfg.OptGroup(name='hyperv',
                            title='Hyper-V Driver Tempest Options')

HyperVGroup = [
    cfg.IntOpt('hypervisor_version',
               default=0,
               help="Compute nodes' hypervisor version, used to determine "
                    "which tests to run. It must have following value: "
                    "major_version * 1000 + minor_version"
                    "For example, Windows / Hyper-V Server 2012 R2 would have "
                    "the value 6003"),
    cfg.StrOpt('vhd_image_ref',
               help="Valid VHD image reference to be used in tests."),
    cfg.StrOpt('vhdx_image_ref',
               help="Valid VHDX image reference to be used in tests."),
    cfg.StrOpt('gen2_image_ref',
               help="Valid Generation 2 VM VHDX image reference to be used "
                    "in tests."),
    cfg.StrOpt('secure_boot_image_ref',
               help="Valid secure boot VM VHDX image reference to be used "
                    "in tests."),
    cfg.StrOpt('secure_boot_image_ssh_user',
               help='User for secure boot image to be used in tests.'),
    cfg.BoolOpt('cluster_enabled',
                default=False,
                help="The compute nodes are joined into a Hyper-V Cluster."),
    cfg.IntOpt('failover_timeout',
               default=120,
               help='The maximum amount of time to wait for a failover to '
                    'occur.'),
    cfg.IntOpt('failover_sleep_interval',
               default=5,
               help='The amount of time to wait between failover checks.'),
    cfg.BoolOpt('remotefx_enabled',
                default=False,
                help="RemoteFX feature is enabled and supported on the "
                     "compute nodes."),
    cfg.IntOpt('available_numa_nodes',
               default=1,
               help="The maximum number of NUMA cells the compute nodes "
                    "have. If it's less than 2, resize negative tests for "
                    "vNUMA will be skipped."),
    cfg.ListOpt('collected_metrics',
                item_type=types.String(
                    choices=('cpu', 'network.outgoing.bytes',
                             'disk.read.bytes')),
                default=[],
                help="The ceilometer metrics to check. If this config value "
                     "is empty, the telemetry tests are skipped. This config "
                     "option assumes that the compute nodes are configured "
                     "and capable of collecting ceilometer metrics. WARNING: "
                     "neutron-ovs-agent is not capable of enabling network "
                     "metrics collection."),
    cfg.IntOpt('polled_metrics_delay',
               default=620,
               help="The number of seconds to wait for the metrics to be "
                    "published by the compute node's ceilometer-polling "
                    "agent. The value must be greater by ~15-20 seconds "
                    "than the agent's publish interval, defined in its "
                    "pipeline.yaml file (typically, the intervals are 600 "
                    "seconds)."),
]

hyperv_host_auth_group = cfg.OptGroup(name='hyperv_host_auth',
                                      title='Hyper-V host '
                                            'authentication options')

hyperv_host_auth_opts = [
    cfg.StrOpt('username',
               help="The username of the Hyper-V hosts."),
    cfg.StrOpt('password',
               secret=True,
               help='The password of the Hyper-V hosts.'),
    cfg.StrOpt('cert_pem_path',
               default=None,
               help='SSL certificate for WinRM remote PS connection.'),
    cfg.StrOpt('cert_key_pem_path',
               default=None,
               help='SSL key paired with cert_pem_path for WinRM remote PS '
                    'connection.'),
    cfg.StrOpt('transport_method',
               default='plaintext',
               choices=('ssl', 'ntlm', 'plaintext'),
               help='The method that should be used to establish a connection '
                    'to a Hyper-V host.')
]

_opts = [
    (hyperv_group, HyperVGroup),
    (hyperv_host_auth_group, hyperv_host_auth_opts),
]


def list_opts():
    return _opts
