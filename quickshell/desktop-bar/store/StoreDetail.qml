import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    required property var catalog
    property alias detailScroll: detailScroll
    property alias videoPlayer: pluginVideo

    id: detailSheet
    enabled: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing
    z: 2
    objectName: catalog.kind === "plugins" ? "plugin-detail" : "theme-detail"
    anchors.fill: parent; visible: catalog.detail !== null
    color: Qt.alpha(catalog.background, 0.90); radius: 0
    MouseArea { anchors.fill: parent; onClicked: catalog.closeDetail() }
    Rectangle {
        anchors.centerIn: parent; width: parent.width - (catalog.compact ? 32 : 100); height: parent.height - 40
        color: catalog.surface; radius: DesktopStyle.radius(12); border.width: 1; border.color: catalog.line
        MouseArea { anchors.fill: parent }
        Flickable {
            id: detailScroll
            objectName: "detail-scroll"
            anchors.fill: parent; anchors.margins: 22; anchors.topMargin: 52; anchors.bottomMargin: 70
            contentWidth: width; contentHeight: detailColumn.height; clip: true
            boundsBehavior: Flickable.StopAtBounds; ScrollBar.vertical: ScrollBar {}
            Column {
                id: detailColumn
                width: parent.width - 12; spacing: 16
                Image {
                    visible: catalog.capabilities.useOnClick
                    width: parent.width; height: !visible ? 0 : source.toString() ? Math.min(catalog.wallpaperIndex >= 0 ? 480 : 260, width * 9 / 16) : 0
                    source: catalog.wallpaperIndex >= 0 && catalog.wallpaperIndex < catalog.wallpapers.length ? catalog.artworkFor(catalog.wallpapers[catalog.wallpaperIndex], false) : catalog.imageFor(catalog.detailItem)
                    sourceSize: Qt.size(1200, 700); fillMode: Image.PreserveAspectFit; asynchronous: true
                }
                Column {
                    visible: catalog.kind === "plugins"; width: parent.width; spacing: 10
                    Item {
                        width: parent.width; height: Math.min(300, width * 9 / 16)
                        readonly property bool video: catalog.currentMedia.type === "video"
                        Image { anchors.fill: parent; visible: !parent.video || catalog.videoPosterOnly; source: parent.video ? catalog.imageFor(catalog.detailItem) : catalog.pluginMedia.length ? catalog.artworkFor(catalog.currentMedia, false) : catalog.imageFor(catalog.detailItem); fillMode: Image.PreserveAspectFit; sourceSize: Qt.size(1200, 700); asynchronous: true }
                        StoreLabel { catalog: detailSheet.catalog; anchors.centerIn: parent; visible: !catalog.pluginMedia.length && !catalog.imageFor(catalog.detailItem); text: "󰏗"; font.pixelSize: 80 }
                        VideoOutput { id: videoOutput; objectName: "plugin-video-output"; anchors.fill: parent; visible: parent.video && !catalog.videoPosterOnly; fillMode: VideoOutput.PreserveAspectFit }
                        Component { id: audioFactory; AudioOutput { muted: false } }
                        MediaPlayer {
                            id: pluginVideo; objectName: "plugin-video-player"
                            source: catalog.opened && catalog.detail && catalog.kind === "plugins" && catalog.currentMedia.type === "video" ? catalog.artworkFor(catalog.currentMedia, false) : ""
                            videoOutput: videoOutput
                            property bool muted: !audioOutput || audioOutput.muted
                            loops: MediaPlayer.Infinite; autoPlay: true
                            onSourceChanged: { if (audioOutput) audioOutput.muted = true; }
                            onErrorOccurred: catalog.detailError = errorString
                        }
                    }
                    Row {
                        visible: catalog.currentMedia.type === "video"; spacing: 10
                        StoreActionButton { catalog: detailSheet.catalog; width: 110; text: pluginVideo.playbackState === MediaPlayer.PlayingState ? Eitr.I18n.tr("Pause") : Eitr.I18n.tr("Play"); onClicked: { if (pluginVideo.playbackState === MediaPlayer.PlayingState) pluginVideo.pause(); else pluginVideo.play(); } }
                        StoreActionButton { catalog: detailSheet.catalog; width: 110; text: pluginVideo.muted ? Eitr.I18n.tr("Unmute") : Eitr.I18n.tr("Mute"); onClicked: { if (!pluginVideo.audioOutput) pluginVideo.audioOutput = audioFactory.createObject(pluginVideo); else pluginVideo.audioOutput.muted = !pluginVideo.audioOutput.muted; } }
                    }
                    Flickable {
                        width: parent.width; height: 76; contentWidth: mediaStrip.width; clip: true
                        Row { id: mediaStrip; spacing: 8
                            Repeater { model: catalog.pluginMedia
                                Rectangle {
                                    required property var modelData
                                    required property int index
                                    width: 110; height: 70; radius: DesktopStyle.radius(6); color: catalog.raised
                                    border.width: 1; border.color: catalog.mediaIndex === index ? catalog.accent : catalog.line
                                    Image { anchors.fill: parent; anchors.margins: 2; visible: parent.modelData.type === "image"; source: parent.modelData.type === "image" ? catalog.artworkFor(parent.modelData, false) : ""; sourceSize: Qt.size(220, 140); fillMode: Image.PreserveAspectCrop }
                                    StoreLabel { catalog: detailSheet.catalog; anchors.centerIn: parent; text: parent.modelData.type === "video" ? "▶" : String(parent.index + 1) }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catalog.selectMedia(parent.index) }
                                }
                            }
                        }
                    }
                    StoreLabel { catalog: detailSheet.catalog; width: parent.width; text: catalog.currentMedia.caption || ""; color: catalog.muted }
                }
                Row {
                    visible: catalog.wallpaperIndex >= 0; spacing: 10
                    StoreActionButton { catalog: detailSheet.catalog; objectName: "wallpaper-back"; width: 100; text: Eitr.I18n.tr("Back"); onClicked: catalog.wallpaperIndex = -1 }
                    StoreActionButton { catalog: detailSheet.catalog; width: 100; text: Eitr.I18n.tr("Previous"); available: catalog.wallpaperIndex > 0; onClicked: catalog.showWallpaper(catalog.wallpaperIndex - 1) }
                    StoreActionButton { catalog: detailSheet.catalog; width: 100; text: Eitr.I18n.tr("Next"); available: catalog.wallpaperIndex < catalog.wallpapers.length - 1; onClicked: catalog.showWallpaper(catalog.wallpaperIndex + 1) }
                }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.wallpaperIndex >= 0; width: parent.width; text: catalog.wallpaperIndex >= 0 && catalog.wallpaperIndex < catalog.wallpapers.length ? catalog.wallpapers[catalog.wallpaperIndex].path.split("/").pop() : ""; color: catalog.muted }
                Column {
                    width: parent.width; spacing: 16; visible: catalog.wallpaperIndex < 0
                StoreLabel { catalog: detailSheet.catalog; width: parent.width; text: catalog.detailItem.name || ""; font.family: SiteStyle.carved; font.pixelSize: 24; font.letterSpacing: 1 }
                StoreLabel { catalog: detailSheet.catalog; width: parent.width; text: catalog.detailItem.description || ""; color: catalog.muted }
                Flow {
                    width: parent.width; spacing: 8
                    Repeater {
                        model: Object.keys(catalog.detailItem.palette || {})
                        Rectangle {
                            id: swatch
                            required property string modelData
                            width: 24; height: 24; radius: 12; color: catalog.detailItem.palette[modelData]
                            border.width: 1; border.color: catalog.lineStrong
                            MouseArea { id: swatchMouse; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton }
                            BarTooltip { target: swatch; hovered: swatchMouse.containsMouse; text: swatch.modelData + " " + catalog.detailItem.palette[swatch.modelData]; foreground: catalog.foreground; background: catalog.raised }
                        }
                    }
                }
                Flow {
                    width: parent.width; spacing: 8
                    StorePill { catalog: detailSheet.catalog; text: catalog.badge(catalog.detailItem) }
                    StorePill { catalog: detailSheet.catalog; visible: typeof catalog.detailItem.light === "boolean"; text: catalog.detailItem.light ? Eitr.I18n.tr("Light") : Eitr.I18n.tr("Dark") }
                    StorePill { catalog: detailSheet.catalog; visible: catalog.isInstalled(catalog.detailItem); text: Eitr.I18n.tr("Installed") }
                    StorePill { catalog: detailSheet.catalog; visible: catalog.detailItem.enabled === false; text: Eitr.I18n.tr("Disabled") }
                    StorePill { catalog: detailSheet.catalog; visible: !!catalog.detailItem.current; current: true; text: Eitr.I18n.tr("Current") }
                }
                StoreLabel { catalog: detailSheet.catalog;
                    width: parent.width
                    text: [catalog.detailItem.author || "", catalog.detailItem.maintainer || (["builtin", "official"].includes(catalog.detailItem.kind) ? Eitr.I18n.tr("The Eitr project") : ""), catalog.detailItem.license || (catalog.kind === "themes" && ["builtin", "official"].includes(catalog.detailItem.kind) ? "GPL-3.0" : "")].filter(value => value).join(" · ")
                    color: catalog.muted
                }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.kind === "plugins"; width: parent.width; text: (catalog.detailItem.version || "") + (catalog.tab === "community" ? " · " + (catalog.detailItem.commit || "").slice(0, 12) : ""); color: catalog.muted }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.kind === "plugins"; width: parent.width; text: catalog.componentsText(catalog.detailItem.components || {}); color: catalog.muted }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.capabilities.useOnClick; width: parent.width; text: catalog.sizeText(catalog.detailItem.size || 0); color: catalog.muted }
                StoreLabel { catalog: detailSheet.catalog; width: parent.width; text: (catalog.detailItem.repository || (catalog.detailItem.source || {}).url || (catalog.detailItem.kind === "builtin" ? "eitr-org/eitr" : catalog.detailItem.kind === "official" ? "eitr-org/eitr-themes" : "")) + " / " + (catalog.detailItem.folder || catalog.detailItem.repositoryPath || (catalog.detailItem.source || {}).folder || (catalog.kind === "plugins" ? "." : "themes/" + (catalog.detailItem.id || ""))); color: catalog.muted; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
                Rectangle { width: parent.width; height: 1; color: catalog.line }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.capabilities.useOnClick; text: Eitr.I18n.tr("Wallpapers"); font.family: SiteStyle.carved; font.pixelSize: 18 }
                StoreLabel { catalog: detailSheet.catalog; visible: catalog.capabilities.useOnClick && catalog.wallpapers.length === 0; text: Eitr.I18n.tr("No wallpapers"); color: catalog.muted }
                Flow {
                    width: parent.width; spacing: 10
                    Repeater {
                        model: catalog.wallpapers
                        Rectangle {
                            id: wallpaperTile
                            required property var modelData
                            required property int index
                            objectName: "wallpaper-" + index
                            width: Math.min(210, detailColumn.width); height: modelData.thumbnail || modelData.imageUrl ? 146 : 76
                            color: catalog.raised; radius: DesktopStyle.radius(8); border.width: 1; border.color: catalog.line
                            Image { x: 1; y: 1; width: parent.width - 2; height: 100; visible: !!wallpaperTile.modelData.thumbnail || !!wallpaperTile.modelData.imageUrl; source: catalog.artworkFor(wallpaperTile.modelData, true); sourceSize: Qt.size(480, 270); asynchronous: true; fillMode: Image.PreserveAspectCrop }
                            Column { x: 8; y: wallpaperTile.height - 42; width: parent.width - 16; spacing: 3
                                StoreLabel { catalog: detailSheet.catalog; width: parent.width; text: wallpaperTile.modelData.path.split("/").pop(); maximumLineCount: 1; elide: Text.ElideMiddle; font.pixelSize: 11 }
                                StoreLabel { catalog: detailSheet.catalog; text: catalog.sizeText(wallpaperTile.modelData.size); color: catalog.muted; font.pixelSize: 11 }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catalog.showWallpaper(wallpaperTile.index) }
                        }
                    }
                }
                StoreLabel { catalog: detailSheet.catalog; width: parent.width; visible: text !== ""; text: catalog.detailError || catalog.error; color: catalog.muted }
                }

            }
        }
                StoreActionButton { catalog: detailSheet.catalog;
                    objectName: "detail-install"
                    anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 22
                    width: 150; primary: true; available: !catalog.busy
                    visible: (catalog.tab === "updates" || !catalog.detailItem.current) && (catalog.capabilities.useOnClick || !catalog.isInstalled(catalog.detailItem) || (catalog.updates[catalog.detailItem.id] || catalog.detailItem.updateCount || 0) > 0)
                    text: catalog.isInstalled(catalog.detailItem) ? ((catalog.kind === "plugins" || catalog.tab === "updates") ? Eitr.I18n.tr("Update") : Eitr.I18n.tr("Apply")) : Eitr.I18n.tr("Install")
                    onClicked: { if (catalog.tab === "updates" && catalog.capabilities.useOnClick) { const itemId = catalog.detailItem.id; catalog.closeDetail(); catalog.act("update", {id: itemId}); } else if (catalog.kind === "plugins") catalog.reviewDetail(); else if (catalog.isInstalled(catalog.detailItem)) { const themeId = catalog.detailItem.id; catalog.closeDetail(); catalog.act("apply", {id: themeId}); } else catalog.reviewDetail(); }
                }
        StoreActionButton { catalog: detailSheet.catalog; objectName: "detail-close"; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 10; width: 32; icon: true; text: "󰅖"; Accessible.name: Eitr.I18n.tr("Close"); onClicked: catalog.closeDetail() }
    }
}
