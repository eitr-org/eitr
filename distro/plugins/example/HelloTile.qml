import QtQuick
import Eitr as Eitr

Item {
    id: tile
    required property var api
    Component.onCompleted: tile.api.detail = Eitr.I18n.tr("Ready")
    Keys.onReturnPressed: tile.api.runDataCommand()
    Keys.onSpacePressed: tile.api.runDataCommand()
}
