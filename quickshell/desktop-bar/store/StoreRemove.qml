import ".."
import QtQuick
import Eitr as Eitr

StoreSheet {
    id: root
    property alias removePackagesChoice: packagesChoice
    visible: catalog.removing !== null
    heading: Eitr.I18n.tr("Remove %1?").arg(catalog.removing ? catalog.removing.name : "")
    description: catalog.kind === "lockscreens" ? Eitr.I18n.tr("Your own lockscreens using this design are hidden until you reinstall it.") : catalog.kind === "plugins" ? Eitr.I18n.tr("The plugin and its files are deleted from this computer.") : catalog.kind === "wallpapers" ? Eitr.I18n.tr("Only this pack’s wallpaper files are deleted.") : Eitr.I18n.tr("The theme is deleted from this computer.")
    confirmText: Eitr.I18n.tr("Remove")
    Row {
        visible: root.catalog.kind === "plugins" && !!root.catalog.removing && (root.catalog.removing.removablePackages || []).length > 0
        width: parent.width; spacing: 10
        onVisibleChanged: packagesChoice.checked = false
        PanelSwitch { id: packagesChoice; anchors.verticalCenter: parent.verticalCenter; foreground: root.catalog.foreground; accent: root.catalog.accent; checked: false }
        StoreLabel {
            catalog: root.catalog
            width: parent.width - packagesChoice.width - parent.spacing; anchors.verticalCenter: parent.verticalCenter; wrapMode: Text.WordWrap
            text: Eitr.I18n.tr("Remove unused plugin-installed packages: {packages}?").replace("{packages}", root.catalog.removing ? (root.catalog.removing.removablePackages || []).join(", ") : "")
            MouseArea { anchors.fill: parent; onClicked: packagesChoice.checked = !packagesChoice.checked }
        }
    }
    StoreLabel { catalog: root.catalog; visible: text !== ""; text: root.catalog.busy ? root.catalog.progress : root.catalog.error; width: parent.width }
}
