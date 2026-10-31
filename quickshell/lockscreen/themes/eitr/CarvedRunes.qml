import QtQuick

// The password field's echo: one Elder Futhark rune per typed character, in a fixed
// order of typing (never derived from the characters), so it reveals only the
// length, as dots do. Every new rune falls hard onto the field, lands white-hot with
// a flash and a burst of sparks, cools to gold and stays carved; the field jolts
// (struck). A deleted rune crumbles into falling pieces and dust. The caret moves
// with the arrows, Home and End; Backspace and Delete crumble the rune beside it.
Item {
    id: carved
    // The hidden password TextInput this echoes: its length and caret position.
    property Item input
    property color gold: "#c4914f"
    property color caret: "white"
    property real size: 20
    property bool animated: true
    signal struck()
    readonly property string futhark: "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
    readonly property real step: size * 0.95
    readonly property int count: input ? input.length : 0
    readonly property int cursor: input ? Math.min(input.cursorPosition, count) : 0
    // Long passwords scroll like a normal field, keeping the caret in view.
    readonly property int visibleCount: Math.max(1, Math.floor((width - size) / step))
    property int first: 0
    function follow() {
        first = Math.max(0, Math.min(first, count - visibleCount));
        if (cursor < first) first = cursor;
        if (cursor > first + visibleCount) first = cursor - visibleCount;
    }
    onCursorChanged: follow()
    onVisibleCountChanged: follow()

    // One entry per rune, holding its glyph from a running counter, so a carved rune
    // never changes and an insertion does not reshuffle the others. Entries are only
    // inserted or removed, never rebuilt, so only a new rune strikes.
    ListModel { id: runes }
    property int typed: 0
    Connections {
        target: carved.input
        // Text and caret update separately; read both once the edit has settled.
        function onTextChanged() { Qt.callLater(carved.sync); }
    }
    function deleteRune(backward) {
        sync();
        const position = input.cursorPosition;
        const start = backward ? position - 1 : position;
        if (start < 0 || start >= count) return;
        input.remove(start, start + 1);
        sync(true);
    }
    function sync(deleting = false) {
        const delta = count - runes.count;
        // Selection is off in the field, so an edit is a pure insert or delete at the caret.
        if (delta < 0) {
            const start = Math.min(cursor, runes.count + delta);
            for (let index = start - delta - 1; index >= start; index--) {
                if (deleting && animated && index >= first && index < first + visibleCount)
                    crumble.createObject(carved, {rune: runes.get(index).glyph,
                                                  x: (index - first) * step, delay: (index - start) * 25});
                runes.remove(index);
            }
        } else if (delta > 0) {
            const start = Math.max(0, Math.min(cursor - delta, runes.count));
            for (let offset = 0; offset < delta; offset++)
                runes.insert(start + offset, {glyph: futhark[typed++ % futhark.length]});
        }
        if (count === 0) typed = 0;
        follow();
    }

    Repeater {
        model: runes
        Item {
            id: slot
            required property int index
            required property string glyph
            visible: index >= carved.first && index < carved.first + carved.visibleCount
            x: (index - carved.first) * carved.step
            // Runes after an insertion or deletion slide to their new place.
            Behavior on x { enabled: carved.animated; NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
            width: carved.step; height: carved.height
            Text {
                id: rune
                anchors.centerIn: parent
                text: slot.glyph
                color: carved.gold
                font.family: "Noto Sans Runic"
                font.pixelSize: carved.size
                transformOrigin: Item.Center
            }
            Rectangle {
                id: flash
                anchors.centerIn: rune
                width: carved.size * 2.4; height: width; radius: width / 2
                color: "#ffd98a"; opacity: 0
            }
            Repeater {
                id: sparks
                model: carved.animated ? 8 : 0
                Rectangle {
                    required property int index
                    readonly property real angle: (index * 45 + 22 + slot.index * 17) * Math.PI / 180
                    property real travel: 0
                    x: rune.x + rune.width / 2 + Math.cos(angle) * travel * carved.size * 1.6 - width / 2
                    y: rune.y + rune.height / 2 + Math.sin(angle) * travel * carved.size * 0.9 - height / 2
                    width: Math.max(2, carved.size * 0.13); height: width; radius: width / 2
                    color: ["#ffd98a", "#ef8c3e", "#f3b063"][index % 3]
                    opacity: 0
                    NumberAnimation on travel { id: fly; running: false; from: 0.2; to: 1; duration: 380; easing.type: Easing.OutCubic }
                    NumberAnimation on opacity { id: fadeSpark; running: false; from: 1; to: 0; duration: 380; easing.type: Easing.InQuad }
                    function burst() { fly.restart(); fadeSpark.restart(); }
                }
            }
            // Each rune strikes once, when it is typed, however fast the typing.
            Component.onCompleted: if (carved.animated) strike.start()
            SequentialAnimation {
                id: strike
                ParallelAnimation {
                    NumberAnimation { target: rune; property: "anchors.verticalCenterOffset"; from: -carved.height * 2.2; to: 0; duration: 170; easing.type: Easing.InExpo }
                    NumberAnimation { target: rune; property: "opacity"; from: 0; to: 1; duration: 80 }
                    NumberAnimation { target: rune; property: "scale"; from: 2.6; to: 1; duration: 170; easing.type: Easing.InExpo }
                }
                ScriptAction { script: { carved.struck(); for (let spark = 0; spark < sparks.count; spark++) sparks.itemAt(spark).burst(); } }
                ParallelAnimation {
                    SequentialAnimation {
                        NumberAnimation { target: rune; property: "scale"; to: 1.3; duration: 50; easing.type: Easing.OutQuad }
                        NumberAnimation { target: rune; property: "scale"; to: 1; duration: 160; easing.type: Easing.OutBack }
                    }
                    NumberAnimation { target: flash; property: "opacity"; from: 0.85; to: 0; duration: 300; easing.type: Easing.OutQuad }
                    NumberAnimation { target: flash; property: "scale"; from: 0.3; to: 1.2; duration: 300; easing.type: Easing.OutQuad }
                    ColorAnimation { target: rune; property: "color"; from: "#fff4d6"; to: carved.gold; duration: 650; easing.type: Easing.InQuad }
                }
            }
        }
    }

    // A deleted rune: four pieces of it fall and tumble apart with a little dust.
    Component {
        id: crumble
        Item {
            id: rubble
            objectName: "eitrRuneRubble"
            property string rune
            property int delay: 0
            property real progress: 0
            width: carved.step; height: carved.height
            Repeater {
                model: 4
                Item {
                    id: piece
                    required property int index
                    readonly property real column: index % 2
                    readonly property real row: Math.floor(index / 2)
                    readonly property real drift: (column - 0.5) * (0.6 + 0.3 * row)
                    width: rubble.width / 2; height: rubble.height / 2
                    x: column * width + drift * rubble.progress * carved.size
                    y: row * height + rubble.progress * rubble.progress * carved.size * (1.4 + row * 0.5)
                    rotation: (column - 0.5) * 70 * rubble.progress * (1 + row)
                    opacity: 1 - rubble.progress
                    clip: true
                    Text {
                        x: -piece.column * piece.width + (rubble.width - width) / 2
                        y: -piece.row * piece.height + (rubble.height - height) / 2
                        text: rubble.rune
                        color: carved.gold
                        font.family: "Noto Sans Runic"
                        font.pixelSize: carved.size
                    }
                }
            }
            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    x: rubble.width * (0.25 + 0.1 * index) + (index % 2 ? 1 : -1) * rubble.progress * carved.size * 0.5
                    y: rubble.height * 0.6 + rubble.progress * carved.size * (0.6 + 0.15 * index)
                    width: Math.max(1.5, carved.size * 0.08); height: width; radius: width / 2
                    color: Qt.darker(carved.gold, 1.3)
                    opacity: (1 - rubble.progress) * 0.8
                }
            }
            SequentialAnimation {
                running: true
                PauseAnimation { duration: rubble.delay }
                NumberAnimation { target: rubble; property: "progress"; from: 0; to: 1; duration: 420; easing.type: Easing.InQuad }
                ScriptAction { script: rubble.destroy() }
            }
        }
    }

    Rectangle {
        // A solid block caret, like a terminal's.
        x: (carved.cursor - carved.first) * carved.step + (carved.step - width) / 2
        anchors.verticalCenter: parent.verticalCenter
        width: carved.size * 0.55; height: carved.size * 1.05
        color: carved.caret
        // Blinks on a timer: a looping animation would redraw the whole screen at the
        // monitor's refresh rate the entire time the screen is locked.
        Timer {
            running: carved.animated && carved.caret.a > 0
            interval: 530; repeat: true
            onTriggered: parent.opacity = parent.opacity > 0 ? 0 : 1
            onRunningChanged: parent.opacity = 1
        }
    }
}
