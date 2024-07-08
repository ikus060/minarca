# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
import subprocess
import time
import xml.etree.ElementTree as et

from minarca_client.locale import _

try:
    from importlib.resources import resource_filename
except ImportError:
    # For Python 2 or Python 3 with older setuptools
    from pkg_resources import resource_filename

APP_ID = 'Minarca'

__all__ = ['send_notification', 'clear_notification']

_xml = """
<toast activationType="protocol" launch="http:">
    <visual>
        <binding template='ToastGeneric'></binding>
    </visual>
</toast>
"""

NOTIFY_PS1 = """
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
{xml}
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$notification = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}').Show($notification)
"""

REMOVE_PS1 = """
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotificationManager]::history.Remove('{tag}', '{group}', '{app_id}')
"""


def _add_button(button, toast):
    if isinstance(button, str):
        button = {'activationType': 'protocol', 'arguments': 'http:' + button, 'content': button}
    actions = toast.find('actions') or et.SubElement(toast, 'actions')
    action = et.SubElement(actions, 'action')
    for name, value in button.items():
        action.attrib[name] = value


def _add_icon(icon, toast):
    if isinstance(icon, str):
        icon = {'placement': 'appLogoOverride', 'hint-crop': 'circle', 'src': icon}
    binding = toast.find('visual/binding')
    image = et.SubElement(binding, 'image')
    for name, value in icon.items():
        image.attrib[name] = value


def _add_text(value, toast):
    binding = toast.find('visual/binding')
    text = et.SubElement(binding, 'text')
    text.text = value


def _run(input_script):
    cmd = ['powershell', '-noprofile', '-noninteractive', '-command', '-']
    p = subprocess.run(
        cmd,
        input=input_script.encode('utf8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if p.stderr or p.returncode != 0:
        raise subprocess.CalledProcessError(returncode=p.returncode, cmd=cmd, output=p.stdout, stderr=p.stderr)
    return p.stdout


def _notify(
    title=None, body=None, icon=None, duration=None, button=None, buttons=[], scenario=None, tag=None, group=None
):
    """
    Show a ToastNotification using PowerShell script.
    """
    toast = et.fromstring(_xml)
    toast.attrib['scenario'] = scenario if scenario else 'default'
    if duration:
        toast.attrib['duration'] = duration
    if title:
        _add_text(title, toast)
    if body:
        _add_text(body, toast)
    if button:
        _add_button(button, toast)
    if buttons:
        for button in buttons:
            _add_button(button, toast)
    if icon:
        _add_icon(icon, toast)
    _run(NOTIFY_PS1.format(app_id=APP_ID, tag=tag, group=group, xml=et.tostring(toast, encoding='unicode')))
    return tag


def _clear(tag=None, group=None):
    """
    Clear notification identified by app_id, tag & group using PowerShell script.
    """
    _run(REMOVE_PS1.format(app_id=APP_ID, tag=tag, group=group))


def send_notification(title, body, replace_id=None):
    icon = resource_filename('minarca_client', 'ui/theme/resources/minarca.ico')
    icon_def = None
    if os.path.isfile(icon):
        icon_def = {'src': icon, 'placement': 'appLogoOverride'}

    # Generate or reuse notificaiton id as tag.
    if replace_id:
        tag = replace_id
    else:
        tag = str(int(time.time()))

    # This make use of "minarca://" protocol.
    buttons = [{'activationType': 'protocol', 'arguments': 'minarca://test', 'content': _('Show details')}]
    _notify(title=title, body=body, icon=icon_def, buttons=buttons, tag=tag, group='default')
    return tag


def clear_notification(notification_id):
    # On Windows, we make use of tag & groupe to clear a notification.
    _clear(tag=notification_id, group='default')
