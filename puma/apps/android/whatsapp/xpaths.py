from puma.utils.xpath_utils import build_resource_id_xpath_widget, build_resource_id_xpath, \
    build_resource_id_text_xpath_widget, build_resource_id_text_xpath, build_content_desc_xpath_widget, \
    build_text_xpath, build_content_desc_xpath, build_text_xpath_widget


def build_wa_resource_id_xpath_widget(widget_type: str, resource_id: str) -> str:
    return build_resource_id_xpath_widget(widget_type, WHATSAPP_PACKAGE, resource_id)


def build_wa_resource_id_xpath(resource_id: str) -> str:
    return build_resource_id_xpath(WHATSAPP_PACKAGE, resource_id)


def build_wa_resource_id_text_xpath_widget(widget_type: str, resource_id: str, text: str) -> str:
    return build_resource_id_text_xpath_widget(widget_type, WHATSAPP_PACKAGE, resource_id, text)


def build_wa_resource_id_text_xpath(resource_id: str, text: str) -> str:
    return build_resource_id_text_xpath(WHATSAPP_PACKAGE, resource_id, text)


WHATSAPP_PACKAGE = 'com.whatsapp'

CONVERSATIONS_WHATSAPP_LOGO = build_wa_resource_id_xpath_widget('ImageView', 'toolbar_logo')
CONVERSATIONS_NEW_CHAT_OR_SEND_MESSAGE = f'{build_content_desc_xpath_widget("ImageButton", "New chat")} | {build_content_desc_xpath_widget("Button", "Send message")}'
CONVERSATIONS_HOME_ROOT_FRAME = build_wa_resource_id_xpath_widget('FrameLayout', 'root_view')
CONVERSATIONS_MENUITEM_ARCHIVE = build_wa_resource_id_xpath('menuitem_conversations_archive')
CONVERSATIONS_ARCHIVED = f'//*[contains(@text,"archived") or @resource-id="{WHATSAPP_PACKAGE}:id/fab"]'
CONVERSATIONS_GROUP_NAME = build_wa_resource_id_xpath('group_name')
CONVERSATIONS_NEW_GROUP = build_text_xpath('New group')
CONVERSATIONS_CHAT_ABLE_CONTACT = build_wa_resource_id_text_xpath('chat_able_contacts_row_name', '{receiver}')
CONVERSATIONS_NEW_BROADCAST_TITLE = build_wa_resource_id_text_xpath('title', 'New broadcast')
CONVERSATIONS_ROW_BY_SUBJECT = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/conversations_row_contact_name" and @text="{{conversation}}"]'

SETTINGS_QR = build_wa_resource_id_xpath_widget('ImageView', 'profile_info_qr_code')
SETTINGS_ACCOUNT_SWITCH = build_wa_resource_id_xpath_widget('ImageView', 'account_switcher_button')

PROFILE_PROFILE_PICTURE = build_content_desc_xpath_widget('ImageView', 'Profile photo')
PROFILE_NAME = build_wa_resource_id_text_xpath_widget('Button', 'profile_settings_row_text', 'Name')
PROFILE_PHONE = build_wa_resource_id_text_xpath_widget('Button', 'profile_settings_row_text', 'Phone')
PROFILE_INFO_EDIT_BUTTON = build_wa_resource_id_xpath_widget('Button', 'profile_info_edit_btn')
PROFILE_GALLERY = build_text_xpath('Gallery')
PROFILE_FOLDERS = build_content_desc_xpath_widget('ImageButton', 'Folders')
PROFILE_SAVE_BUTTON = build_wa_resource_id_xpath('done_btn')
PROFILE_INFO_STATUS_CARD = build_wa_resource_id_xpath('profile_info_status_card')

NEW_CHAT_HEADER = build_text_xpath_widget('TextView', 'New chat')
NEW_CHAT_NEW_GROUP = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New group')
NEW_CHAT_NEW_CONTACT = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New contact')
NEW_CHAT_NEW_COMMUNITY = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New community')

