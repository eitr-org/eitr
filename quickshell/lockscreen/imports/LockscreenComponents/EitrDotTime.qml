import QtQuick

Item {
    id: root
    property string text: "00"
    property color color: "white"
    property real dotSize: 7
    readonly property var digits: [
        "01110100011001110101110011000101110",
        "00100011000010000100001000010001110",
        "01110100010000100010001000100011111",
        "11110000010000101110000010000111110",
        "00010001100101010010111110001000010",
        "11111100001000011110000010000111110",
        "01110100001000011110100011000101110",
        "11111000010001000100010000100001000",
        "01110100011000101110100011000101110",
        "01110100011000101111000010000101110"
    ]
    implicitWidth: text.length * dotSize * 7.2
    implicitHeight: dotSize * 9
    Repeater {
        model: root.text.length
        Item {
            required property int index
            x: index * root.dotSize * 7.2; width: root.dotSize * 6.2; height: root.height
            readonly property string mask: root.digits[Number(root.text[index])] || ""
            Repeater {
                model: 35
                Rectangle {
                    required property int index
                    width: root.dotSize; height: width; radius: width / 2
                    x: index % 5 * root.dotSize * 1.35; y: Math.floor(index / 5) * root.dotSize * 1.35
                    color: root.color; visible: parent.mask[index] === "1"
                }
            }
        }
    }
}
