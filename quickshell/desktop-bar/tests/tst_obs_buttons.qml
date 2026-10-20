import QtQuick
import QtTest
import ".."

TestCase {
    name: "ObsButtons"
    when: windowShown
    width: 200
    height: 100
    visible: true
    QtObject {
        id: controller
        property color foreground: "white"
        property color background: "black"
        property string pendingAction: ""
        property bool controlsReady: pendingAction === ""
        property string lastAction: ""
        function run(action) { lastAction = action; pendingAction = action; }
    }
    PanelButton {
        id: recordButton
        foreground: controller.foreground
        text: "󰐌"
        icon: true
        available: controller.controlsReady
        loading: controller.pendingAction === "record"
        onClicked: controller.run("record")
    }
    PanelButton {
        id: stopButton
        x: 40
        foreground: controller.foreground
        text: "󰓛"
        icon: true
        available: controller.controlsReady
        loading: controller.pendingAction === "stop"
        onClicked: controller.run("stop")
    }
    function cleanup() { controller.pendingAction = ""; controller.lastAction = ""; }
    function test_clicked_button_loads_and_all_controls_disable() {
        mouseClick(recordButton);
        compare(controller.lastAction, "record");
        verify(recordButton.loading);
        verify(!recordButton.enabled);
        verify(!stopButton.enabled);
        verify(!stopButton.loading);
        controller.pendingAction = "";
        verify(!recordButton.loading);
        verify(recordButton.enabled);
    }
    function test_stop_loading() {
        mouseClick(stopButton);
        verify(stopButton.loading);
        verify(!recordButton.enabled);
    }
}
