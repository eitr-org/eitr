import ".."
import QtQuick
import Eitr as Eitr
import "SettingsIndex.js" as SettingsIndex

FamilyPageHeader {
    id: header
    required property string page
    readonly property var entry: SettingsIndex.entry(page)
    readonly property var pageGroup: SettingsIndex.groupFor(entry)
    rune: pageGroup.rune
    group: Eitr.I18n.tr(pageGroup.name)
    title: Eitr.I18n.tr(entry.title)
    description: Eitr.I18n.tr(entry.description)
}