CHAT_ROOT_LAYOUT = build_wa_resource_id_xpath_widget('LinearLayout', 'conversation_root_layout')
CHAT_CONTACT_HEADER = build_wa_resource_id_xpath_widget('TextView', 'conversation_contact_name')
CHAT_CONTACT_HEADER_TEXT = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/conversation_contact_name" and contains(lower-case(@text), "{{conversation}}")]'
CHAT_CONTACT_HEADER_WITH_NAME = build_wa_resource_id_text_xpath_widget('TextView', 'conversation_contact_name', '{conversation}')
CHAT_DELETE_BUTTON = build_content_desc_xpath('Delete')
CHAT_DELETE_FOR_EVERYONE = f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/buttonPanel"]//*[@text="Delete for everyone"]'
CHAT_REPLY = build_content_desc_xpath('Reply')
CHAT_VIEW_ONCE_MEDIA = '//*[contains(@resource-id, "view_once_media")]'
CHAT_VOICE_NOTE_BUTTON = build_wa_resource_id_xpath('voice_note_btn')
CHAT_STICKER = build_wa_resource_id_xpath('sticker')
CHAT_STICKERS = build_wa_resource_id_xpath('stickers')
CHAT_EMOJI = build_wa_resource_id_xpath('emoji')
CHAT_EMOJIS = build_wa_resource_id_xpath('emojis')
CHAT_EMOJI_PICKER = build_wa_resource_id_xpath('emoji_picker_btn')
CHAT_DIRECTORY_NAME = '//android.widget.TextView[@text="{directory_name}"]'
CHAT_DIRECTORY_MEDIA_BY_INDEX = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View'
CHAT_POPUP_BUTTON_OK = build_wa_resource_id_xpath_widget('Button', 'vo_sp_bottom_sheet_ok_button')
CHAT_CAPTION_TEXT_BOX = build_wa_resource_id_xpath('caption')
CHAT_SEND_MEDIA_VIEW_ONCE = build_wa_resource_id_xpath('view_once_toggle')
CHAT_CONTACT_NAME = build_wa_resource_id_text_xpath_widget('TextView', 'name', '{contact_name}')
CHAT_ATTACH_SEND_BUTTON = build_wa_resource_id_xpath('send_btn')
CHAT_ATTACH_CONTACT_BUTTON = build_wa_resource_id_xpath('pickfiletype_contact_holder')
CHAT_ATTACH_GALLERY_BUTTON = build_content_desc_xpath_widget('Button', 'Gallery')
CHAT_GALLERY_FOLDERS_BUTTON = build_content_desc_xpath_widget('ImageButton', 'Folders')
CHAT_FIRST_MEDIA_IN_FOLDER = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[5]/android.view.View[3]/android.widget.Button'
CHAT_STOP_SHARING = build_text_xpath('Stop sharing')
CHAT_MESSAGE_BY_CONTENT = f"//*[@resource-id='{WHATSAPP_PACKAGE}:id/conversation_text_row']//*[contains(@text,'{{message_contains}}')]"
CHAT_MESSAGE_BY_CONTENT_AND_STATE = (f'(//android.widget.FrameLayout['
                              f'@resource-id="{WHATSAPP_PACKAGE}:id/conversation_text_row"'
                              f' and .//android.widget.TextView[@resource-id="com.whatsapp:id/message_text" and @text="{{message_text}}"]'
                              f' and .//android.widget.ImageView[@content-desc="{{state}}"]])')
CHAT_FORWARD_MESSAGE = f"//*[@resource-id='{WHATSAPP_PACKAGE}:id/action_mode_bar']//*[@content-desc='Forward']"
CHAT_FORWARD_CONTACT_BY_NAME = f"//*[@resource-id='{WHATSAPP_PACKAGE}:id/contact_list']//*[@text='{{to_chat}}']"
CHAT_MENTION_SUGGESTIONS = build_wa_resource_id_xpath_widget('ImageView', 'contact_photo')
CHAT_ATTACH_BUTTON = build_wa_resource_id_xpath('input_attach_button')
CHAT_ATTACH_LOCATION_BUTTON = build_wa_resource_id_xpath_widget('Button', 'pickfiletype_location_holder')

