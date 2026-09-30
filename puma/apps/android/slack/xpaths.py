# Home state
HOME_HISTORY_BUTTON= '//android.view.View[@content-desc="History"]'
HOME_CREATE_NEW_BUTTON= '//android.widget.Button[@content-desc="Create new"]'
HOME_WORKSPACE_SELECTOR= '//android.view.View[@content-desc="Workspace menu"]'
HOME_CHANNEL_BUTTON= '//*[android.widget.FrameLayout[@resource-id="com.Slack:id/channel_icon"]][android.widget.TextView[@content-desc="{channel_name}"]]'

# Channel state
CHAT_TITLE= '//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.widget.TextView[@text="{chat_title}"]'
CHAT_BACK_BUTTON= '//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.view.View[@content-desc="Back"]'
CHAT_TEXT_INPUT= '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.widget.MultiAutoCompleteTextView'
