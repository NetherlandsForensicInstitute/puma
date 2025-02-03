from setuptools import setup, find_packages

from puma.utils import PROJECT_ROOT
from puma.version import version

setup(
    name="pumapy",
    version=version,
    description="",
    long_description=f"{open(f'{PROJECT_ROOT}/README.md').read()}",
    long_description_content_type="text/markdown",
    author="Netherlands Forensic Institute",
    author_email="netherlandsforensicinstitute@users.noreply.github.com",
    url="https://github.com/NetherlandsForensicInstitute/puma",
    license="EUPL-1.2",
    packages=find_packages(include=['puma*']),
    test_suite="test",
    install_requires=[
        "appium-python-client~=4.3.0",
        "Pillow==10.4.0",
        "pytesseract==0.3.10",
        "geopy~=2.4.1",
        "setuptools~=75.1.0",
        "gpxpy~=1.6.2",
        "adb_pywrapper~=1.0.3",
        "requests~=2.32.3"
    ],
)
