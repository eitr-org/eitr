import ".."
import Eitr as Eitr
import QtQuick

// A spinning refresh glyph shown only while a panel loads. Panels refresh when
// they open, so there is no manual refresh button; this just shows the work.
PanelButton {
    id: indicator
    required property bool busy
    required property color background
    property string label: Eitr.I18n.tr("Updating")
    visible: busy
    width: 34; height: 32
    text: ""; icon: true; compactIconBackground: true; loading: true
    Accessible.name: label
    HoverHandler { id: hover }
    BarTooltip { target: indicator; hovered: hover.hovered; text: indicator.label; foreground: indicator.foreground; background: indicator.background }
}
