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
CHAT_ATTACHMENTS_BUTTON = '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.view.View[@content-desc="Attachments"]'
CHAT_SEND_BUTTON = '//android.widget.FrameLayout[@resource-id="com.Slack:id/advanced_message_input_container"]//android.view.View[@content-desc="Send"]'

# Attachments state
ATTACHMENTS_UPLOAD_FILE_BUTTON = '//android.widget.TextView[@resource-id="com.Slack:id/title" and @text="Upload a file"]'
# Only shown when Slack has no permission to access photos yet, the photo strip is shown instead once it has
ATTACHMENTS_ATTACH_PHOTOS_BUTTON = '//android.widget.TextView[@resource-id="com.Slack:id/title" and @text="Attach photos & videos"]'
ATTACHMENTS_MEDIA_STRIP = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]'
ATTACHMENTS_PICTURES = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]/android.widget.FrameLayout[starts-with(@content-desc, "Photo, ")]'
ATTACHMENTS_PICTURE = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.Slack:id/media_recycler_view"]/android.widget.FrameLayout[@content-desc="{content_desc}"]'
ATTACHMENTS_DONE_BUTTON = '//android.widget.Button[@resource-id="com.Slack:id/media_gallery_attach_fab"]'
