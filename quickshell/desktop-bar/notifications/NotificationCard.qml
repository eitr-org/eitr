import ".."
import Eitr as Eitr
import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import "../PanelStyle.js" as PanelStyle
import "../NotificationDetect.js" as NotificationDetect
import "../NotificationLogic.js" as NotificationLogic

Rectangle {
    id: card
    required property var notification
    // Identical notifications collapsed into this card.
    property int repeats: 1
    required property color foreground
    required property color accent
    property bool compact: false
    property bool filled: true
    property bool expandOnClick: false
    property real receivedAt: 0
    signal expansionRequested()
    signal dismissed()
    readonly property bool imageIsPreview: NotificationLogic.imageIsPreview(notification,
        imageLoader.implicitWidth, imageLoader.implicitHeight)
    readonly property bool useNotificationImage: notification && !imageIsPreview
    Image {
        id: imageLoader
        visible: false
        source: NotificationLogic.imageSource(card.notification)
        sourceSize: Qt.size(NotificationLogic.thumbnailWidth * Screen.devicePixelRatio, NotificationLogic.thumbnailHeight * Screen.devicePixelRatio)
        asynchronous: true
    }
    // The app behind the notification: its desktop entry gives an icon when the
    // notification names none, and its window is what a plain click opens.
    readonly property var desktopEntry: !notification ? null
        : (notification.desktopEntry ? DesktopEntries.byId(notification.desktopEntry) : null)
          || (notification.appName ? DesktopEntries.heuristicLookup(notification.appName) : null)
    readonly property var shown: NotificationLogic.presentation(notification)
    readonly property var detected: notification ? NotificationDetect.scan(shown.summary, shown.body) : ({code: "", link: ""})
    property bool codeCopied: false
    onNotificationChanged: { codeCopied = false; copiedTimer.stop(); }
    Timer { id: copiedTimer; interval: 1500; onTriggered: card.codeCopied = false }
    signal activated(int notificationId)
    // Without an action of its own, a click opens the app that sent the notification.
    function openApp() {
        activated(notification.id);
        Quickshell.execDetached(NotificationLogic.openCommand(notification, Eitr.Paths.code("quickshell/desktop-bar/scripts/notification-open.py")));
    }
    function invokeAction(action) {
        var id = notification.id;
        activated(id);
        action.invoke();
    }
    function copyCode() {
        if (!detected.code) return;
        Quickshell.execDetached(NotificationLogic.copyCommand(detected.code));
        codeCopied = true;
        copiedTimer.restart();
    }
    function openLink() {
        if (!detected.link) return;
        activated(notification.id);
        Quickshell.execDetached(NotificationLogic.openLinkCommand(detected.link, Eitr.Paths.code("quickshell/desktop-bar/scripts/notification-open.py")));
    }
    implicitHeight: content.implicitHeight + 28
    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
    color: filled ? Qt.alpha(foreground, 0.055) : "transparent"
    readonly property int urgency: notification && notification.urgency !== undefined ? notification.urgency : 1
    opacity: urgency === 0 ? 0.8 : 1
    NotificationPriorityBorder {
        anchors.fill: parent
        shown: card.filled
        urgency: card.urgency
        accent: card.accent
        cornerRadius: card.radius
    }

    // Behind the content so dismiss, action, and reply controls keep their own clicks.
    MouseArea {
        objectName: "activateNotification"
        anchors.fill: parent
        readonly property var defaultAction: card.notification
            ? card.notification.actions.find(action => action.identifier === "default") : null
        enabled: !!card.notification
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (card.expandOnClick) card.expansionRequested();
            else if (defaultAction) card.invokeAction(defaultAction);
            else card.openApp();
        }
    }

    Column {
        id: content
        x: 14; y: 14
        width: parent.width - 28
        spacing: 10
        Item {
            id: cardHeader
            width: parent.width
            height: Math.max(30, titleBox.implicitHeight)
            Item {
                id: applicationIcon
                objectName: "notificationAppIcon"
                anchors.verticalCenter: parent.verticalCenter
                width: 28; height: 28
                Image {
                    id: notificationImage
                    objectName: "notificationImage"
                    anchors.fill: parent
                    source: card.useNotificationImage ? imageLoader.source : ""
                    sourceSize: Qt.size(NotificationLogic.thumbnailWidth * Screen.devicePixelRatio, NotificationLogic.thumbnailHeight * Screen.devicePixelRatio)
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    visible: status === Image.Ready
                }
                Image {
                    id: fallbackIcon
                    objectName: "notificationFallbackIcon"
                    anchors.fill: parent
                    source: NotificationLogic.appIconSource(card.notification, card.desktopEntry ? card.desktopEntry.icon : "",
                        Eitr.Paths.code("walker/icons"), name => Quickshell.iconPath(name, true))
                    fillMode: Image.PreserveAspectFit
                    visible: notificationImage.status !== Image.Ready && status === Image.Ready
                }
                Text {
                    objectName: "notificationFallbackGlyph"
                    anchors.centerIn: parent
                    visible: notificationImage.status !== Image.Ready && fallbackIcon.status !== Image.Ready
                    text: "󰂚"; color: card.foreground
                    font.family: DesktopFonts.family; font.pixelSize: 22
                }
            }
            Column {
                id: titleBox
                x: 38
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 28 - 30 - 20
                spacing: 3
                Text {
                    objectName: "notificationTitle"
                    width: parent.width
                    text: card.shown.summary + (card.repeats > 1 ? "  ×" + card.repeats : "")
                    textFormat: Text.PlainText
                    color: card.foreground
                    font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    font.bold: true
                    wrapMode: Text.Wrap
                    maximumLineCount: card.compact ? 2 : 4
                    elide: Text.ElideRight
                }
                Text {
                    objectName: "notificationTime"
                    visible: card.receivedAt > 0 && isFinite(card.receivedAt)
                    width: parent.width
                    text: visible ? Qt.formatDateTime(new Date(card.receivedAt), "MMM d · HH:mm") : ""
                    color: card.foreground
                    opacity: 0.65
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    elide: Text.ElideRight
                }
            }
            PanelButton {
                objectName: "dismissNotification"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: 30; height: 30
                text: "󰅖"; icon: true; compactIconBackground: true
                foreground: card.foreground
                onClicked: if (card.notification) {
                    let notice = card.notification;
                    card.dismissed();
                    notice.dismiss();
                }
            }
        }
        Text {
            visible: text !== ""
            width: parent.width
            text: card.shown.body
            textFormat: Text.PlainText
            color: card.foreground; opacity: 0.85
            font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
            wrapMode: Text.Wrap
            maximumLineCount: card.compact ? 3 : 12
            elide: Text.ElideRight
        }
        Image {
            objectName: "notificationPreview"
            source: card.imageIsPreview ? imageLoader.source : ""
            sourceSize: Qt.size(NotificationLogic.thumbnailWidth * Screen.devicePixelRatio, NotificationLogic.thumbnailHeight * Screen.devicePixelRatio)
            visible: status === Image.Ready && card.imageIsPreview
            readonly property real displayScale: Math.min(1,
                content.width / Math.max(1, implicitWidth),
                (card.compact ? 128 : 160) / Math.max(1, implicitWidth),
                (card.compact ? 96 : 120) / Math.max(1, implicitHeight))
            width: visible ? implicitWidth * displayScale : 0
            height: visible ? implicitHeight * displayScale : 0
            fillMode: Image.PreserveAspectFit
            asynchronous: true
        }
        // Actions sit in an even grid: one fills the row, the rest pair up in two
        // equal columns, and an odd last action spans the row.
        Flow {
            id: actionGrid
            readonly property var nativeActions: card.notification ? card.notification.actions.filter(action => action.identifier !== "default" && action.identifier !== "inline-reply") : []
            readonly property var actions: {
                var items = nativeActions.map(action => ({kind: "action", identifier: action.identifier, text: action.text, action: action}));
                if (card.detected.code) items.push({kind: "copy-code", identifier: "copy-code"});
                if (card.detected.link) items.push({kind: "open-link", identifier: "open-link"});
                return items;
            }
            width: parent.width
            spacing: 6
            Repeater {
                model: actionGrid.actions
                PanelButton {
                    required property var modelData
                    required property int index
                    readonly property bool fullRow: actionGrid.actions.length === 1 || (index === actionGrid.actions.length - 1 && index % 2 === 0)
                    objectName: "notificationAction_" + modelData.identifier
                    text: modelData.kind === "copy-code" ? (card.codeCopied ? Eitr.I18n.tr("Copied") : Eitr.I18n.tr("Copy code"))
                        : modelData.kind === "open-link" ? Eitr.I18n.tr("Open link")
                        : modelData.text
                    leadingIcon: modelData.kind === "copy-code" ? (card.codeCopied ? "\u{F012C}" : "\u{F018F}")
                        : modelData.kind === "open-link" ? "\u{F0339}"
                        : ""
                    width: fullRow ? actionGrid.width : (actionGrid.width - actionGrid.spacing) / 2
                    height: 32
                    foreground: card.foreground
                    onClicked: {
                        if (modelData.kind === "copy-code") card.copyCode();
                        else if (modelData.kind === "open-link") card.openLink();
                        else card.invokeAction(modelData.action);
                    }
                }
            }
        }
        Row {
            visible: card.notification && card.notification.hasInlineReply
            width: parent.width; spacing: 8
            TextField {
                id: reply
                objectName: "notificationReply"
                width: parent.width - 76; height: 34
                placeholderText: card.notification ? card.notification.inlineReplyPlaceholder || Eitr.I18n.tr("Reply…") : ""
                color: card.foreground
                font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                background: Rectangle { color: Qt.alpha(card.foreground, 0.08); radius: DesktopStyle.radius(PanelStyle.controlRadius) }
                onAccepted: if (text.trim()) { card.notification.sendInlineReply(text); text = ""; }
            }
            PanelButton {
                text: Eitr.I18n.tr("Send"); height: 34; foreground: card.foreground
                available: reply.text.trim().length > 0
                onClicked: { card.notification.sendInlineReply(reply.text); reply.text = ""; }
            }
        }
    }
}
