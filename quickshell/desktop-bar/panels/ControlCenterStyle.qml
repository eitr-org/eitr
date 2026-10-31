import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts
import "../PanelStyle.js" as PanelStyle

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "style"; width: parent.width; spacing: 12
    Text {
        visible: Object.keys(section.centerRef.styleErrors).length > 0
        width: parent.width; wrapMode: Text.WordWrap
        text: Object.keys(section.centerRef.styleErrors).map(key => key + ": " + section.centerRef.styleErrors[key]).join("\n")
        color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Theme & Wallpaper"); startOpen: true
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Theme"); glyph: "󰏘"; onClicked: section.centerRef.pickerRequested("theme") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Wallpaper"); glyph: "󰸉"; onClicked: section.centerRef.pickerRequested("wallpaper") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Fonts"); glyph: "󰛖"; onClicked: section.centerRef.walkerMenu("fonts") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Focus")
    RowLayout {
        width: parent.width
        Text { Layout.fillWidth: true; text: Eitr.I18n.tr("Distraction-free tabbed desktop"); color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; wrapMode: Text.WordWrap }
        PanelSwitch { checked: FocusMode.enabled; foreground: section.centerRef.foreground; accent: section.centerRef.accent; onClicked: FocusMode.select(checked) }
    }
    Text { width: parent.width; visible: FocusMode.error !== ""; text: FocusMode.error; color: section.centerRef.foreground; wrapMode: Text.Wrap; font.pixelSize: PanelStyle.captionSize }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Corners")
    Row {
        width: parent.width; spacing: 8
        Repeater {
            model: DesktopStyle.options
            PanelButton {
                required property var modelData
                width: (parent.width - 16) / 3
                text: Eitr.I18n.tr(modelData.label); textSize: 12
                foreground: section.centerRef.foreground
                selected: DesktopStyle.corners === modelData.key
                onClicked: DesktopStyle.select(modelData.key)
            }
        }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Bar")
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Layout") }
    Grid { width: parent.width; columns: 2; spacing: 8
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Full"); selected: section.centerRef.layout === "unified"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("layout", "unified") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Centered"); selected: section.centerRef.layout === "centered"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("layout", "centered") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Tabs"); selected: section.centerRef.layout === "notch"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("layout", "notch") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Islands"); selected: section.centerRef.layout === "islands"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("layout", "islands") }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Position") }
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        Repeater { model: ["top", "bottom", "left", "right"]
            PanelButton { textSize: 12; iconSize: 16; required property string modelData; Layout.fillWidth: true; text: modelData.charAt(0).toUpperCase() + modelData.slice(1); foreground: section.centerRef.foreground; selected: section.centerRef.barPosition === modelData; onClicked: section.centerRef.settingRequested("edge", modelData) }
        }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Appearance") }
    Row { width: parent.width; spacing: 8
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Blur"); selected: section.centerRef.appearance === "transparent"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("appearance", "transparent") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Theme Color"); selected: section.centerRef.appearance === "solid"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("appearance", "solid") }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Show on") }
    Row { width: parent.width; spacing: 8
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Main Display"); selected: section.centerRef.barScreens === "main"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("screens", "main") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("All Displays"); selected: section.centerRef.barScreens === "all"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("screens", "all") }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Clock") }
    Row { width: parent.width; spacing: 8
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("12-hour"); selected: section.centerRef.clockFormat === "12h"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("clock", "12h") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("24-hour"); selected: section.centerRef.clockFormat === "24h"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("clock", "24h") }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Media style") }
    Row { width: parent.width; spacing: 8
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Bars"); selected: section.centerRef.mediaStyle === "bars"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("mediaStyle", "bars") }
        PanelButton { textSize: 12; iconSize: 16; width: (parent.width - 8) / 2; text: Eitr.I18n.tr("Line"); selected: section.centerRef.mediaStyle === "line"; foreground: section.centerRef.foreground; onClicked: section.centerRef.settingRequested("mediaStyle", "line") }
    }
    ControlCenterOptionHeading { centerRef: section.centerRef; text: Eitr.I18n.tr("Behavior") }
    Row {
        width: parent.width; spacing: PanelStyle.selectionActionGap
        Text {
            width: parent.width - autoHideSwitch.width - parent.spacing; height: 32
            verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Auto-hide")
            color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            id: autoHideSwitch
            anchors.verticalCenter: parent.verticalCenter
            checked: section.centerRef.barAutoHide; foreground: section.centerRef.foreground; accent: section.centerRef.accent
            Accessible.name: Eitr.I18n.tr("Auto-hide")
            onClicked: section.centerRef.settingRequested("autohide", checked ? "yes" : "no")
        }
    }
    Row {
        width: parent.width; spacing: PanelStyle.selectionActionGap
        Text {
            width: parent.width - dockSwitch.width - parent.spacing; height: 32
            verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Dock")
            color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            id: dockSwitch
            anchors.verticalCenter: parent.verticalCenter
            checked: section.centerRef.barDock; foreground: section.centerRef.foreground; accent: section.centerRef.accent
            Accessible.name: Eitr.I18n.tr("Dock")
            onClicked: section.centerRef.settingRequested("dock", checked ? "yes" : "no")
        }
    }
    Row {
        width: parent.width; spacing: PanelStyle.selectionActionGap
        Text {
            width: parent.width - reduceMotionSwitch.width - parent.spacing; height: 32
            verticalAlignment: Text.AlignVCenter; text: Eitr.I18n.tr("Reduce motion")
            color: section.centerRef.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
        }
        PanelSwitch {
            id: reduceMotionSwitch
            anchors.verticalCenter: parent.verticalCenter
            checked: DesktopStyle.reduceMotion; foreground: section.centerRef.foreground; accent: section.centerRef.accent
            Accessible.name: Eitr.I18n.tr("Reduce motion")
            onClicked: section.centerRef.settingRequested("reduceMotion", checked ? "yes" : "no")
        }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Workspaces")
    Column { width: parent.width; spacing: 6
        Repeater { model: ["Dots", "Glyph", "Numbers", "Runes"]
            PanelButton {
                textSize: 12; iconSize: 16
                id: workspaceChoice
                required property string modelData
                width: parent.width; text: modelData; textAlignment: Text.AlignLeft
                foreground: section.centerRef.foreground; selected: section.centerRef.workspaceStyle === modelData
                onClicked: section.centerRef.workspaceStyleRequested(modelData)
                Row {
                    anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                    Repeater { model: 5
                        WorkspaceMarker { required property int index; style: workspaceChoice.modelData; label: String(index + 1); active: index === 1; foreground: section.centerRef.foreground; accent: section.centerRef.accent; selectedForeground: section.centerRef.background }
                    }
                }
            }
        }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
        title: Eitr.I18n.tr("Lockscreen")
        Column { width: parent.width; spacing: 6
            Repeater { model: section.centerRef.lockscreens
                PanelButton {
                    required property var modelData
                    width: parent.width; textSize: 12; text: Eitr.I18n.tr(modelData.label); textAlignment: Text.AlignLeft
                    leadingIcon: modelData.value === section.centerRef.lockscreen ? "\u{F00C}" : ""
                    foreground: section.centerRef.foreground; selected: modelData.value === section.centerRef.lockscreen
                    available: !section.centerRef.lockscreenWriteRef.running
                    onClicked: if (!selected) section.centerRef.run(section.centerRef.lockscreenWriteRef, ["python3", section.centerRef.lockscreenScript, "select", modelData.value])
                }
            }
        }
    }
    ControlCenterFold { centerRef: section.centerRef;
        title: Eitr.I18n.tr("Cursor")
        Repeater {
            model: [{key: "family", label: Eitr.I18n.tr("Family")}, {key: "size", label: Eitr.I18n.tr("Size")}, {key: "color", label: Eitr.I18n.tr("Color")}]
            Column {
                id: cursorGroup
                required property var modelData
                width: parent.width; spacing: 6
                ControlCenterOptionHeading { centerRef: section.centerRef; text: cursorGroup.modelData.label }
                Flow { width: parent.width; spacing: 6
                    Repeater { model: section.centerRef.cursorChoices[cursorGroup.modelData.key] || []
                        PanelButton {
                            required property var modelData
                            width: cursorGroup.modelData.key === "family" ? (parent.width - 6) / 2 : (parent.width - 18) / 4
                            textSize: 12; text: modelData.label.replace(" (Default)", "")
                            foreground: section.centerRef.foreground; selected: modelData.selected
                            available: !section.centerRef.cursorWriteRef.running
                            onClicked: if (!selected) section.centerRef.run(section.centerRef.cursorWriteRef, ["python3", section.centerRef.cursorScript, "set", cursorGroup.modelData.key, modelData.id])
                        }
                    }
                }
            }
        }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Terminal")
    Column { width: parent.width; spacing: 6
    Flow { width: parent.width; spacing: 6
        Repeater { model: section.centerRef.terminalChoices
            PanelButton {
                required property var modelData
                width: (parent.width - 6) / 2
                text: modelData.label
                foreground: section.centerRef.foreground; selected: section.centerRef.terminalChoice === modelData.value
                leadingIcon: selected ? "\u{F00C}" : ""
                available: !section.centerRef.terminalWriteRef.running
                onClicked: if (!selected) section.centerRef.run(section.centerRef.terminalWriteRef, ["python3", section.centerRef.terminalScript, "set", "terminal", modelData.value])
            }
        }
    }
    Item { width: parent.width; height: Math.max(32, terminalLabel.implicitHeight)
        ControlCenterLabel { centerRef: section.centerRef; id: terminalLabel; width: parent.width - 60; anchors.verticalCenter: parent.verticalCenter; wrapMode: Text.WordWrap; text: Eitr.I18n.tr("Cursor Fire: a blazing trail behind Kitty's cursor") }
        PanelSwitch {
            anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
            checked: section.centerRef.cursorFire; enabled: !section.centerRef.fireWriteRef.running && !section.centerRef.styleErrors.effects
            foreground: section.centerRef.foreground; accent: section.centerRef.accent
            onToggled: section.centerRef.run(section.centerRef.fireWriteRef, ["python3", section.centerRef.effectsScript, "set", "cursor-fire", checked ? "on" : "off"])
        }
    }
    }
    }
}
