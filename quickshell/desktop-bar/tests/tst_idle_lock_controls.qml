import QtQuick
import QtTest
import ".."

TestCase {
    id: test
    name: "IdleLockControls"
    when: windowShown
    visible: true
    width: 400; height: 300
    property int toggles: 0
    property int locks: 0
    Component {
        id: controlsComponent
        IdleLockControls {
            width: 304
            idleEnabled: false
            busy: false
            foreground: "white"; accent: "cyan"
            onToggleRequested: test.toggles++
            onLockRequested: test.locks++
        }
    }
    Component {
        id: paddedPanelComponent
        Item {
            width: 340
            height: paddedControls.implicitHeight + 36 + 28
            property string barEdge: "top"
            property real revealProgress: 1
            property color background: "#202020"
            PanelSurface {
                anchors.fill: parent
                hostWindow: parent
                IdleLockControls {
                    id: paddedControls
                    objectName: "paddedIdleControls"
                    x: 18; y: 18
                    width: parent.width - 36
                    idleEnabled: true; busy: false
                    foreground: "white"; accent: "cyan"
                }
            }
        }
    }
    function cleanup() { toggles = 0; locks = 0; }
    function test_toggle_and_manual_lock_are_independent() {
        var controls = createTemporaryObject(controlsComponent, test);
        var toggle = findChild(controls, "idleLockSwitch");
        compare(toggle.checked, false);
        mouseClick(toggle);
        compare(toggles, 1);
        compare(locks, 0);
        mouseClick(findChild(controls, "lockNowButton"));
        compare(locks, 1);
        compare(toggles, 1);
    }
    function test_backend_state_updates_do_not_toggle_idle() {
        var controls = createTemporaryObject(controlsComponent, test);
        var toggle = findChild(controls, "idleLockSwitch");
        controls.idleEnabled = true;
        compare(toggle.checked, true);
        controls.idleEnabled = false;
        compare(toggle.checked, false);
        compare(toggles, 0);
    }
    function test_busy_prevents_duplicate_requests() {
        var controls = createTemporaryObject(controlsComponent, test, {busy: true});
        mouseClick(findChild(controls, "idleLockSwitch"));
        mouseClick(findChild(controls, "lockNowButton"));
        compare(toggles, 0);
        compare(locks, 0);
    }
    function test_compact_header_lock_button() {
        var controls = createTemporaryObject(controlsComponent, test);
        var button = findChild(controls, "lockNowButton");
        verify(button.icon);
        compare(button.width, 34);
        compare(button.height, 34);
        var position = button.mapToItem(controls, 0, 0);
        compare(position.x + button.width, controls.width);
        compare(position.y, 0);
        compare(controls.implicitHeight, 88);
    }
    function test_toggle_fits_surface_content_data() {
        return ["top", "bottom", "left", "right"].map(edge => ({tag: edge, edge: edge}));
    }
    function test_toggle_fits_surface_content(data) {
        var panel = createTemporaryObject(paddedPanelComponent, test, {barEdge: data.edge});
        var controls = findChild(panel, "paddedIdleControls");
        var toggle = findChild(controls, "idleLockSwitch");
        var frame = findChild(panel, "panelContentFrame");
        var bottom = toggle.mapToItem(frame, 0, toggle.height).y;
        verify(frame.height - bottom >= 18, "Toggle must retain full bottom padding");
    }
}
