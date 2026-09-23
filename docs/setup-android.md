# Setting up Android devices

You can either use a physical Android device or an Android emulator.
See [Optional: Android Studio](#optional-android-studio-for-running-an-emulator) for instructions on installing
Android Studio and running an emulator

- Have the Android device(s) or emulator(s) connected to the system where Puma runs, configured as follows:
    - Connected to the Internet
    - Language set to English
    - File transfer enabled
    - (Root access is not needed)

You can check if the device is connected:

  ```shell
  adb devices
    > List of devices attached
  894759843jjg99993  device
  ```

If the status says `device`, the device is connected and available.

The UDID of the device (in the example above `894759843jjg99993`) is what you pass to Puma, e.g. `WhatsApp("894759843jjg99993")`.

## Optional: Android Studio (for running an emulator)

For more information about Android Emulators, refer
to [the Android developer website](https://developer.android.com/studio/run/managing-avds#about)
Follow these steps to create and start an Android emulator:

1. [Install Android Studio](https://developer.android.com/studio/run/managing-avds#createavd).
2. [Create an Android Virtual Device (avd)](https://developer.android.com/studio/run/managing-avds) We recommend a Pixel
   with the Playstore enabled, and a recent Android version. For running 1 or a few apps, the default configuration can
   be used.
3. [Start the emulator](https://developer.android.com/studio/run/managing-avds#emulator).

If you want to run the emulator from the commandline, refer
to [Start the emulator from the command line](https://developer.android.com/studio/run/emulator-commandline).

See [troubleshooting](troubleshooting.md#android) if the device does not connect.
