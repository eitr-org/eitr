import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

PanelButton {
    required property var catalog

    id: button
    property bool primary: false
    readonly property bool hovered: buttonHover.hovered
    foreground: catalog.foreground
    outlined: !primary
    color: primary ? Qt.alpha(catalog.accent, hovered || activeFocus ? 0.34 : 0.24) : fillColor
    border.width: primary || outlined ? 1 : 0
    border.color: primary ? Qt.alpha(catalog.accent, 0.7) : selected || activeFocus ? catalog.accent : catalog.lineStrong
    HoverHandler { id: buttonHover }
}
