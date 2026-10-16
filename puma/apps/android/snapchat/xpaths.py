# Most resource ids in Snapchat are obfuscated (com.snapchat.android:id/0_resource_name_obfuscated), so many locators
# use content descriptions, texts or the structure of the screen instead.

# Navigation bar, at the bottom of the camera, chat and other tabs
NAVIGATION_CAMERA_TAB = '//android.view.ViewGroup[@resource-id="com.snapchat.android:id/ngs_camera_icon_container"]'
NAVIGATION_CHAT_TAB = '//android.view.ViewGroup[@resource-id="com.snapchat.android:id/ngs_chat_icon_container"]'

# Camera, both the camera tab and the camera opened from a chat
CAMERA_PAGE = '//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/camera_page"]'
CAMERA_CAPTURE_BUTTON = '//android.widget.FrameLayout[@content-desc="Camera Capture"]'
CAMERA_FLIP_BUTTON = '//android.view.ViewGroup[@content-desc="Flip Camera"]'

# Camera opened from a chat, which sends the snap to that chat
CHAT_CAMERA_CLOSE_BUTTON = '//android.widget.ImageView[@content-desc="Close camera"]'
CHAT_CAMERA_RECIPIENT = ('//android.widget.TextView[@text="Send To"]'
                         '/following-sibling::android.widget.TextView[lower-case(@text)=lower-case("{conversation}")]')

# Conversations, the chat tab
CONVERSATIONS_TITLE = '//android.widget.TextView[@text="Chat" and @clickable="true"]'
CONVERSATIONS_SEARCH_BUTTON = '//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/hova_header_search_icon"]'

# Search, opened from the conversations
SEARCH_TEXT_FIELD = '//android.widget.EditText[@resource-id="search-textfield"]'
SEARCH_CANCEL_BUTTON = '//android.view.View[@resource-id="dismiss-button"]'
SEARCH_FRIEND_RESULT = ('//android.view.View[@resource-id="friend-result-cell"'
                        ' and .//android.widget.TextView[@resource-id="result-title" and lower-case(@content-desc)=lower-case("{conversation}")]]')

# Chat
CHAT_TEXT_FIELD = '//android.widget.EditText[@resource-id="com.snapchat.android:id/chat_input_text_field"]'
CHAT_MESSAGE_LIST = '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.snapchat.android:id/chat_message_list"]'
CHAT_CAMERA_BUTTON = '//android.widget.ImageButton[@resource-id="com.snapchat.android:id/chat_input_bar_camera"]'
CHAT_TITLE = ('//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/avatar_icon"]'
              '/following-sibling::*//android.widget.TextView[lower-case(@text)=lower-case("{conversation}")]')

# Preview of a snap that was just taken, on the camera tab and in a chat
SNAP_PREVIEW_FRAME = '//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/preview_frame"]'
SNAP_PREVIEW_DISCARD_BUTTON = '//android.widget.ImageButton[@content-desc="Discard"]'
SNAP_PREVIEW_CAPTION_BUTTON = '//android.view.View[@resource-id="caption"]'
SNAP_PREVIEW_CAPTION_TEXT_FIELD = '//android.widget.EditText[@resource-id="com.snapchat.android:id/caption_edit_text_view"]'
SNAP_PREVIEW_SEND_TO_BUTTON = '//android.view.ViewGroup[@resource-id="com.snapchat.android:id/sent_to_button_label_mode_view"]'

# Preview of a snap taken from a chat: it has a button to send it to the chat, and one to add more friends
CHAT_SNAP_PREVIEW_MORE_FRIENDS_BUTTON = '//android.widget.TextView[@text="+ More Friends"]'
CHAT_SNAP_PREVIEW_SEND_BUTTON = ('//android.widget.TextView[@text="+ More Friends"]'
                                 '/following-sibling::android.view.ViewGroup[.//android.widget.TextView[lower-case(@text)=lower-case("{conversation}")]]')

# Send to, where the recipients of a snap are chosen
SEND_TO_SEARCH_FIELD = '//android.widget.EditText[@resource-id="com.snapchat.android:id/input_field_edit_text"]'
SEND_TO_BACK_BUTTON = '//android.view.View[@resource-id="com.snapchat.android:id/subscreen_top_left"]'
SEND_TO_RECIPIENT = '//android.view.View[./javaClass[lower-case(@text)=lower-case("{recipient}")]]'
SEND_TO_SELECTED_RECIPIENT = ('//android.view.ViewGroup[@resource-id="com.snapchat.android:id/send_to_confirmation_bar"]'
                              '//android.widget.TextView[lower-case(@text)=lower-case("{recipient}")]')
# The stories to post to, visible to friends only or to everyone. Only one of them can be selected. The name of a story
# is the first line of its row: the row of the last snap has the story it was posted to as second line.
SEND_TO_MY_STORY = '//android.view.View[./javaClass[1][@text="My Story · Friends Only"]]'
SEND_TO_PUBLIC_STORY = '//android.view.View[./javaClass[1][@text="My Story · Public"]]'
# Asks to confirm adding the snap to My Story, when My Story is selected. Cancel deselects My Story.
SEND_TO_ADD_TO_STORY_CONFIRM_BUTTON = '//android.view.View[@resource-id="com.snapchat.android:id/add_to_story_dialog_confirm_view"]'
# Introduces the public story and the public profile, the first time the public story is selected.
SEND_TO_PUBLIC_STORY_INTRODUCTION_OKAY_BUTTON = '//android.widget.Button[@resource-id="introducing-public-story-nux-button"]'
SEND_TO_SEND_BUTTON ='//android.view.View[@resource-id="com.snapchat.android:id/send_to_send_button"]'

# Pop-ups
POPUP_DIALOG = '//android.widget.LinearLayout[@resource-id="com.snapchat.android:id/dialog_content"]'
POPUP_CANCEL_BUTTON = '//android.widget.TextView[@resource-id="com.snapchat.android:id/cancel_button"]'
# Asks to share the location, shown after taking the first snap. Declined.
POPUP_LOCATION_ALLOW_BUTTON = '//android.view.View[@resource-id="com.snapchat.android:id/location_permission_alert_confirm_view"]'
# Asks whether to abandon a snap that was edited (e.g. has a caption), when leaving the preview.
POPUP_DISCARD_SNAP_BUTTON = '//android.view.View[@resource-id="com.snapchat.android:id/discard_alert_dialog_discard_view"]'
# Asks to save the snaps posted to a story in Memories, the first time a snap is posted to a story. Declined.
POPUP_AUTO_SAVE_STORY_TITLE = ('//android.widget.TextView[@resource-id="com.snapchat.android:id/alert_dialog_title"'
                               ' and starts-with(@text, "Auto-Save Story Snaps")]')
# Covers the camera until Snapchat may use the camera and microphone. Allowing it shows the permission requests of
# Android, which are handled by the generic pop-up handlers.
POPUP_CAMERA_PERMISSION_TITLE = '//android.widget.TextView[@text="Snapchat is a camera app"]'
POPUP_CAMERA_PERMISSION_ALLOW_BUTTON = f'{POPUP_CAMERA_PERMISSION_TITLE}/following-sibling::android.view.View'
