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
        "appium-python-client==3.1.0",
        "selenium==4.14.0",
        "Pillow==10.1.0",
        "pytesseract==0.3.10",
        "adb-pywrapper==1.0.1",
    ],
)
