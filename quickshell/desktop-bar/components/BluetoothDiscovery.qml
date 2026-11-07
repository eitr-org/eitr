import ".."
import QtQuick

// One Bluetooth discovery run: toggle() starts scanning on the adapter and stops it
// when pressed again, after `timeout`, or when its owner calls stop().
Item {
    id: discovery
    property var adapter: null
    property var scanningAdapter: null
    property int timeout: 20000
    readonly property bool scanning: scanningAdapter !== null
    visible: false
    function toggle() {
        if (scanningAdapter) stop();
        else if (adapter) { scanningAdapter = adapter; adapter.discovering = true; timer.restart(); }
    }
    function stop() {
        timer.stop();
        if (!scanningAdapter) return;
        scanningAdapter.discovering = false;
        scanningAdapter = null;
    }
    Timer {
        id: timer
        interval: discovery.timeout
        onTriggered: discovery.stop()
    }
}
