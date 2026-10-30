import Eitr as Eitr
import QtQuick
import QtQuick.Controls.Basic
import "PanelStyle.js" as PanelStyle
import "NotificationLogic.js" as NotificationLogic

Rectangle {
    id: card
    required property var notification
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
    signal activated(int notificationId)
    function invokeAction(action) {
        var id = notification.id;
        activated(id);
        action.invoke();
    }
    implicitHeight: content.implicitHeight + 28
    radius: DesktopStyle.radius(PanelStyle.cornerRadius)
    color: filled ? Qt.alpha(foreground, 0.055) : "transparent"
    readonly property int urgency: notification && notification.urgency !== undefined ? notification.urgency : 1
    opacity: urgency === 0 ? 0.8 : 1
    NotificationPriorityGlow {
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
        enabled: card.expandOnClick || !!defaultAction
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (card.expandOnClick) card.expansionRequested();
            else card.invokeAction(defaultAction);
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
                    source: card.notification && card.notification.appIcon ? (card.notification.appIcon.indexOf("/") !== -1 || card.notification.appIcon.indexOf(":") !== -1 ? card.notification.appIcon : "image://icon/" + card.notification.appIcon) : ""
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
                    text: card.notification ? card.notification.summary : ""
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
            text: card.notification ? card.notification.body : ""
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
            readonly property var actions: card.notification ? card.notification.actions.filter(action => action.identifier !== "default" && action.identifier !== "inline-reply") : []
            width: parent.width
            spacing: 6
            Repeater {
                model: actionGrid.actions
                PanelButton {
                    required property var modelData
                    required property int index
                    readonly property bool fullRow: actionGrid.actions.length === 1 || (index === actionGrid.actions.length - 1 && index % 2 === 0)
                    objectName: "notificationAction_" + modelData.identifier
                    text: modelData.text
                    width: fullRow ? actionGrid.width : (actionGrid.width - actionGrid.spacing) / 2
                    height: 32
                    foreground: card.foreground
                    onClicked: card.invokeAction(modelData)
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
