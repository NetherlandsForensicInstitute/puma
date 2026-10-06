import re

from setuptools import setup, find_packages

from puma.utils import PROJECT_ROOT
from puma.version import version

GITHUB_URL = "https://github.com/NetherlandsForensicInstitute/puma"


def long_description() -> str:
    """
    The README, with relative links replaced by absolute links to GitHub, so they also work on PyPI.
    """
    def absolute(match):
        image, label, target = match.groups()
        if re.match(r'^(https?:|mailto:|#)', target):
            return match.group(0)
        base = f"{GITHUB_URL}/raw/main/" if image else f"{GITHUB_URL}/blob/main/"
        return f"{image}[{label}]({base}{target})"

    readme = open(f'{PROJECT_ROOT}/README.md').read()
    return re.sub(r'(!?)\[([^\]]*)\]\(([^)\s]+)\)', absolute, readme)


setup(
    name="pumapy",
    version=version,
    description="",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author="Netherlands Forensic Institute",
    author_email="netherlandsforensicinstitute@users.noreply.github.com",
    url="https://github.com/NetherlandsForensicInstitute/puma",
    license="EUPL-1.2",
    packages=find_packages(include=['puma*']),
    test_suite="test",
    install_requires=[
        "urllib3~=2.6.3",
        "appium-python-client~=5.2.4",
        "Pillow==12.3.0",
        "pytesseract==0.3.13",
        "geopy~=2.4.1",
        "setuptools~=80.9.0",
        "gpxpy~=1.6.2",
        "adb_pywrapper~=1.3.0",
        "requests~=2.32.5"
    ],
)
