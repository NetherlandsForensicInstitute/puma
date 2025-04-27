# Puma puma

Welcome to the Puma tutorial! This section of the repository is dedicated to guiding you through the process of learning
how to use Puma and how to contribute to Puma.

### Prerequisites

Before you begin, make sure you have the following:

- Familiarity with Python
- Have Android Studio installed with an emulator running on your host machine (
  see [Puma README](../README.md#requirements))
- Install the requirements with the installation scripts in [the install folder](../install)
- Additionally, install the `tutorial_requirements` by running `pip install tutorial/tutorial_requirements` from the
  puma root.

### Run Exercises with Jupyter

The exercises are available as [Jupyter Notebooks](https://docs.jupyter.org/en/latest/start/index.html), in this
project, run `jupyter notebook`. This will open a browser window in which you can navigate to the first exercise and
get started.

### Set Up Appium Inspector

Before you can use Appium Inspector, you first need to configure the capabilities. See the [Appium Inspector section in
the CONTRIBUTING.md](../CONTRIBUTING.md#example-writing-new-appium-actions) for a JSON snippet.

### Run an emulator in Android Studio

1. `New project` > `No Activity` > `Finish`
2. Go to `Tools` > `Device Manager`. If there is already a device listed, you can run it by clicking the `play button`.
   If no device is listed, proceed with the steps below:
3. 3.`+` > `Create Virtual Device` > `Pixel 9` (or any other with the Google PlayStore icon) > `Finish`.
4. Run by clicking the `Play` button