import QtQuick
import QtTest
import ".."

TestCase {
    id: test
    name: "NotificationGroup"
    width: 440; height: 900
    visible: true
    when: windowShown
    property int clears: 0
    property int activatedId: 0
    Component {
        id: groupComponent
        NotificationGroup {
            width: 400
            foreground: "#ddccaa"; accent: "#88aa99"
            background: "#262626"
            onToggleRequested: expanded = !expanded
            onClearRequested: test.clears++
            onActivated: notificationId => test.activatedId = notificationId
        }
    }
    function notice(id) {
        return {id: id, appName: "Test", appIcon: "", summary: "Message " + id,
            body: "Body", image: "", urgency: 1, hasInlineReply: false,
            actions: [], dismiss: function() {}};
    }
    function test_activation_from_collapsed_and_expanded_cards() {
        activatedId = 0;
        var first = notice(3), second = notice(2);
        first.actions = [{identifier: "default", text: "Open", invoke: function() {}}];
        second.actions = first.actions;
        var group = createTemporaryObject(groupComponent, test, {notifications: [first, second]});
        mouseClick(findChild(group, "frontNotificationCard"), 3, 3);
        verify(group.expanded);
        compare(activatedId, 0);
        tryCompare(group, "revealProgress", 1);
        mouseClick(findChild(group, "frontNotificationCard"), 3, 3);
        compare(activatedId, 3);
        mouseClick(group, 3, group.height - 3);
        compare(activatedId, 2);
    }
    function test_collapsed_card_without_default_action_still_expands() {
        activatedId = 0;
        var group = createTemporaryObject(groupComponent, test, {notifications: [notice(3), notice(2)]});
        mouseClick(findChild(group, "frontNotificationCard"), 3, 3);
        verify(group.expanded);
        compare(activatedId, 0);
        tryCompare(group, "revealProgress", 1);
        mouseClick(findChild(group, "frontNotificationCard"), 3, 3);
        compare(activatedId, 0);
    }
    function test_expand_and_collapse() {
        var group = createTemporaryObject(groupComponent, test, {notifications: [notice(3), notice(2), notice(1)]});
        compare(group.displayedNotifications.length, 1);
        compare(group.displayedNotifications[0].id, 3);
        compare(group.stackDepth, 3);
        verify(findChild(group, "collapsedNotificationStack").visible);
        verify(findChild(group, "notificationStackLayer2"));
        var firstLayer = findChild(group, "notificationStackLayer1");
        var secondLayer = findChild(group, "notificationStackLayer2");
        compare(firstLayer.x, 8);
        compare(secondLayer.x, 16);
        compare(secondLayer.y, 14);
        compare(firstLayer.color.a, 1);
        verify(firstLayer.color !== secondLayer.color);
        verify(!findChild(group, "notificationStackLayer3"));
        var toggle = findChild(group, "toggleNotificationGroup");
        var frontCard = findChild(group, "frontNotificationCard");
        var frontHeight = frontCard.height;
        var frontWidth = frontCard.width;
        verify(toggle.visible);
        mouseClick(toggle);
        compare(group.displayedNotifications.length, 3);
        verify(group.expanded);
        tryCompare(group, "revealProgress", 1);
        compare(frontCard.height, frontHeight);
        compare(frontCard.width, frontWidth);
        compare(frontCard.compact, false);
        verify(!findChild(group, "collapsedNotificationStack").visible);
        group.notifications = [notice(4), notice(3), notice(2), notice(1)];
        compare(group.displayedNotifications.length, 4);
        compare(group.stackDepth, 3);
        wait(400);
        mouseClick(toggle);
        compare(group.displayedNotifications.length, 1);
        tryCompare(group, "revealProgress", 0);
        verify(findChild(group, "collapsedNotificationStack").visible);
        compare(group.displayedNotifications[0].id, 4);
        mouseClick(findChild(group, "clearNotificationGroup"));
        compare(clears, 1);
    }
    function test_single_notification() {
        var group = createTemporaryObject(groupComponent, test, {notifications: [notice(1)]});
        compare(group.displayedNotifications.length, 1);
        compare(group.stackDepth, 1);
        verify(!findChild(group, "notificationStackLayer1"));
        verify(!findChild(group, "toggleNotificationGroup").visible);
    }
    function test_expanded_front_matches_translucent_cards() {
        var group = createTemporaryObject(groupComponent, test, {
            notifications: [notice(3), notice(2)], background: "transparent"
        });
        var front = findChild(group, "frontNotificationCard");
        compare(front.color.a, 1);
        group.expanded = true;
        tryCompare(group, "revealProgress", 1);
        compare(front.color, Qt.alpha(group.foreground, 0.055));
        compare(front.opacity, 1);
        group.expanded = false;
        tryCompare(group, "revealProgress", 0);
        compare(front.color.a, 1);
    }
}
