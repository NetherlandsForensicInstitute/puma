from dataclasses import dataclass
from enum import Enum
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy

FILL_AD_ACTIVITY = "com.horizon.android.feature.syi.SyiActivity"

class Condition(Enum):
    NEW = "Nieuw"
    AS_NEW = "Zo goed als nieuw"
    USED = "Gebruikt"


class ShippingMode(Enum):
    PICKUP = "Ophalen"
    SEND = "Verzenden"
    PICKUP_OR_SEND = "Ophalen of Verzenden"


class PackageType(Enum):
    SMALL = "Brievenbuspakje"
    MEDIUM = "Gemiddeld pakket"
    LARGE = "Groot pakket"


@dataclass
class AdInput:
    title: str
    category: str
    description: str
    price: str
    picture_dir: str
    picture_indices: list
    condition: Condition = Condition.USED
    shipping_mode: ShippingMode = ShippingMode.SEND
    package_type: PackageType = PackageType.MEDIUM
    advertisement_type: str = "Gratis"


class MarktplaatsAd:
    def __init__(self, ad_input: AdInput, marktplaats_actions):
        self.ad_input = ad_input
        # The mp_actions object is passed just to have access to the functionality in AndroidAppiumActions
        self.mp_actions = marktplaats_actions

    def select_picture_folder_and_pictures(self, directory_name, pic_indices):
        directory_tile = f'//android.widget.TextView[@resource-id="nl.marktplaats.android:id/albumName" and contains(@text, "{directory_name}")]'
        self.mp_actions.swipe_to_find_element(xpath=directory_tile).click()
        pictures = self.mp_actions.driver.find_elements(by=AppiumBy.XPATH,
                                                        value='(//android.view.View[contains(@content-desc, "Image")])')
        for pic_index in pic_indices:
            pictures[pic_index].click()
        add_button = (
            self.mp_actions.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[@text="Add"]'))
        add_button.click()

    def create(self, picture_dir, picture_indices):
        xpath = '//android.widget.TextView[@resource-id="nl.marktplaats.android:id/hpButtonText" and @text="Post an ad"]'
        self.mp_actions.return_to_homescreen()
        post_add_button = self.mp_actions.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        post_add_button.click()
        self.select_picture_folder_and_pictures(picture_dir,picture_indices) #TODO click skip
        sleep(3)
        cont_button = (
            self.mp_actions.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[@text="Continue"]'))
        cont_button.click()

        # TODO everything case insensitive

    def fill(self, ad_input: AdInput):
        """
        Fill ad with input. Assumes you are in the ad editing screen.
        """
        sleep(3)
        current_activity = self.mp_actions.driver.current_activity
        if not current_activity == FILL_AD_ACTIVITY:
            print({current_activity})
            # raise ValueError(f"Expected to be in ad editing screen, but current activity is {current_activity}. "
            #                  f"Please call create first.")
        # TODO check if in ad editing screen, otherwise create or log a warning
        # TODO pass AdInput.X to each function
        self.set_title()
        self.set_category()
        self.set_description()
        self.set_condition()
        self.set_price()
        self.set_shipping_mode()
        self.set_package_type()
        self.set_advertisement_type()

    def add_pictures(self, picture_dir: str, indices=None):
        if indices is None:
            indices = []
        ...

    def set_title(self):
        title_field = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                          value='//android.widget.EditText[@text="Title"]')
        title_field.send_keys(self.ad_input.title)

    def set_category(self):
        #TODO
        category_field = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                             value='//android.widget.TextView[@text="Category"]').click()
        self.mp_actions.driver.back()

    def set_description(self):
        description_field = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                                value='//android.widget.EditText[@text="Description"]')
        description_field.send_keys(self.ad_input.description)
        sleep(1)

    def set_condition(self):
        attribute_list = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                             value='//android.widget.TextView[contains(@text, "Attributes")]').click()
        condition_attribute = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                                  value='//android.widget.TextView[contains(@text, "Conditie")]').click()
        # condition_to_set = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
        #                                                        value=f'//android.widget.TextView[@text, {self.ad_input.condition.value}]').click()
        condition_to_set = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                               value=f'//android.widget.CheckBox[@resource-id="nl.marktplaats.android:id/value" and @text="{self.ad_input.condition.value}"]').click()

        ok_button = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                        value='//android.widget.Button[@text = "OK"]').click()
        ok_button2 = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                         value='//android.widget.Button[@text = "OK"]').click()

    def set_price(self):
        set_price = self.mp_actions.scroll_to_find_element(resource_id="nl.marktplaats.android:id/priceValue")
        set_price.send_keys(self.ad_input.price)

    def set_shipping_mode(self):
        shipping_mode = self.mp_actions.scroll_to_find_element(
            resource_id="nl.marktplaats.android:id/shippingWidgetTitle")
        shipping_mode.click()
        # Select shipping mode
        self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                            value=f'//android.widget.RadioButton[@text="{self.ad_input.shipping_mode.value}"]').click()
        self.mp_actions.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@text = "OK"]').click()

    def set_package_type(self):
        self.mp_actions.scroll_to_find_element(text_equals=f'{self.ad_input.package_type.value}').click()

    def set_advertisement_type(self):
        self.mp_actions.driver.find_element(
            by=AppiumBy.XPATH, value=
            f"//android.widget.TextView[@resource-id='nl.marktplaats.android:id/title' and @text='{self.ad_input.advertisement_type}']"
            f"/.."  # Parent element of the text element
            f"//android.widget.ImageView[@resource-id='nl.marktplaats.android:id/checkbox']"
            # checkbox sibling of the text element
        ).click()

    def post(self):
        post_add_btn = self.mp_actions.driver.find_element(by=AppiumBy.XPATH,
                                                           value=f'//android.widget.Button[@resource-id="nl.marktplaats.android:id/primary" and @text="Post ad"]')
        post_add_btn.click()
