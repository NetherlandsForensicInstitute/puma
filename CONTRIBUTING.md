# Contributing to PUMA

Thank you for considering contributing to our project! By following these guidelines, you will help ensure that our project remains consistent, maintainable, and easy to use.

## Table of Contents
<!-- TOC -->
* [Contributing to PUMA](#contributing-to-puma)
  * [Table of Contents](#table-of-contents)
  * [Development Installation](#development-installation)
  * [Issues](#issues)
  * [Pull Requests](#pull-requests)
  * [Coding Standards](#coding-standards)
  * [Documentation](#documentation)
    * [App Version Support:](#app-version-support)
  * [Writing Puma apps](#writing-puma-apps)
  * [Legacy and deprecation](#legacy-and-deprecation)
  * [Supporting new app versions](#supporting-new-app-versions)
  * [Resources](#resources)
  * [License](#license)
<!-- TOC -->

## Development Installation
To contribute to the project, follow the following installation steps: 

- Follow the installation steps in the [README.md](README.md)
- Install [Appium Inspector](https://github.com/appium/appium-inspector)
- Install Puma by cloning the repository:
```bash
git clone git@github.com:NetherlandsForensicInstitute/puma.git
```
- Create a virtual environment and install Python dependencies:
```bash
cd puma
python3.11 -m venv env
source env/bin/activate 
pip install -r requirements.txt
```

## Issues
- Open an issue for bug reports, feature requests, or general feedback.
- When opening an issue, please provide as much detail as possible, including screenshots, and steps to reproduce for bug reports. If the issue is about a specific app, include its package name and version.


## Pull Requests
- All contributions to the project must be submitted via pull request.
- Ensure that your pull request addresses a specific issue or feature request. If none exists, please open a new issue first to discuss the changes you'd like to make.
- Follow the [GitHub Flow](https://guides.github.com/introduction/flow/) workflow:
  1. Create a new branch from `main`. The branch name should start with the issue number. When adding support for a new
  version of an application, please do this in 1 single issue.
  2. Make your changes and commit them with descriptive commit messages. See the sections [How to add a new application](docs/writing-apps.md#how-to-add-a-new-application) or [Supporting new app versions](#supporting-new-app-versions).
  3. Submit a pull request to the main repository's `main` branch.
- Ensure that your code adheres to the project's [coding standards and conventions](#coding-standards).
- Provide a clear and detailed description of your changes in the pull request description.


## Coding Standards
- **PEP Compliance**: Adhere to PEP 8 for code style. Use PEP 484 for typing hints. Refer to the [PEP 8 documentation](https://www.python.org/dev/peps/pep-0008/) for guidelines.
- **Typing Hints**: Use typing hints on all method signatures, including arguments and return values.
- **Documentation**: PyDoc should be in the reStructuredText style, and include the parameters and return value.


## Documentation
- **Pydoc**: Add pydoc to all methods, fully explaining the method, its arguments, and any limitations. Protected methods (prefixed with `_`) do not need documentation.
- **Update App README**: If a new major feature is added (e.g., stickers, pictures, calls), update the application-specific README to reflect these changes.

### App Version Support:
Any pull request to the `main` branch must **fully** support a specific version of the application. (See [Supporting new app versions](#supporting-new-app-versions)) This version should be
newer than the version currently supported by the codebase.

## Writing Puma apps
How Puma apps work (the StateGraph, states, transitions and actions), and how to add support for a new application or
new functionality, is explained in [Writing Puma apps](docs/writing-apps.md). This includes
[how to add a new application](docs/writing-apps.md#how-to-add-a-new-application), for Android as well as
[iOS](docs/writing-apps.md#ios-applications).

## Legacy and deprecation
In Puma 3.0.0, the `StateGraph` was introduced. Before that, a number of applications were already supported, using the
old `AndroidAppiumActions` as an abstract base class. These classes are no longer maintained, and they are marked using
the `@deprecated` decorator. If you want to add new functionality to these classes, please rewrite it to the Puma `StateGraph`,
and add the functionality using the new framework.

## Supporting new app versions
When you notice the code no longer works on a newer app version, you can update the code to work for the new version.
- To diagnose which functionality does not work anymore for the new version, run the <TODO test script>, which verifies
each function for an app and reports which ones do not work anymore. Make sure to run it after you have finished as well.
- Make sure that all functions in the application class for the specific app version works again, also when you might only be interested in some
of them. For example, when you have a script that sends a few messages and you want to update this in the Appium code
for WhatsApp, also make sure sending a picture and calling still works.
- The most common cause for the code not working for a specific app version anymore is the change of an attribute value.
For example, the resource id for the WhatsApp text box changed from `com.whatsapp:id/entry` to `com.whatsapp:id/whatsappEntry`.
This needs to be updated in the xpath used to find the element.
- **Do not make the code backwards compatible with older versions**, just update the code to work for the new version.
This ensures the code remains readable. For older versions the user can go back to a dedicated release for that version.
- Also perform the following actions:
  - Update the version annotation in the class
  - Refer to the test script provided in our repository for guidelines on creating these tests.


## Resources
- XPATH is a powerful selector for XML documents. Learn about XPATH syntax from resources like [W3Schools XPATH Tutorial](https://www.w3schools.com/xml/xpath_intro.asp).
- Appium is an open-source project and ecosystem of related software, designed to facilitate UI automation of many app platforms. See the [Appium website](http://appium.io/docs/en/latest/).


## License