SEND_LOCATION_HEADER = f'//android.view.ViewGroup[@resource-id="{WHATSAPP_PACKAGE}:id/toolbar"]/android.widget.TextView[@text="Send location"]'
SEND_LOCATION_CURRENT_LOCATION = build_wa_resource_id_xpath_widget('FrameLayout', 'send_current_location_btn')
SEND_LOCATION_CURRENT_LOCATION_BUTTON = build_wa_resource_id_xpath('send_current_location_btn')
SEND_LOCATION_LIVE_LOCATION = build_wa_resource_id_xpath_widget('FrameLayout', 'live_location_btn')
SEND_LOCATION_LIVE_LOCATION_BUTTON = build_wa_resource_id_xpath('live_location_btn')
SEND_LOCATION_LIVE_LOCATION_DIALOG = build_wa_resource_id_xpath_widget('LinearLayout', 'location_new_user_dialog_container')
SEND_LOCATION_POPUP_CONTINUE = build_text_xpath_widget('Button', 'Continue')
SEND_LOCATION_CAPTION = build_wa_resource_id_xpath('comment')

CHAT_SETTINGS_CONTACT_NAME = (f'{build_wa_resource_id_xpath_widget("TextView", "contact_title")} | '
                              f'{build_wa_resource_id_xpath_widget("TextView", "business_title")} | '
                              f'{build_wa_resource_id_xpath_widget("TextView", "group_title")}')
