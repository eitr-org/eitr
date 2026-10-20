import QtQuick
import QtTest
import ".."

TestCase {
    id: test
    name: "OverviewTileReveal"
    when: windowShown
    width: 400; height: 300
    property real elapsed: 0
    OverviewTileReveal { id: first; order: 0; elapsed: test.elapsed; width: 100; height: 100 }
    OverviewTileReveal { id: last; order: 9; elapsed: test.elapsed; width: 100; height: 100 }
    NumberAnimation { id: clock; target: test; property: "elapsed"; from: 0; to: 755; duration: 755 }
    function cleanup() { clock.stop(); first.opened = false; last.opened = false; elapsed = 0; }
    function test_stagger_and_finish_under_one_second() {
        first.opened = true; last.opened = true;
        clock.start();
        wait(100);
        verify(first.progress > 0);
        compare(last.progress, 0);
        tryCompare(first, "progress", 1, 500);
        tryCompare(last, "progress", 1, 650);
        compare(first.opacity, 1);
        compare(last.scale, 1);
    }
    function test_close_is_immediate() {
        elapsed = 755;
        first.opened = true; last.opened = true;
        compare(first.opacity, 1);
        compare(last.opacity, 1);
        first.opened = false; last.opened = false;
        compare(first.opacity, 0);
        compare(last.opacity, 0);
    }
    function test_reopen_restarts() {
        elapsed = 755; last.opened = true;
        compare(last.progress, 1);
        last.opened = false;
        elapsed = 0; last.opened = true;
        compare(last.progress, 0);
    }
    function test_recreated_tile_does_not_replay_entrance() {
        elapsed = 755;
        const component = Qt.createComponent("../OverviewTileReveal.qml");
        compare(component.status, Component.Ready);
        const tile = component.createObject(test, {opened: true, order: 9, elapsed: test.elapsed});
        compare(tile.progress, 1);
        tile.destroy();
    }
}
