from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import AndroidAppiumActions
from puma.apps.android.marktplaats.advertisement import AdInput, MarktplaatsAd

MARKTPLAATS_PACKAGE = 'nl.marktplaats.android'

# TODO add version annotation
class MarktplaatsActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      MARKTPLAATS_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server,
                                      app_activity="com.horizon.android.feature.homepage.SpringboardActivity")
    def currently_in_homescreen(self) -> bool:
        # Send message occurs when no conversations are present yet. New chat when there are conversations.
        return self.driver.current_activity == "com.horizon.android.feature.homepage.SpringboardActivity"

    def return_to_homescreen(self):
        if self.driver.current_package != MARKTPLAATS_PACKAGE:
            self.driver.activate_app(MARKTPLAATS_PACKAGE)
        while not self.currently_in_homescreen():
            self.driver.back()
            save_ad_popup = '//android.widget.TextView[@resource-id="nl.marktplaats.android:id/alertTitle" and @text="Save ad?"]'
            if self.is_present(save_ad_popup):
                self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@text="No, please remove"]').click()

        sleep(0.5)

    def add_new_ad(self, ad_input: AdInput):
        ad = MarktplaatsAd(ad_input, marktplaats_actions=self)
        ad.create(ad_input.picture_dir, ad_input.picture_indices)
        ad.fill(ad_input)
        ad.post()
