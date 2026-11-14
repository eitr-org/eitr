import ".."
import QtQuick
import Eitr as Eitr

// What a catalog section shows without items: the Community welcome card when the
// community index loaded and is empty, otherwise the empty or failure message (Retry
// only after a failed load).
Item {
    id: emptyState
    required property var catalogContext
    required property var sectionContext
    required property real viewportHeight
    readonly property bool welcome: catalogContext.communityEmpty && !sectionContext.modelData.local
    visible: !sectionContext.items.length
    width: parent ? parent.width : 0
    height: visible ? viewportHeight : 0
    Column {
        anchors.centerIn: parent
        width: parent.width - 40
        spacing: 14
        ControlCard {
            objectName: "catalog-community-welcome"
            visible: emptyState.welcome
            width: Math.min(520, parent.width)
            anchors.horizontalCenter: parent.horizontalCenter
            foreground: emptyState.catalogContext.foreground
            surface: emptyState.catalogContext.surface; line: emptyState.catalogContext.line; gold: emptyState.catalogContext.gold; carved: true
            spacing: 14
            title: Eitr.I18n.tr("No community items yet")
            SettingsText {
                text: Eitr.I18n.tr("Try another source filter or check again later.")
                color: emptyState.catalogContext.foreground
            }
            PanelButton {
                width: 170; outlined: true; text: Eitr.I18n.tr("All"); foreground: emptyState.catalogContext.foreground
                onClicked: emptyState.catalogContext.sourceFilter = "all"
            }
        }
        SettingsText {
            visible: !emptyState.welcome
            horizontalAlignment: Text.AlignHCenter
            text: emptyState.sectionContext.pageError || (emptyState.sectionContext.modelData.local ? Eitr.I18n.tr("No installed items match this filter.") : Eitr.I18n.tr("No items match this filter."))
            color: emptyState.catalogContext.muted
        }
        PanelButton {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: !emptyState.welcome && emptyState.sectionContext.pageError !== ""
            width: 90; outlined: true; text: Eitr.I18n.tr("Retry"); foreground: emptyState.catalogContext.foreground
            onClicked: {
                emptyState.catalogContext.previewRequests = ({});
                if (emptyState.sectionContext.modelData.local) emptyState.catalogContext.refreshInstalled();
                else emptyState.catalogContext.refreshIndex();
            }
        }
    }
}
