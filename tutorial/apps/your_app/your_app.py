from typing import Dict

from typing_extensions import deprecated

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

YOUR_APP_PACKAGE = 'TODO'

@deprecated('This class does not use the Puma state machine, and will therefore not be maintained. ' +
            'If you want to add functionality, please rewrite this class using StateGraph as the abstract base class.')
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