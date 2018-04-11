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

import unittest

import functools
from mock import patch, call, Mock, PropertyMock
import requests_mock

import os, sys

# Hack to load synchronizer framework
test_path=os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
xos_dir=os.path.join(test_path, "../../..")
if not os.path.exists(os.path.join(test_path, "new_base")):
    xos_dir=os.path.join(test_path, "../../../../../../orchestration/xos/xos")
    services_dir = os.path.join(xos_dir, "../../xos_services")
sys.path.append(xos_dir)
sys.path.append(os.path.join(xos_dir, 'synchronizers', 'new_base'))
# END Hack to load synchronizer framework

# generate model from xproto
def get_models_fn(service_name, xproto_name):
    name = os.path.join(service_name, "xos", xproto_name)
    if os.path.exists(os.path.join(services_dir, name)):
        return name
    else:
        name = os.path.join(service_name, "xos", "synchronizer", "models", xproto_name)
        if os.path.exists(os.path.join(services_dir, name)):
            return name
    raise Exception("Unable to find service=%s xproto=%s" % (service_name, xproto_name))
# END generate model from xproto

def mock_get_westbound_service_instance_properties(prop):
    return prop

def match_json(desired, req):
    if desired!=req.json():
        raise Exception("Got request %s, but body is not matching" % req.url)
        return False
    return True

class TestSyncOLTDevice(unittest.TestCase):

    def setUp(self):
        global DeferredException

        self.sys_path_save = sys.path
        sys.path.append(xos_dir)
        sys.path.append(os.path.join(xos_dir, 'synchronizers', 'new_base'))

        # Setting up the config module
        from xosconfig import Config
        config = os.path.join(test_path, "../test_vsg_hw_config.yaml")
        Config.clear()
        Config.init(config, "synchronizer-config-schema.yaml")
        # END Setting up the config module

        from synchronizers.new_base.mock_modelaccessor_build import build_mock_modelaccessor
        build_mock_modelaccessor(xos_dir, services_dir, [get_models_fn("vsg-hw", "vsg-hw.xproto")])
        import synchronizers.new_base.modelaccessor

        from sync_vsg_hw_service_instance import SyncVSGHWServiceInstance, model_accessor

        # import all class names to globals
        for (k, v) in model_accessor.all_model_classes.items():
            globals()[k] = v


        self.sync_step = SyncVSGHWServiceInstance


        # mock onos-fabric
        onos_fabric = Mock()
        onos_fabric.name = "onos-fabric"
        onos_fabric.rest_hostname = "onos-fabric"
        onos_fabric.rest_port = "8181"
        onos_fabric.rest_username = "onos"
        onos_fabric.rest_password = "rocks"

        # mock generic service
        svc = Mock()
        svc.name = "onos-fabric"
        svc.leaf_model = onos_fabric

        # mock vsg-hw service
        self.vsg_service = Mock()
        self.vsg_service.provider_services = [svc]

        # create a mock vsg-hw service instance
        o = Mock()
        o.id = 1
        o.owner = self.vsg_service
        o.tologdict.return_value = {}

        si = Mock()
        si.get_westbound_service_instance_properties = mock_get_westbound_service_instance_properties

        self.o = o
        self.si = si



    def tearDown(self):
        self.o = None
        sys.path = self.sys_path_save

    @requests_mock.Mocker()
    def test_sync_success(self, m):
        expected_conf = {
            'hosts': {
                "mac_address/s_tag": {
                    "basic": {
                        "ips": ["ip_address"],
                        "locations": ["switch_datapath_id/switch_port"],
                        "innerVlan": "c_tag",
                    }
                }
            }
        }

        m.post("http://onos-fabric:8181/onos/v1/network/configuration",
               status_code=200,
               additional_matcher=functools.partial(match_json, expected_conf))

        # override the get_westbound_service_instance_properties mock to remove the outer_tpid field
        def wb_si_prop(prop):
            if prop == "outer_tpid":
                return None
            return prop

        self.si.get_westbound_service_instance_properties = wb_si_prop

        with patch.object(ServiceInstance.objects, "get") as service_instance_mock:
            service_instance_mock.return_value = self.si

            self.sync_step().sync_record(self.o)

            self.assertTrue(m.called)

    @requests_mock.Mocker()
    def test_sync_success_with_tpid(self, m):
        expected_conf = {
            'hosts': {
                "mac_address/s_tag": {
                    "basic": {
                        "ips": ["ip_address"],
                        "locations": ["switch_datapath_id/switch_port"],
                        "innerVlan": "c_tag",
                        "outerTpid": "outer_tpid"
                    }
                }
            }
        }

        m.post("http://onos-fabric:8181/onos/v1/network/configuration",
               status_code=200,
               additional_matcher=functools.partial(match_json, expected_conf))

        with patch.object(ServiceInstance.objects, "get") as service_instance_mock:
            service_instance_mock.return_value = self.si

            self.sync_step().sync_record(self.o)

            self.assertTrue(m.called)