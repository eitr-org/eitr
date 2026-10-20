import QtQuick
import Quickshell
import Eitr as Eitr
import ".." as Bar

ShellRoot {
    Component.onCompleted: {
        if (Quickshell.env("QT_QPA_PLATFORM") !== "offscreen") throw new Error("This fixture runs offscreen only");
        if (Eitr.I18n.locale !== Quickshell.env("EITR_TEST_LANGUAGE")) throw new Error("Message locale does not match LC_MESSAGES");
    }
    FloatingWindow {
        implicitWidth: 640; implicitHeight: 410
        visible: true
        Rectangle {
            id: sample
            anchors.fill: parent
            Row {
                Repeater {
                    model: [false, true]
                    Rectangle {
                        id: palette
                        required property bool modelData
                        width: 320; height: 410
                        color: modelData ? "#eff1e9" : "#18212b"
                        readonly property color foreground: modelData ? "#343c42" : "#e9eef1"
                        readonly property color accent: modelData ? "#617250" : "#c4914f"
                        Column {
                            x: 24; y: 24; width: 272; spacing: 12
                            Bar.PanelHeading {
                                width: parent.width
                                text: Eitr.I18n.tr("Notifications")
                                foreground: palette.foreground; accent: palette.accent
                            }
                            Bar.PanelDivider { width: parent.width; text: Eitr.I18n.tr("Connectivity"); foreground: palette.foreground }
                            Bar.ControlCenterTile {
                                width: 196; height: 44
                                title: Eitr.I18n.tr("Automatic idle lock")
                                subtitle: Eitr.I18n.tr("On"); glyph: "󰌾"
                                foreground: palette.foreground
                            }
                            Bar.ControlCenterTile {
                                width: 196; height: 44
                                title: Eitr.I18n.tr("Do Not Disturb")
                                subtitle: Eitr.I18n.tr("Off"); glyph: "󰂛"
                                foreground: palette.foreground
                            }
                            Bar.PanelHeading {
                                width: 230
                                text: Eitr.I18n.tr("Keyboard Layout")
                                foreground: palette.foreground; accent: palette.accent
                            }
                            Bar.PanelButton {
                                width: 110
                                text: Eitr.I18n.tr("Confirm removal")
                                foreground: palette.foreground
                            }
                            Text {
                                objectName: "barSlot"
                                width: 190; height: 28
                                text: new Date(2026, 8, 24, 17, 59).toLocaleString(Qt.locale(Eitr.I18n.systemLocale), "dddd d MMMM hh:mm")
                                color: palette.foreground
                                font.family: Bar.DesktopFonts.family; font.pixelSize: 13
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
        Timer {
            interval: 300; running: true
            onTriggered: {
                function inspect(item) {
                    if (item.visible && item.text !== undefined && item.contentWidth !== undefined && item.width > 0
                        && item.contentWidth > item.width + 1 && item.elide === Text.ElideNone && item.wrapMode === Text.NoWrap)
                        throw new Error("Unbounded translated text: " + item.text);
                    for (const child of item.children) inspect(child);
                }
                inspect(sample);
                sample.grabToImage(function(result) {
                    if (!result.saveToFile(Quickshell.env("EITR_TEST_CAPTURE"))) throw new Error("Could not save offscreen fixture");
                    console.log("I18N_LAYOUT_OK", Eitr.I18n.locale);
                    Qt.quit();
                });
            }
        }
    }
}
