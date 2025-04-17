from typing import Dict

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

YOUR_APP_PACKAGE = 'TODO'

@supported_version("TODO")
class YourAppActions(AndroidAppiumActions):

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      YOUR_APP_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def your_app_function(self):
        print("Functionality can be added here!")