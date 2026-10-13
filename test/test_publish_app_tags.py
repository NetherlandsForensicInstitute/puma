import importlib.util
import unittest

from puma.utils import PROJECT_ROOT


def _load_publish_app_tags():
    spec = importlib.util.spec_from_file_location('publish_app_tags',
                                                  f'{PROJECT_ROOT}/.github/scripts/publish_app_tags.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPublishAppTags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        publish_app_tags = _load_publish_app_tags()
        cls.app_classes = publish_app_tags.find_app_classes()
        cls.get_app_name_and_platform = staticmethod(publish_app_tags.get_app_name_and_platform)

    def test_finds_android_and_ios_apps(self):
        names = {app_class.__name__ for app_class in self.app_classes}
        # an app on each platform, the legacy apps and the App Store, which was missing from the hand-maintained list
        for expected in ['WhatsApp', 'GoogleMapsActions', 'WhatsappBusinessActions', 'Messages', 'AppStore']:
            self.assertIn(expected, names)

    def test_finds_no_base_classes(self):
        names = {app_class.__name__ for app_class in self.app_classes}
        for base_class in ['StateGraph', 'AndroidAppiumActions', 'WhatsAppCommon']:
            self.assertNotIn(base_class, names)

    def test_one_tag_per_app(self):
        tags = [self.get_app_name_and_platform(app_class) for app_class in self.app_classes]
        self.assertEqual(len(tags), len(set(tags)), f'Multiple classes with a supported version for the same app: {tags}')


if __name__ == '__main__':
    unittest.main()
