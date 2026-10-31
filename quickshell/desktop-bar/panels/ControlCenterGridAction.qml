import ".."
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts

PanelButton {
    required property var centerRef
    id: action
    property string tooltip: ""
    HoverHandler { id: actionHover; enabled: action.tooltip !== "" }
    BarTooltip { target: action; hovered: actionHover.hovered; text: action.tooltip; foreground: action.centerRef.foreground; background: action.centerRef.background }
    required property string title
    required property string glyph
    property url image: ""
    Layout.fillWidth: true; Layout.preferredWidth: 1; height: 34
    textSize: 12; iconSize: 16
    text: title; leadingIcon: glyph; leadingImage: image; foreground: action.centerRef.foreground; textAlignment: Text.AlignLeft
}
