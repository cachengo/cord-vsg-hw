
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


from synchronizers.new_base.modelaccessor import VSGHWServiceInstance, model_accessor
from synchronizers.new_base.policy import Policy
from synchronizers.new_base.exceptions import *

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class VSGHWServiceInstancePolicy(Policy):
    model_name = "VSGHWServiceInstance"

    def handle_create(self, service_instance):
        return self.handle_update(service_instance)

    def handle_update(self, service_instance):
        log.info("Handle_update VSG-HW Service Instance", service_instance=service_instance)
        if (service_instance.link_deleted_count>0) and (not service_instance.provided_links.exists()):
            # if the last provided_link has just gone away, then self-destruct
            self.logger.info("The last provided link has been deleted -- self-destructing.")
            # TODO: We shouldn't have to call handle_delete ourselves. The model policy framework should handle this
            #       for us, but it isn't. I think that's happening is that serviceinstance.delete() isn't setting a new
            #       updated timestamp, since there's no way to pass `always_update_timestamp`, and therefore the
            #       policy framework doesn't know that the object has changed and needs new policies. For now, the
            #       workaround is to just call handle_delete ourselves.
            self.handle_delete(service_instance)
            # Note that if we deleted the Instance in handle_delete, then django may have cascade-deleted the service
            # instance by now. Thus we have to guard our delete, to check that the service instance still exists.
            if VSGHWServiceInstance.objects.filter(id=service_instance.id).exists():
                service_instance.delete()
            else:
                self.logger.info("Tenant %s is already deleted" % service_instance)
            return

    def handle_delete(self, service_instance):
        log.info("Handle_delete VSG-HW Service Instance", service_instance=service_instance)


