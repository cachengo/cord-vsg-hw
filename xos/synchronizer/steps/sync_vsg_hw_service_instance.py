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


import os
import sys
from synchronizers.new_base.SyncInstanceUsingAnsible import SyncStep
from synchronizers.new_base.modelaccessor import VSGHWServiceInstance

from xosconfig import Config
from multistructlog import create_logger
from time import sleep
import requests

log = create_logger(Config().get('logging'))

# parentdir = os.path.join(os.path.dirname(__file__), "..")
# sys.path.insert(0, parentdir)
# sys.path.insert(0, os.path.dirname(__file__))

class SyncVSGHWServiceInstance(SyncStep):
    provides = [VSGHWServiceInstance]

    observes = VSGHWServiceInstance

    def sync_record(self, o):
        log.info("Sync'ing VSG-HW Service Instance", service_instance=o)

    def delete_record(self, o):
        log.info("Deleting VSG-HW Service Instance", service_instance=o)
        pass