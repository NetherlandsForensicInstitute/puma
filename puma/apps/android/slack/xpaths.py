# Slack inserts zero-width spaces in some names (e.g. after hyphens), so these are stripped before comparing
ZERO_WIDTH_SPACE = '\u200b'

# Home state
HOME_HISTORY_BUTTON= '//android.view.View[lower-case(@content-desc)="history"]'
HOME_CREATE_NEW_BUTTON= '//android.widget.Button[lower-case(@content-desc)="create new"]'
HOME_WORKSPACE_SELECTOR= '//android.view.View[lower-case(@content-desc)="workspace menu"]'
HOME_CHANNEL_BUTTON = f'//*[android.widget.FrameLayout[@resource-id="com.Slack:id/channel_icon"]][android.widget.TextView[lower-case(translate(@content-desc, "{ZERO_WIDTH_SPACE}", ""))=lower-case("{{channel_name}}")]]'
HOME_DIRECT_MESSAGE_BUTTON = f'//android.view.ViewGroup[@resource-id="com.Slack:id/sk_list_user_view"]/android.widget.TextView[lower-case(translate(@text, "{ZERO_WIDTH_SPACE}", ""))=lower-case("{{direct_message}}")]'

# Channel state
CHAT_TITLE = f'//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.widget.TextView[lower-case(translate(@text, "{ZERO_WIDTH_SPACE}", ""))=lower-case("{{chat_title}}")]'
CHAT_BACK_BUTTON= '//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.view.View[lower-case(@content-desc)="back"]'
CHAT_TEXT_INPUT= '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.widget.MultiAutoCompleteTextView'
