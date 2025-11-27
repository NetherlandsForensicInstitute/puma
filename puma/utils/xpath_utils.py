def build_resource_id_xpath_widget(widget_type: str, package_name: str, resource_id: str) -> str:
    return _build_resource_id_xpath(f'android.widget.{widget_type}', package_name, resource_id)

def build_resource_id_xpath(package_name: str, resource_id: str) -> str:
    return _build_resource_id_xpath('*', package_name, resource_id)

def _build_resource_id_xpath(class_name: str, package_name: str, resource_id: str) -> str:
    return f'//{class_name}[@resource-id="{package_name}:id/{resource_id}"]'

def build_content_desc_xpath_widget(widget_type: str, content_desc: str) -> str:
    return _build_content_desc_xpath(f'android.widget.{widget_type}', content_desc)

def build_content_desc_xpath(content_desc: str) -> str:
    return _build_content_desc_xpath('*', content_desc)

def _build_content_desc_xpath(class_name: str, content_desc: str) -> str:
    return f'//{class_name}[@content-desc="{content_desc}"]'

def build_text_xpath_widget(widget_type: str, text: str) -> str:
    return _build_text_xpath(f'android.widget.{widget_type}', text)

def build_text_xpath(text: str) -> str:
    return _build_text_xpath('*', text)

def _build_text_xpath(class_name: str, text: str) -> str:
    return f'//{class_name}[@text="{text}"]'

def build_resource_id_text_xpath_widget(widget_type: str, package_name: str, resource_id: str, text: str) -> str:
    return _build_resource_id_text_xpath(f'android.widget.{widget_type}', package_name, resource_id, text)

def build_resource_id_text_xpath(package_name: str, resource_id: str, text: str) -> str:
    return _build_resource_id_text_xpath('*', package_name, resource_id, text)

def _build_resource_id_text_xpath(class_name: str, package_name: str, resource_id: str, text: str) -> str:
    return f'//{class_name}[@resource-id="{package_name}:id/{resource_id}" and @text="{text}"]'