# Slack inserts zero-width spaces in some names (e.g. after hyphens), so these are stripped before comparing
ZERO_WIDTH_SPACE = '\u200b'
# The zero-width space in XPath, so the XPaths themselves do not contain this invisible character
_XPATH_ZERO_WIDTH_SPACE = 'codepoints-to-string(8203)'

# Home state
HOME_HISTORY_BUTTON= '//android.view.View[lower-case(@content-desc)="history"]'
HOME_CREATE_NEW_BUTTON= '//android.widget.Button[lower-case(@content-desc)="create new"]'
HOME_WORKSPACE_SELECTOR= '//android.view.View[lower-case(@content-desc)="workspace menu"]'
# The text is used rather than the content-desc, as the content-desc of channels with unread messages is e.g. 'general, unread'
HOME_CHANNEL_BUTTON = f'//*[android.widget.FrameLayout[@resource-id="com.Slack:id/channel_icon"]][android.widget.TextView[@resource-id="com.Slack:id/channel_name" and lower-case(translate(@text, {_XPATH_ZERO_WIDTH_SPACE}, ""))=lower-case("{{channel_name}}")]]'
HOME_DIRECT_MESSAGE_BUTTON = f'//android.view.ViewGroup[@resource-id="com.Slack:id/sk_list_user_view"]/android.widget.TextView[lower-case(translate(@text, {_XPATH_ZERO_WIDTH_SPACE}, ""))=lower-case("{{direct_message}}")]'

# Channel state
CHAT_TITLE = f'//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.widget.TextView[lower-case(translate(@text, {_XPATH_ZERO_WIDTH_SPACE}, ""))=lower-case("{{chat_title}}")]'
CHAT_BACK_BUTTON= '//android.view.ViewGroup[@resource-id="com.Slack:id/toolbar_compose"]//android.view.View[lower-case(@content-desc)="back"]'
CHAT_TEXT_INPUT= '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.widget.MultiAutoCompleteTextView'
CHAT_ATTACHMENTS_BUTTON = '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.view.View[@content-desc="Attachments"]'
CHAT_SEND_BUTTON = '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.view.View[@content-desc="Send"]'
CHAT_MESSAGES_LIST = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/messages_list"]'
# Shown above the first message of the conversation
CHAT_BEGINNING_OF_CONVERSATION = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/messages_list"]/android.widget.LinearLayout[@resource-id="com.Slack:id/header_container"]'

# Resource ids of the elements of a message, used for parsing the messages in the page source
MESSAGES_LIST_ID = 'com.Slack:id/messages_list'
MESSAGE_ID = 'com.Slack:id/message_layout'
MESSAGE_SENDER_ID = 'com.Slack:id/name'
MESSAGE_TIME_ID = 'com.Slack:id/message_time'
MESSAGE_TEXT_ID = 'com.Slack:id/msg_text'
MESSAGE_FILE_ID = 'com.Slack:id/file_frame_layout'

# Attachments state
ATTACHMENTS_UPLOAD_FILE_BUTTON = '//android.widget.TextView[@resource-id="com.Slack:id/title" and @text="Upload a file"]'
# Only shown when Slack has no permission to access photos yet, the photo strip is shown instead once it has
ATTACHMENTS_ATTACH_PHOTOS_BUTTON = '//android.widget.TextView[@resource-id="com.Slack:id/title" and @text="Attach photos & videos"]'
ATTACHMENTS_MEDIA_STRIP = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]'
ATTACHMENTS_PICTURES = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]/android.widget.FrameLayout[starts-with(@content-desc, "Photo, ")]'
ATTACHMENTS_PICTURE = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]/android.widget.FrameLayout[@content-desc="{content_desc}"]'
ATTACHMENTS_DONE_BUTTON = '//android.widget.Button[@resource-id="com.Slack:id/media_gallery_attach_fab"]'
