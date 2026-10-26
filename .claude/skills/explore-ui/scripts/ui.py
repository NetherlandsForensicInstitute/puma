"""
Explore the UI of a connected Android device over adb, without starting an Appium session.

The UI hierarchy is printed in the same shape as the Appium page source (the class of an element is its tag), so the
XPaths you test here can be used in Puma. See ../references/android.md for how and when to use this.

    python ui.py tree                 the elements on screen that carry information
    python ui.py find '<xpath>' ...   the elements matching each XPath (needs lxml)
    python ui.py tap '<xpath>'        tap the center of the first matching element (needs lxml)
    python ui.py xml                  the full hierarchy as XML
    python ui.py focus                the package and activity that are in the foreground
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ElementTree

try:
    from lxml import etree
except ImportError:
    etree = None

# The port the Appium UiAutomator2 server listens on, on the device
UIAUTOMATOR2_SERVER_PORT = 6790
# Characters that are valid in a class name, but not in an XML tag. The UiAutomator2 server replaces these as well
INVALID_TAG_CHARACTERS = r'[$@#&]'
BOUNDS_PATTERN = r'\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]'
SHORT_CLASS_NAMES = {'android.widget.': 'w.', 'android.view.': 'v.'}
SERIAL = None


def adb(*args: str) -> str:
    serial = ['-s', SERIAL] if SERIAL else []
    result = subprocess.run(['adb', *serial, *args], capture_output=True)
    if result.returncode != 0 and not result.stdout:
        sys.exit(f'adb {" ".join(args)} failed: {result.stderr.decode(errors="replace").strip()}')
    return result.stdout.decode('utf-8', errors='replace')


def _uiautomator_dump() -> str | None:
    """
    :return: The hierarchy as dumped by uiautomator, or None if the dump failed.
    """
    output = adb('exec-out', 'uiautomator', 'dump', '/dev/tty')
    if '<hierarchy' not in output:
        return None
    return output[output.index('<hierarchy'):output.rindex('</hierarchy>') + len('</hierarchy>')]


def _to_appium_source(dump: str) -> str:
    """
    uiautomator names every element 'node', while Appium uses the class of the element as tag.
    """
    root = ElementTree.fromstring(dump)
    for node in root.iter('node'):
        node.tag = re.sub(INVALID_TAG_CHARACTERS, '.', node.get('class')) or 'node'
    ElementTree.indent(root)
    return ElementTree.tostring(root, encoding='unicode')


def _uiautomator2_server_source() -> str | None:
    """
    While the UiAutomator2 server of Appium is running on the device, uiautomator cannot dump the hierarchy. In that
    case the page source is requested from that server, using the Appium session that is already open.

    :return: The Appium page source, or None if there is no UiAutomator2 server with an open session.
    """
    serial = SERIAL or adb('get-serialno').strip()
    for line in adb('forward', '--list').splitlines():
        match = re.fullmatch(rf'{re.escape(serial)} tcp:(\d+) tcp:{UIAUTOMATOR2_SERVER_PORT}', line.strip())
        if not match:
            continue
        server = f'http://127.0.0.1:{match.group(1)}'
        try:
            sessions = json.load(urllib.request.urlopen(f'{server}/sessions', timeout=5))['value']
            if sessions:
                source = urllib.request.urlopen(f'{server}/session/{sessions[0]["id"]}/source', timeout=30)
                return json.load(source)['value']
        except OSError:
            continue
    return None


def get_source() -> str:
    """
    :return: The UI hierarchy of the current screen, in the shape of the Appium page source.
    """
    dump = _uiautomator_dump()
    if dump:
        return _to_appium_source(dump)
    source = _uiautomator2_server_source()
    if source:
        print('uiautomator dump failed, using the page source of the running Appium session', file=sys.stderr)
        return source
    sys.exit('Could not dump the UI hierarchy. Is the screen on and unlocked? If the screen keeps animating (video, '
             'spinner), uiautomator cannot dump it. If an Appium session was left behind, stop its server with: '
             'adb shell am force-stop io.appium.uiautomator2.server')


def _first_string(value) -> str:
    if isinstance(value, list):
        value = value[0] if value else ''
    return str(value)


def _register_xpath2_functions():
    """
    Appium evaluates XPath 2.0, lxml only XPath 1.0. These are the XPath 2.0 functions used in Puma.
    """
    functions = etree.FunctionNamespace(None)
    functions['lower-case'] = lambda _, value: _first_string(value).lower()
    functions['upper-case'] = lambda _, value: _first_string(value).upper()
    functions['ends-with'] = lambda _, value, suffix: _first_string(value).endswith(_first_string(suffix))
    functions['matches'] = lambda _, value, pattern: bool(re.search(_first_string(pattern), _first_string(value)))


def find(source: str, xpath: str) -> list:
    if etree is None:
        sys.exit('Evaluating XPaths needs lxml: pip install lxml')
    _register_xpath2_functions()
    try:
        matches = etree.fromstring(source.encode()).xpath(xpath)
    except etree.XPathError as e:
        sys.exit(f'Invalid XPath {xpath}: {e}')
    return [match for match in matches if isinstance(match, etree._Element)]


def center(element) -> tuple[int, int]:
    left, top, right, bottom = map(int, re.fullmatch(BOUNDS_PATTERN, element.get('bounds')).groups())
    return (left + right) // 2, (top + bottom) // 2


def describe(element) -> str:
    attributes = element.attrib
    name = attributes.get('class', element.tag)
    for prefix, short in SHORT_CLASS_NAMES.items():
        name = name.replace(prefix, short)
    description = [name]
    for label, key in (('text', 'text'), ('desc', 'content-desc'), ('id', 'resource-id')):
        if attributes.get(key):
            description.append(f'{label}={attributes[key]!r}')
    description.append(attributes.get('bounds', ''))
    flags = [flag for flag in ('clickable', 'long-clickable', 'scrollable', 'checked', 'selected', 'focused')
             if attributes.get(flag) == 'true']
    if attributes.get('enabled') == 'false':
        flags.append('disabled')
    return ' '.join(description + flags)


def print_tree(source: str, show_all: bool, package: str | None):
    def walk(element, depth: int):
        attributes = element.attrib
        informative = any(attributes.get(key) for key in ('text', 'content-desc', 'resource-id'))
        if 'bounds' in attributes and (show_all or informative) and package in (None, attributes.get('package')):
            print(f'{"  " * depth}{describe(element)}')
        for child in element:
            walk(child, depth + 1)

    walk(ElementTree.fromstring(source), 0)


def print_focus():
    for line in adb('shell', 'dumpsys', 'window').splitlines():
        if 'mCurrentFocus=' in line:
            print(line.strip())


def main():
    global SERIAL
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--serial', help='The serial of the device, required when multiple devices are connected')
    commands = parser.add_subparsers(dest='command', required=True)
    tree = commands.add_parser('tree')
    tree.add_argument('--all', action='store_true', help='Also show elements without text, content-desc or resource-id')
    tree.add_argument('--package', help='Only show elements of this package')
    commands.add_parser('find').add_argument('xpaths', nargs='+')
    commands.add_parser('tap').add_argument('xpath')
    commands.add_parser('xml')
    commands.add_parser('focus')
    args = parser.parse_args()
    SERIAL = args.serial
    # Element texts can contain characters the console encoding does not support, e.g. on Windows
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if args.command == 'focus':
        print_focus()
    elif args.command == 'tree':
        print_focus()
        print_tree(get_source(), args.all, args.package)
    elif args.command == 'xml':
        print(get_source())
    elif args.command == 'find':
        source = get_source()
        for xpath in args.xpaths:
            matches = find(source, xpath)
            print(f'{len(matches)} match(es) for {xpath}')
            for match in matches:
                print(f'  {describe(match)}')
    elif args.command == 'tap':
        matches = find(get_source(), args.xpath)
        if not matches:
            sys.exit(f'No match for {args.xpath}')
        x, y = center(matches[0])
        print(f'Tapping ({x}, {y}): {describe(matches[0])}' + (f' (first of {len(matches)})' if len(matches) > 1 else ''))
        adb('shell', 'input', 'tap', str(x), str(y))


if __name__ == '__main__':
    main()
