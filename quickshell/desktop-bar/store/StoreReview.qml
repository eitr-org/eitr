import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: root
    required property var catalog
    property alias addressInput: addressInput

    objectName: "native-review"; z: 4; anchors.fill: parent
    visible: catalog.nativeReviewing || catalog.addingAddress
    color: Qt.alpha(catalog.background, 0.94)
    MouseArea { anchors.fill: parent }
    Rectangle {
        anchors.centerIn: parent; width: parent.width - (catalog.compact ? 32 : 100); height: parent.height - 40
        color: catalog.surface; radius: DesktopStyle.radius(12); border.width: 1; border.color: catalog.line
        Column {
            anchors.fill: parent; anchors.margins: 24; spacing: 16
            StoreLabel { catalog: root.catalog; width: parent.width; font.family: SiteStyle.carved; font.pixelSize: 22; text: catalog.addingAddress ? Eitr.I18n.tr("Add from a Git address") : catalog.nativeReview && catalog.nativeReview.changes && catalog.nativeReview.changes.new ? Eitr.I18n.tr("Review plugin update") : catalog.nativeReview && catalog.nativeReview.choices ? (catalog.kind === "themes" ? Eitr.I18n.tr("Choose themes") : Eitr.I18n.tr("Choose plugins")) : catalog.pluginQueueTotal > 1 ? Eitr.I18n.tr("Review plugin %1 of %2").arg(catalog.pluginQueueTotal - catalog.pluginQueue.length).arg(catalog.pluginQueueTotal) : catalog.kind === "themes" ? Eitr.I18n.tr("Review theme installation") : Eitr.I18n.tr("Review plugin installation") }
            Column {
                visible: catalog.addingAddress; width: parent.width; spacing: 14
                StoreLabel { catalog: root.catalog; width: parent.width; text: Eitr.I18n.tr("HTTPS or SSH Git address"); color: catalog.muted }
                TextField { id: addressInput; objectName: "git-address"; width: parent.width; color: catalog.foreground; placeholderText: "https://…"; placeholderTextColor: catalog.muted; font.family: SiteStyle.mono; selectionColor: catalog.accent; selectedTextColor: catalog.foreground; background: Rectangle { color: catalog.raised; radius: 4; border.width: 1; border.color: catalog.lineStrong } selectByMouse: true; onAccepted: catalog.prepareReview({url: text.trim()}) }
                StoreLabel { catalog: root.catalog; width: parent.width; text: catalog.kind === "plugins" ? Eitr.I18n.tr("Plugins run with your account's full permissions") : Eitr.I18n.tr("Data-only themes · Review selected sources"); color: catalog.muted }
            }
            Flickable {
                width: parent.width; height: Math.max(40, parent.height - 150); visible: !catalog.addingAddress
                contentWidth: width; contentHeight: reviewColumn.height; clip: true; boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                Column {
                    id: reviewColumn; width: parent.width - 12; spacing: 14
                    readonly property var facts: catalog.nativeReview || ({})
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: catalog.busy ? Eitr.I18n.tr("Loading…") : catalog.error; color: catalog.muted }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: !!catalog.nativeReview; text: reviewColumn.facts.dataOnly ? Eitr.I18n.tr("Data-only themes · Review selected sources") : Eitr.I18n.tr("Plugins run with your account's full permissions"); font.bold: true }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: !!catalog.nativeReview && !reviewColumn.facts.dataOnly; text: reviewColumn.facts.official ? Eitr.I18n.tr("Official Eitr plugin") : Eitr.I18n.tr("Eitr has not reviewed it. Its code belongs to its author, not to Eitr. Only add plugins from people and repositories you trust."); color: reviewColumn.facts.official ? catalog.muted : catalog.accent; font.bold: !reviewColumn.facts.official }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: !reviewColumn.facts.themes && text !== ""; text: (reviewColumn.facts.spec || {}).name || ""; font.family: SiteStyle.carved; font.pixelSize: 22 }
                    StoreLabel { catalog: root.catalog; width: parent.width; text: [reviewColumn.facts.url, reviewColumn.facts.folder, reviewColumn.facts.commit, reviewColumn.facts.author, (reviewColumn.facts.spec || {}).author, (reviewColumn.facts.spec || {}).version, reviewColumn.facts.license].filter(value => value).join("\n"); wrapMode: Text.WrapAnywhere; color: catalog.muted }
                    Flow {
                        width: reviewColumn.width; spacing: 14
                        visible: !!reviewColumn.facts.choices || catalog.kind === "themes" && !!reviewColumn.facts.themes
                        Repeater { model: reviewColumn.facts.choices || (catalog.kind === "themes" ? reviewColumn.facts.themes || [] : [])
                            StoreGitThemeCard { catalog: root.catalog; required property var modelData; row: modelData; selectable: !!reviewColumn.facts.choices; width: Math.floor((reviewColumn.width - 14 * (catalog.columns - 1)) / catalog.columns) }
                        }
                    }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: catalog.componentsText(reviewColumn.facts.spec || {}); wrapMode: Text.WrapAnywhere }
                    StoreLabel { catalog: root.catalog; width: parent.width; text: Eitr.I18n.tr("System packages"); font.bold: true; visible: (reviewColumn.facts.packages || []).length > 0 }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: (reviewColumn.facts.packages || []).length > 0; color: catalog.muted; text: Eitr.I18n.tr("Missing packages require the administrator password.") + "\n" + (reviewColumn.facts.packages || []).map(package => package.installed ? Eitr.I18n.tr("{name} · already installed").replace("{name}", package.name) : Eitr.I18n.tr("{name} · will be installed").replace("{name}", package.name)).join("\n"); wrapMode: Text.WrapAnywhere }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: (reviewColumn.facts.flags || []).join("\n"); color: catalog.accent; wrapMode: Text.WrapAnywhere }
                    StoreLabel { catalog: root.catalog; width: parent.width; text: Eitr.I18n.tr("Files"); font.bold: true; visible: (reviewColumn.facts.files || []).length > 0 }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: (reviewColumn.facts.files || []).join("\n"); wrapMode: Text.WrapAnywhere; color: catalog.muted }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: reviewColumn.facts.changes && reviewColumn.facts.changes.new ? [reviewColumn.facts.changes.old + " → " + reviewColumn.facts.changes.new].concat(reviewColumn.facts.changes.subjects || [], (reviewColumn.facts.changes.files || []).map(file => file.status + " " + file.path + " +" + file.added + " −" + file.removed), reviewColumn.facts.changes.flags || []).join("\n") : ""; wrapMode: Text.WrapAnywhere }
                    Repeater { model: reviewColumn.facts.qml || []
                        StoreActionButton { catalog: root.catalog; required property var modelData; width: reviewColumn.width; text: modelData.path; onClicked: catalog.loadReviewSource(modelData.path, 0) }
                    }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: !!catalog.reviewSourcePath; text: catalog.reviewSourcePath + "\n" + catalog.reviewSourceText; font.family: SiteStyle.mono; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
                    Row { spacing: 10; visible: !!catalog.reviewSourcePath
                        StoreActionButton { catalog: root.catalog; width: 100; text: Eitr.I18n.tr("Previous"); available: catalog.reviewSourceOffset > 0; onClicked: catalog.loadReviewSource(catalog.reviewSourcePath, Math.max(0, catalog.reviewSourceOffset - 16384)) }
                        StoreActionButton { catalog: root.catalog; width: 100; text: Eitr.I18n.tr("Next"); available: catalog.reviewSourceOffset + 16384 < catalog.reviewSourceTotal; onClicked: catalog.loadReviewSource(catalog.reviewSourcePath, catalog.reviewSourceOffset + 16384) }
                    }
                    StoreActionButton { catalog: root.catalog; width: 220; visible: !!reviewColumn.facts.assistant; available: !catalog.busy; text: Eitr.I18n.tr("Ask the AI to check"); onClicked: { catalog.busy = true; catalog.request("advice", {token: catalog.nativeReview.token}, function(failure, data) { catalog.busy = false; catalog.advice = failure || (data.answer || []).join("\n"); }); } }
                    StoreLabel { catalog: root.catalog; width: parent.width; visible: text !== ""; text: catalog.advice; wrapMode: Text.WrapAnywhere }
                }
            }
            Row {
                spacing: 12
                StoreActionButton { catalog: root.catalog; width: 110; text: Eitr.I18n.tr("Cancel"); available: !catalog.confirmingReview; onClicked: { DesktopData.releaseOwner(catalog); catalog.busy = false; catalog.addingAddress = false; catalog.discardReview(); catalog.forceActiveFocus(); } }
                StoreActionButton { catalog: root.catalog; objectName: "address-review"; width: 110; visible: catalog.addingAddress; primary: true; text: Eitr.I18n.tr("Review"); onClicked: catalog.prepareReview({url: catalog.addressInput.text.trim()}) }
                StoreActionButton { catalog: root.catalog; objectName: "git-continue"; width: 150; visible: !!catalog.nativeReview && !!catalog.nativeReview.choices; primary: true; available: catalog.gitSelected.length > 0 && !catalog.busy
                    text: catalog.gitSelected.length > 1 ? Eitr.I18n.tr("Continue · %1").arg(catalog.gitSelected.length) : Eitr.I18n.tr("Continue")
                    onClicked: { if (catalog.kind === "plugins") catalog.reviewChosenPlugins(); else catalog.prepareReview({url: catalog.nativeReview.url, ids: catalog.gitSelected}); } }
                StoreActionButton { catalog: root.catalog; objectName: "native-confirm"; width: 110; visible: !!catalog.nativeReview && !!catalog.nativeReview.token; available: !catalog.busy; primary: true; text: Eitr.I18n.tr("Confirm"); onClicked: catalog.nativeConfirm() }
            }
        }
    }
}
