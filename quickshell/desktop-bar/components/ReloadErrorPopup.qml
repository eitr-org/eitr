import ".."
import Eitr as Eitr
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../PanelStyle.js" as PanelStyle

Scope {
    id: root
    required property color foreground
    required property color background
    required property var targetScreen
    property string barEdge: "top"
    property string errorMessage: ""
    readonly property bool showing: popupLoader.active
    readonly property var popupWindow: popupLoader.item

    function showError(message) {
        errorMessage = message;
        popupLoader.active = true;
    }
    function dismiss() { popupLoader.active = false; }

    Connections {
        target: Quickshell
        function onReloadCompleted() {
            Quickshell.inhibitReloadPopup();
            root.dismiss();
        }
        function onReloadFailed(errorString) {
            Quickshell.inhibitReloadPopup();
            root.showError(errorString);
        }
    }

    LazyLoader {
        id: popupLoader
        PanelWindow {
            id: popup
            screen: root.targetScreen
            color: "transparent"
            implicitWidth: Math.min(560, (screen ? screen.width : 600) - 24)
            implicitHeight: content.implicitHeight + PanelStyle.padding * 2
            anchors { top: root.barEdge !== "bottom"; bottom: root.barEdge === "bottom"; right: root.barEdge !== "left"; left: root.barEdge === "left" }
            margins { top: root.barEdge === "top" ? 42 : 12; bottom: 42; left: root.barEdge === "left" ? 42 : 12; right: root.barEdge === "right" ? 42 : 12 }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "desktop-reload-error"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

            Rectangle {
                anchors.fill: parent
                radius: DesktopStyle.radius(PanelStyle.cornerRadius)
                color: root.background
                border.width: 1
                border.color: Qt.alpha(root.foreground, 0.2)
                focus: true
                Keys.onEscapePressed: root.dismiss()

                Column {
                    id: content
                    x: PanelStyle.padding; y: PanelStyle.padding
                    width: parent.width - PanelStyle.padding * 2
                    spacing: 12
                    Row {
                        width: parent.width; spacing: 12
                        PanelHeading {
                            width: parent.width - 46; height: 34
                            text: Eitr.I18n.tr("Quickshell reload failed")
                            foreground: root.foreground; accent: root.foreground; rune: "protection"
                        }
                        PanelButton {
                            width: 34; height: 34; icon: true; text: "󰅖"
                            foreground: root.foreground
                            onClicked: root.dismiss()
                        }
                    }
                    Text {
                        width: parent.width
                        text: Eitr.I18n.tr("Your last working configuration is still running.")
                        textFormat: Text.PlainText
                        color: root.foreground
                        font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
                        wrapMode: Text.Wrap
                    }
                    Rectangle { width: parent.width; height: 1; color: Qt.alpha(root.foreground, 0.15) }
                    Flickable {
                        width: parent.width
                        height: Math.min(errorText.implicitHeight, Math.max(60, Math.min(300, (popup.screen ? popup.screen.height : 800) - 180)))
                        contentWidth: width
                        contentHeight: errorText.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        TextEdit {
                            id: errorText
                            width: parent.width
                            text: root.errorMessage
                            textFormat: TextEdit.PlainText
                            readOnly: true; selectByMouse: true
                            color: root.foreground
                            selectionColor: Qt.alpha(root.foreground, 0.25)
                            selectedTextColor: root.foreground
                            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                            wrapMode: TextEdit.WrapAnywhere
                            Keys.onEscapePressed: root.dismiss()
                        }
                    }
                }
            }
        }
    }
}
