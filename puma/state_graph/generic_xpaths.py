# Android
APP_STOPPED_POPUP_TITLE = '//android.widget.TextView[@resource-id="android:id/alertTitle"]'
APP_STOPPED_POPUP_CLOSE_BUTTON = '//android.widget.Button[@resource-id="android:id/aerr_close"]'

APP_UPDATE_POPUP_DISMISS_BUTTON = '//android.widget.ImageView[@content-desc="Dismiss update dialog"]'

PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]'
PERMISSIONS_POPUP_ALLOW_BUTTON = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]'

# iOS system alerts are handled by button label, see puma.state_graph.popup_handler.IOSAlertHandler
IOS_PERMISSION_DENY_BUTTON = "Don’t Allow"
IOS_TRACKING_DENY_BUTTON = 'Ask App Not to Track'
# In order of preference: always prefer the least intrusive option that still grants the permission
IOS_PERMISSION_ALLOW_BUTTONS = ['Allow While Using App', 'Allow Full Access', 'Allow', 'OK']
# Other system prompts, which are declined
IOS_ENABLE_DICTATION_BUTTON = 'Enable Dictation'
IOS_NOT_NOW_BUTTON = 'Not Now'
