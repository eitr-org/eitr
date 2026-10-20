import QtQuick
import QtTest
import ".."

TestCase {
    id: test
    name: "NotificationCard"
    when: windowShown
    width: 440; height: 420
    visible: true
    property int actionCalls: 0
    property int dismissCalls: 0
    property string replyText: ""
    property int activatedId: 0
    property int lockCalls: 0
    function test_arrival_time_and_missing_timestamp() {
        var card = createTemporaryObject(cardComponent, test, {notification: notice()});
        var label = findChild(card, "notificationTime");
        verify(!label.visible);
        card.receivedAt = new Date(2026, 9, 14, 9, 7).getTime();
        verify(label.visible);
        compare(label.text, Qt.formatDateTime(new Date(card.receivedAt), "MMM d · HH:mm"));
        verify(label.text.indexOf("09:07") !== -1);
        card.receivedAt = 0;
        verify(!label.visible);
        compare(label.text, "");
    }
    Component {
        id: idleControlsComponent
        IdleLockControls {
            width: 400
            idleEnabled: true
            busy: false
            foreground: "white"
            accent: "cyan"
            onLockRequested: test.lockCalls++
        }
    }
    Component {
        id: cardComponent
        NotificationCard {
            width: 400
            foreground: "white"
            accent: "cyan"
            onActivated: function(notificationId) { test.activatedId = notificationId; }
        }
    }
    function notice() {
        return {id: 17, appName: "Test", appIcon: "", summary: "Message",
            body: "A notification body", image: "", urgency: 1,
            hasInlineReply: true, inlineReplyPlaceholder: "Reply",
            actions: [{identifier: "open", text: "Open", invoke: function() { test.actionCalls++; }}],
            dismiss: function() { test.dismissCalls++; },
            sendInlineReply: function(text) { test.replyText = text; }};
    }
    function cleanup() {
        actionCalls = 0; dismissCalls = 0; replyText = ""; activatedId = 0; lockCalls = 0;
    }
    function test_popup_dismiss_does_not_activate_underlying_lock() {
        var controls = createTemporaryObject(idleControlsComponent, test);
        var card = createTemporaryObject(cardComponent, test, {notification: notice(), compact: true, z: 1});
        wait(20);
        var closeButton = findChild(card, "dismissNotification");
        var closePosition = closeButton.mapToItem(test, 0, 0);
        var lockPosition = controls.lockTarget.mapToItem(controls, 0, 0);
        controls.x = closePosition.x - lockPosition.x;
        controls.y = closePosition.y - lockPosition.y;
        mouseClick(closeButton);
        compare(dismissCalls, 1);
        compare(lockCalls, 0);
    }
    function test_action_and_dismiss() {
        var card = createTemporaryObject(cardComponent, test, {notification: notice()});
        verify(card);
        wait(20);
        mouseClick(findChild(card, "notificationAction_open"));
        compare(actionCalls, 1);
        compare(activatedId, 17);
        mouseClick(findChild(card, "dismissNotification"));
        compare(dismissCalls, 1);
    }
    function test_inline_reply() {
        var card = createTemporaryObject(cardComponent, test, {notification: notice()});
        var reply = findChild(card, "notificationReply");
        reply.forceActiveFocus();
        reply.text = "hello";
        keyClick(Qt.Key_Return);
        compare(replyText, "hello");
        compare(reply.text, "");
    }
    function test_card_default_action_data() {
        return [{tag: "center", compact: false}, {tag: "popup", compact: true}];
    }
    function test_card_default_action(data) {
        var notification = notice();
        notification.actions.push({identifier: "default", text: "Open message",
            invoke: function() { test.actionCalls++; }});
        var card = createTemporaryObject(cardComponent, test,
            {notification: notification, compact: data.compact});
        wait(20);
        // Padding, icon, title, and body all activate the same default action.
        mouseClick(card, 3, 3);
        mouseClick(findChild(card, "notificationAppIcon"));
        mouseClick(findChild(card, "notificationTitle"));
        mouseClick(card, 30, 55);
        compare(actionCalls, 4);
        compare(activatedId, 17);
        mouseClick(findChild(card, "dismissNotification"));
        compare(dismissCalls, 1);
        compare(actionCalls, 4);
        mouseClick(findChild(card, "notificationAction_open"));
        compare(actionCalls, 5);
        mouseClick(findChild(card, "notificationReply"));
        compare(actionCalls, 5);
    }
    function test_no_default_action_does_not_guess() {
        var card = createTemporaryObject(cardComponent, test, {notification: notice()});
        mouseClick(card, 3, 3);
        compare(actionCalls, 0);
        compare(activatedId, 0);
    }
    function test_title_and_icon_centers_data() {
        return [{tag: "single line", title: "Message"},
                {tag: "wrapped title", title: "A long notification title that should wrap onto multiple lines beside the app icon"}];
    }
    function test_title_and_icon_centers(data) {
        var notification = notice();
        notification.summary = data.title;
        var card = createTemporaryObject(cardComponent, test, {notification: notification});
        wait(20);
        var icon = findChild(card, "notificationAppIcon");
        var title = findChild(card, "notificationTitle");
        var iconCenter = icon.mapToItem(card, 0, icon.height / 2);
        var titleCenter = title.mapToItem(card, 0, title.height / 2);
        verify(Math.abs(iconCenter.y - titleCenter.y) <= 0.5);
    }
    function test_image_sizes_data() {
        return [
            {tag: "small image as icon", sourceWidth: 64, sourceHeight: 48, compact: false},
            {tag: "4K image as icon", sourceWidth: 3840, sourceHeight: 2160, compact: false},
            {tag: "popup image as icon", sourceWidth: 3840, sourceHeight: 2160, compact: true},
            {tag: "portrait as icon", sourceWidth: 600, sourceHeight: 1200, compact: false},
        ];
    }
    function test_image_sizes(data) {
        var notification = notice();
        notification.image = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="' + data.sourceWidth + '" height="' + data.sourceHeight + '"><rect width="100%" height="100%" fill="cyan"/></svg>');
        notification.appName = "Google Chrome";
        var card = createTemporaryObject(cardComponent, test, {notification: notification, compact: data.compact});
        var image = findChild(card, "notificationImage");
        tryCompare(image, "status", Image.Ready);
        compare(image.width, 28);
        compare(image.height, 28);
        compare(image.fillMode, Image.PreserveAspectFit);
        verify(image.visible);
        verify(!findChild(card, "notificationFallbackIcon").visible);
        verify(!findChild(card, "notificationFallbackGlyph").visible);
        var plainCard = createTemporaryObject(cardComponent, test,
            {notification: notice(), compact: data.compact});
        compare(card.implicitHeight, plainCard.implicitHeight);
    }
    function test_image_fallback_data() {
        return [{tag: "absent image", image: "", appIcon: true},
                {tag: "broken image", image: "file:///nonexistent-eitr-notification-image.png", appIcon: true},
                {tag: "no icons", image: "", appIcon: false}];
    }
    function test_body_preview_caps_data() {
        return [{tag: "center screenshot", appName: "Satty", compact: false, width: 160, height: 90},
                {tag: "popup screenshot", appName: "Satty", compact: true, width: 128, height: 72},
                {tag: "other app attachment", appName: "Photo editor", compact: false, width: 160, height: 90}];
    }
    function test_body_preview_caps(data) {
        var notification = notice();
        notification.appName = data.appName;
        notification.image = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160"><rect width="100%" height="100%" fill="cyan"/></svg>');
        var card = createTemporaryObject(cardComponent, test, {notification: notification, compact: data.compact});
        var preview = findChild(card, "notificationPreview");
        tryCompare(preview, "status", Image.Ready);
        compare(preview.width, data.width);
        compare(preview.height, data.height);
        verify(!findChild(card, "notificationImage").visible);
    }
    function test_screenshot_preview_is_not_an_avatar_data() {
        return [{tag: "Satty app name", appName: "Satty", desktopEntry: ""},
                {tag: "Satty desktop entry", appName: "Screenshot", desktopEntry: "satty.desktop"}];
    }
    function test_screenshot_preview_is_not_an_avatar(data) {
        var notification = notice();
        notification.appName = data.appName;
        notification.desktopEntry = data.desktopEntry;
        notification.image = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28"><rect width="28" height="28" fill="magenta"/></svg>');
        var card = createTemporaryObject(cardComponent, test, {notification: notification});
        compare(findChild(card, "notificationImage").source.toString(), "");
        verify(findChild(card, "notificationFallbackGlyph").visible);
        var preview = findChild(card, "notificationPreview");
        tryCompare(preview, "status", Image.Ready);
        verify(preview.visible);
        compare(preview.width, 28);
    }
    function test_image_fallback(data) {
        var notification = notice();
        notification.image = data.image;
        notification.appIcon = data.appIcon ? "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28"><rect width="28" height="28" fill="cyan"/></svg>') : "";
        var card = createTemporaryObject(cardComponent, test, {notification: notification});
        var image = findChild(card, "notificationImage");
        tryCompare(image, "status", data.image ? Image.Error : Image.Null);
        verify(!image.visible);
        var fallback = findChild(card, "notificationFallbackIcon");
        if (data.appIcon) tryCompare(fallback, "status", Image.Ready);
        compare(fallback.visible, data.appIcon);
        compare(findChild(card, "notificationFallbackGlyph").visible, !data.appIcon);
    }
}
