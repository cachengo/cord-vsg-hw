# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from synchronizers.new_base.SyncInstanceUsingAnsible import SyncStep
from synchronizers.new_base.modelaccessor import model_accessor, VSGHWServiceInstance, ServiceInstance

from xosconfig import Config
from multistructlog import create_logger
import requests
from requests.auth import HTTPBasicAuth

log = create_logger(Config().get('logging'))

class SyncVSGHWServiceInstance(SyncStep):
    provides = [VSGHWServiceInstance]

    observes = VSGHWServiceInstance

    @staticmethod
    def format_url(url):
        if 'http' in url:
            return url
        else:
            return 'http://%s' % url

    @staticmethod
    def get_fabric_onos_info(si):

        # get the vsg-hw service
        vsg_hw = si.owner

        # get the onos_fabric service
        fabric_onos = [s.leaf_model for s in vsg_hw.provider_services if "onos" in s.name.lower()]

        if len(fabric_onos) == 0:
            raise Exception('Cannot find ONOS service in provider_services of vSG-HW')

        fabric_onos = fabric_onos[0]

        return {
            'url': SyncVSGHWServiceInstance.format_url("%s:%s" % (fabric_onos.rest_hostname, fabric_onos.rest_port)),
            'user': fabric_onos.rest_username,
            'pass': fabric_onos.rest_password
        }

    def sync_record(self, o):
        log.info("Sync'ing VSG-HW Service Instance", service_instance=o)


        onos = SyncVSGHWServiceInstance.get_fabric_onos_info(o)

        si = ServiceInstance.objects.get(id=o.id)

        mac_address = si.get_westbound_service_instance_properties("mac_address")
        s_tag = si.get_westbound_service_instance_properties("s_tag")
        c_tag = si.get_westbound_service_instance_properties("c_tag")
        ip = si.get_westbound_service_instance_properties("ip_address")
        dpid = si.get_westbound_service_instance_properties("switch_datapath_id")
        port = si.get_westbound_service_instance_properties("switch_port")

        data = {
            'hosts': {
                mac_address + "/" + str(s_tag): {
                    "basic": {
                        "ips": [ip],
                        "locations": ["%s/%s" % (dpid, port)],
                        "innerVlan": str(c_tag),
                    }
                }
            }
        }

        # Adding the optional tpid
        tpid = si.get_westbound_service_instance_properties("outer_tpid")
        if tpid:
            data["hosts"][mac_address + "/" + str(s_tag)]["basic"]["outerTpid"] = str(tpid)

        url = onos['url'] + '/onos/v1/network/configuration'

        log.info("Sending requests to ONOS", url=url, body=data)

        r = requests.post(url, json=data, auth=HTTPBasicAuth(onos['user'], onos['pass']))

        if r.status_code != 200:
            raise Exception("Failed to terminate subscriber in ONOS: %s" % r.text)

        log.info("ONOS response", res=r.text)

    def delete_record(self, o):
        log.info("Deleting VSG-HW Service Instance", service_instance=o)
        pass