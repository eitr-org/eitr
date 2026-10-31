import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Item {
    id: picker
    property bool opened: false
    property var defaultScreen: null
    property color foreground: "#ffffff"
    property color background: "#202024"
    property string requestId: ""
    property string title: ""
    property string subtitle: ""
    property int hour: 0
    property int minute: 0
    property int column: 0
    property string typed: ""
    property bool editing: false
    readonly property string digits: typed.length === 3 ? "0" + typed : typed
    readonly property bool valid: !editing || ((typed.length === 3 || typed.length === 4) && Number(digits.slice(0, 2)) < 24 && Number(digits.slice(2)) < 60)
    readonly property string value: editing ? digits.padEnd(4, "_").slice(0, 2) + ":" + digits.padEnd(4, "_").slice(2, 4) : pad(hour) + ":" + pad(minute)

    function pad(number) { return String(number).padStart(2, "0"); }
    function setValue(text) {
        const match = /^(\d{1,2}):(\d{2})$/.exec(text);
        if (!match || Number(match[1]) > 23 || Number(match[2]) > 59) return false;
        hour = Number(match[1]); minute = Number(match[2]);
        return true;
    }
    function open(request, question, detail, initial) {
        if ((request.length < 1 || request.length > 64 || /[^A-Za-z0-9_-]/.test(request)) || opened || writer.running) return;
        requestId = request; title = question; subtitle = detail; typed = ""; editing = false; column = 0;
        const next = new Date();
        if (!setValue(initial)) { hour = (next.getHours() + 1) % 24; minute = 0; }
        opened = true;
        Qt.callLater(function() { content.forceActiveFocus(); });
    }
    function step(which, delta) {
        if (!valid) return;
        setValue(value);
        typed = ""; editing = false; column = which;
        if (which === 0) hour = (hour + delta + 24) % 24;
        else minute = (minute + delta + 60) % 60;
    }
    function typeDigit(text) {
        // A full field starts over, so a typed time can always be retyped.
        if (!editing || typed.length >= 4) { typed = ""; editing = true; }
        typed += text;
    }
    function finish(cancelled) {
        if (!opened || writer.running) return;
        if (!cancelled && !valid) return;
        writer.command = ["python3", "-c",
            "import os,re,sys,tempfile\nfrom pathlib import Path\nrequest,value=sys.argv[1:]\nassert re.fullmatch(r'[A-Za-z0-9_-]{1,64}',request)\nassert not value or re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]\\n',value)\nbase=os.environ['XDG_RUNTIME_DIR']\nassert base.startswith('/')\ndirectory=Path(base)/'eitr-time-picker'\ndirectory.mkdir(mode=0o700,exist_ok=True)\ndirectory.chmod(0o700)\nfd,name=tempfile.mkstemp(dir=directory)\nwith os.fdopen(fd,'w') as output: output.write(value)\nos.replace(name,directory/request)",
            requestId, cancelled ? "" : value + "\n"];
        writer.running = true;
    }
    Process {
        id: writer
        onExited: function(code) { if (code === 0) picker.opened = false; }
    }
    IpcHandler {
        target: "timepicker"
        function open(request: string, title: string, subtitle: string, initial: string): void {
            picker.open(request, title, subtitle, initial);
        }
    }
    PanelWindow {
        visible: picker.opened
        screen: picker.defaultScreen || Quickshell.screens[0]
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        color: "transparent"
        WlrLayershell.namespace: "desktop-time-picker"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        Rectangle { anchors.fill: parent; color: "#80000000" }
        Item {
            id: content
            anchors.fill: parent
            focus: true
            Keys.onPressed: function(event) {
                if (event.key === Qt.Key_Escape) picker.finish(true);
                else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) picker.finish(false);
                else if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) picker.step(picker.column, event.key === Qt.Key_Up ? 1 : -1);
                else if ([Qt.Key_Left, Qt.Key_Right, Qt.Key_Tab, Qt.Key_Backtab].includes(event.key)) picker.column = 1 - picker.column;
                else if (event.key === Qt.Key_Backspace) { if (!picker.editing) picker.typed = picker.value.replace(":", ""); picker.editing = true; picker.typed = picker.typed.slice(0, -1); }
                else if (/^[0-9]$/.test(event.text)) picker.typeDigit(event.text);
                else return;
                event.accepted = true;
            }
            Rectangle {
                objectName: "timePickerCard"
                anchors.centerIn: parent
                width: Math.min(380, parent.width - 2 * PanelStyle.padding)
                height: layout.height + 2 * PanelStyle.padding
                radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                color: picker.background
                Column {
                    id: layout
                    x: PanelStyle.padding; y: PanelStyle.padding
                    width: parent.width - 2 * PanelStyle.padding
                    spacing: 12
                    Text {
                        width: parent.width; wrapMode: Text.Wrap
                        text: picker.title; color: picker.foreground
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.headingSize
                    }
                    Text {
                        width: parent.width; visible: text.length > 0; wrapMode: Text.Wrap
                        text: picker.subtitle; color: picker.foreground; opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    }
                    Text {
                        width: parent.width; height: 64
                        text: picker.value; horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: picker.valid ? picker.foreground : "#d04b4b"
                        font.family: DesktopFonts.family; font.pixelSize: 40
                        font.features: PanelStyle.tabularFigures
                    }
                    Item {
                        width: parent.width; height: 2
                        Rectangle {
                            width: 48; height: 2
                            x: parent.width / 2 + (picker.column === 0 ? -60 : 12)
                            color: picker.foreground
                        }
                    }
                    Row {
                        anchors.right: parent.right; spacing: 8
                        PanelButton {
                            width: 100
                            text: Eitr.I18n.tr("Cancel"); foreground: picker.foreground
                            Keys.forwardTo: [content]
                            activeFocusOnTab: false
                            onClicked: picker.finish(true)
                        }
                        PanelButton {
                            width: 100
                            enabled: picker.valid
                            text: Eitr.I18n.tr("Set"); foreground: picker.foreground
                            Keys.forwardTo: [content]
                            activeFocusOnTab: false
                            onClicked: picker.finish(false)
                        }
                    }
                }
            }
        }
    }
}