CHAT_SETTINGS_CONTACT_NAME_TEXT = (f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/contact_title" and contains(lower-case(@text), "{{conversation}}")] | '
                                   f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/business_title" and contains(lower-case(@text), "{{conversation}}")] | '
                                   f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/group_title" and contains(lower-case(@text), "{{conversation}}")]')
CHAT_SETTINGS_NOTIFICATIONS = build_wa_resource_id_xpath_widget('LinearLayout', 'notifications_and_sounds_layout')
CHAT_SETTINGS_MEDIA_VISIBILITY = build_wa_resource_id_xpath_widget('Button', 'media_visibility_layout')
CHAT_SETTINGS_ANY_MEMBER = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/name"]'
CHAT_SETTINGS_MEMBER = build_wa_resource_id_text_xpath('name', '{member}')
CHAT_SETTINGS_REMOVE_MEMBER = "//*[starts-with(@text, 'Remove')]"
CHAT_SETTINGS_EXIT_GROUP_BUTTON = build_text_xpath_widget('Button', 'Exit group')
CHAT_SETTINGS_EXIT_GROUP_LIST_ITEM = build_wa_resource_id_text_xpath('list_item_title', 'Exit group')
CHAT_SETTINGS_DISAPPEARING_MESSAGES = f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/list_item_title" and @text="Disappearing messages"]'
CHAT_SETTINGS_OK_BUTTON = build_text_xpath_widget('Button', 'OK')
CHAT_SETTINGS_CONTAINS_DELETE_GROUP = '//*[contains(@text,"Delete group")]'

RADIO_BUTTON_24_HOURS = build_text_xpath_widget('RadioButton', '24 hours')
RADIO_BUTTON_OFF = build_text_xpath_widget('RadioButton', 'Off')

UPDATES_HEADER = f'//android.view.ViewGroup[@resource-id="{WHATSAPP_PACKAGE}:id/toolbar"]/android.widget.TextView[@text="Updates"]'
UPDATES_STATUS_HEADER = build_wa_resource_id_text_xpath_widget('TextView', 'header_textview', 'Status')
UPDATES_NEW_STATUS = build_content_desc_xpath_widget('ImageButton', 'New status update')
UPDATES_EDIT_CAPTION = build_wa_resource_id_xpath_widget('EditText', 'caption')
UPDATES_SHUTTER = build_content_desc_xpath_widget('ImageView', 'Shutter, Button. Double tap to take a picture, double tap and hold to start recording, release to stop recording.')
UPDATES_CAMERA_BUTTON = build_content_desc_xpath_widget('Button', 'Camera')

CALLS_START_CALL = (
    f'{build_content_desc_xpath_widget("Button", "Start a call")} | '
    f'{build_content_desc_xpath_widget("ImageButton", "New call")}'
)
CALLS_HEADER =  f'({build_text_xpath_widget("TextView", "Calls")})[1]'

CALL_CONTACT_HEADER = build_wa_resource_id_xpath_widget('TextView', 'title')
CALL_CONTACT_HEADER_TEXT = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/title" and contains(lower-case(@text), "{{conversation}}")]'
CALL_TAB_SEARCH_BUTTON = build_content_desc_xpath_widget('ImageButton', 'Search')
CALL_SCREEN_BACKGROUND = build_wa_resource_id_xpath_widget('RelativeLayout', 'call_screen')
CALL_CONTACT_ROW = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/contact_name" and @text="{{conversation}}"]'
CALL_END_CALL_BUTTON = ('//*[@content-desc="Leave call" or '
                        f'@resource-id="{WHATSAPP_PACKAGE}:id/end_call_button" or '
                        f'@resource-id="{WHATSAPP_PACKAGE}:id/footer_end_call_btn"]')

VOICE_CALL_START_BUTTON = build_content_desc_xpath_widget('ImageView', 'Voice call')
VIDEO_CALL_START_BUTTON = build_content_desc_xpath_widget('ImageView', 'Video call')
VOICE_CALL_CAMERA_BUTTON = f'//android.widget.Button[@content-desc="Turn camera on" and @resource-id="{WHATSAPP_PACKAGE}:id/camera_button"]'
VIDEO_CALL_CAMERA_BUTTON = f'//android.widget.Button[@content-desc="Turn camera off" and @resource-id="{WHATSAPP_PACKAGE}:id/camera_button"]'
VIDEO_CALL_SWITCH_CAMERA = build_wa_resource_id_xpath_widget('Button', 'calling_camera_switch_wds_button')

RECEIVE_CALL_ANSWER_BUTTON = "//android.widget.Button[@content-desc='Answer' or @content-desc='Video']"
RECEIVE_CALL_DECLINE_BUTTON = build_content_desc_xpath_widget('Button', 'Decline')

TEXT_ENTRY = build_wa_resource_id_xpath('entry')
TEXT_VIEWS = '//android.widget.TextView'

OPEN_SETTINGS_BY_TITLE = build_text_xpath_widget('TextView', 'Settings')
PROFILE_INFO = build_wa_resource_id_xpath_widget('TextView', 'profile_info_name')

HAMBURGER_MENU = build_content_desc_xpath_widget('ImageView', 'More options')
SEARCH_BAR = build_wa_resource_id_xpath_widget('EditText', 'search_view_edit_text')
CONVERSATIONS_CHAT_TAB = "//android.widget.FrameLayout[starts-with(@content-desc, 'Chats')]"
UPDATES_TAB = build_wa_resource_id_text_xpath_widget('TextView', 'navigation_bar_item_small_label_view', 'Updates')
CALLS_TAB = build_wa_resource_id_text_xpath_widget('TextView', 'navigation_bar_item_small_label_view', 'Calls')

SEND = build_wa_resource_id_xpath('send')
SEND_CONTENT = build_content_desc_xpath_widget('ImageButton', 'Send')
SEND_RESOURCE = build_wa_resource_id_xpath_widget('ImageButton', 'send')
STOP_BUTTON = build_content_desc_xpath_widget('Button', 'Stop')
NEXT_BUTTON = build_wa_resource_id_xpath('next_btn')
EDIT_TEXT2 = "//android.widget.EditText"
EDIT_TEXT = build_wa_resource_id_xpath('edit_text')
OK_BUTTON = build_wa_resource_id_xpath('ok_btn')
