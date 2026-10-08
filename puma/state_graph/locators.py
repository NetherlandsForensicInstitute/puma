from appium.webdriver.common.appiumby import AppiumBy


class Locator(str):
    """
    A locator for a UI element that uses a strategy other than XPath.

    Puma identifies UI elements with plain strings, which are interpreted as XPaths. On iOS, XPath lookups can be slow,
    because the whole UI hierarchy needs to be serialized for every lookup. Locators allow using faster strategies, such
    as iOS predicate strings or iOS class chains, wherever Puma expects an XPath.

    A Locator is a string, so it can be used everywhere a plain XPath string is accepted (states, clicks, pop-up
    handlers, etc.). Use the factory functions below to create one.
    """
    by: str

    def __new__(cls, value: str, by: str):
        locator = super().__new__(cls, value)
        locator.by = by
        return locator

    def __repr__(self):
        return f'{self.by}={super().__repr__()}'


def accessibility_id(value: str) -> Locator:
    """
    Locate an element by its accessibility id. On iOS this is the 'name' attribute, on Android the 'content-desc'.
    """
    return Locator(value, AppiumBy.ACCESSIBILITY_ID)


def ios_predicate(value: str) -> Locator:
    """
    Locate an element using an iOS predicate string, e.g. `type == "XCUIElementTypeButton" AND name == "Done"`.
    See https://appium.github.io/appium-xcuitest-driver/latest/reference/locator-strategies/
    """
    return Locator(value, AppiumBy.IOS_PREDICATE)


def ios_class_chain(value: str) -> Locator:
    """
    Locate an element using an iOS class chain, e.g. `**/XCUIElementTypeCell[`name BEGINSWITH "Bob"`]`.
    See https://appium.github.io/appium-xcuitest-driver/latest/reference/locator-strategies/
    """
    return Locator(value, AppiumBy.IOS_CLASS_CHAIN)


def to_by_value(locator: str) -> tuple[str, str]:
    """
    Converts a locator to the (by, value) pair used by Appium. Plain strings are interpreted as XPaths.

    :param locator: A plain XPath string or a Locator.
    :return: The Appium locator strategy and value.
    """
    if isinstance(locator, Locator):
        return locator.by, str(locator)
    return AppiumBy.XPATH, locator
