"""Manifest-only build profiles. No device access or installation."""
import xml.etree.ElementTree as ET

ANDROID = '{http://schemas.android.com/apk/res/android}'
ET.register_namespace('android', ANDROID[1:-1])
PREVIEW_PACKAGE = 'local.proskurnin.xiaomipreview'


def universal_manifest(source):
    """Same application identity, opt-in platform services, no boot takeover."""
    root = ET.fromstring(source)
    app = root.find('application')
    for child in list(app):
        if child.get(ANDROID + 'name') in {'.BootHomeReceiver', '.PowerMenuActivity'}:
            app.remove(child)
    ET.SubElement(app, 'meta-data', {ANDROID + 'name': 'proskurnin.universal', ANDROID + 'value': 'true'})
    ET.SubElement(app, 'provider', {
        ANDROID + 'name': '.PreviewApiConfigProvider',
        ANDROID + 'authorities': root.get('package') + '.configuration',
        ANDROID + 'exported': 'true', ANDROID + 'permission': 'android.permission.DUMP'})
    return ET.tostring(root, encoding='unicode', xml_declaration=True)


def preview_manifest(source):
    root = ET.fromstring(source)
    original = root.attrib['package']
    root.set('package', PREVIEW_PACKAGE)
    root.set(ANDROID + 'versionName', root.get(ANDROID + 'versionName') + '-xiaomi-preview')
    permissions = {'android.permission.INTERNET', 'android.permission.RECORD_AUDIO', 'android.permission.ACCESS_NETWORK_STATE',
                   'android.permission.ACCESS_WIFI_STATE'}
    for child in list(root):
        if child.tag == 'permission' or (child.tag == 'uses-permission'
                and child.get(ANDROID + 'name') not in permissions):
            root.remove(child)
    app = root.find('application')
    app.set(ANDROID + 'label', 'Proskurnin TV · Preview')
    for child in list(app):
        if child.tag != 'activity' or child.get(ANDROID + 'name') not in {'.MainActivity', '.MovieActivity', '.AssistantActivity'}:
            app.remove(child)
            continue
        child.set(ANDROID + 'name', original + child.get(ANDROID + 'name'))
        for intent_filter in list(child.findall('intent-filter')):
            if any(c.get(ANDROID + 'name') == 'android.intent.category.HOME'
                   for c in intent_filter.findall('category')):
                child.remove(intent_filter)
    ET.SubElement(app, 'meta-data', {ANDROID + 'name': 'proskurnin.preview_only',
                                   ANDROID + 'value': 'true'})
    ET.SubElement(app, 'provider', {
        ANDROID + 'name': original + '.PreviewApiConfigProvider',
        ANDROID + 'authorities': PREVIEW_PACKAGE + '.configuration',
        ANDROID + 'exported': 'true',
        ANDROID + 'grantUriPermissions': 'false',
        ANDROID + 'permission': 'android.permission.DUMP'})
    return ET.tostring(root, encoding='unicode', xml_declaration=True)
