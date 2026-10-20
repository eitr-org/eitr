import QtQuick
import QtTest
import ".."

TestCase {
    name: "PanelBodyPadding"
    width: 1000; height: 1000
    Item {
        id: host
        width: 468; height: 740
        property string barEdge: "top"
        property real revealProgress: 1
        property color background: "#262626"
        PanelSurface { id: surface; anchors.fill: parent; hostWindow: host }
    }
    function test_equal_padding_data() {
        var rows = [];
        for (var edge of ["top", "bottom", "left", "right"])
            for (var alignment of ["start", "center", "end"])
                rows.push({tag: edge + "-" + alignment, edge: edge, alignment: alignment});
        return rows;
    }
    function test_equal_padding(data) {
        host.barEdge = data.edge;
        var vertical = data.edge === "left" || data.edge === "right";
        host.x = vertical ? 30 : data.alignment === "start" ? 0 : data.alignment === "end" ? 532 : 266;
        host.y = vertical ? (data.alignment === "start" ? 0 : data.alignment === "end" ? 260 : 130) : 30;
        var frame = findChild(surface, "panelContentFrame");
        var leading = data.alignment === "start" ? 0 : 14;
        var trailing = data.alignment === "end" ? 0 : 14;
        var position = vertical ? frame.y : frame.x;
        var size = vertical ? frame.height : frame.width;
        var total = vertical ? host.height : host.width;
        var expected = 14 - (leading + trailing) / 2;
        compare(position - leading, expected);
        compare(total - trailing - position - size, expected);
    }
}
