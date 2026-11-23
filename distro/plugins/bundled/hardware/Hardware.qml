// SPDX-License-Identifier: MIT
// Copyright (c) 2026 The Eitr project
pragma ComponentBehavior: Bound
import QtQuick
import "HardwareState.js" as HardwareState

Item {
    id: root
    required property var api
    implicitWidth: 480
    implicitHeight: displayMode === "compact" ? 96 : 280

    property bool persistData: true
    property string displayMode: "detailed"
    property bool loaded: false
    property bool applyingSaved: false

    readonly property var hardwareSnapshot: api.hardware
    readonly property var summary: HardwareState.summarize(hardwareSnapshot)
    readonly property bool lightTheme: api.foreground.hslLightness < 0.5
    readonly property color fallbackSurface: api.palette && api.palette.surface
        ? api.palette.surface
        : Qt.rgba(api.background.r, api.background.g, api.background.b, Math.max(0.92, api.background.a))
    readonly property bool ownSurface: api.surface === "none"
    readonly property color primaryColor: api.foreground
    readonly property color secondaryColor: Qt.alpha(api.foreground, 0.72)
    readonly property color mutedColor: Qt.alpha(api.foreground, 0.54)
    readonly property color tileFillColor: Qt.alpha(api.foreground, lightTheme ? 0.045 : 0.06)
    readonly property color tileBorderColor: Qt.alpha(api.foreground, lightTheme ? 0.12 : 0.14)
    readonly property color trackColor: Qt.alpha(api.foreground, lightTheme ? 0.14 : 0.18)
    readonly property color warnColor: lightTheme ? "#b45309" : "#f59e0b"
    readonly property color critColor: lightTheme ? "#dc2626" : "#f87171"
    readonly property real cardRadius: Math.max(4, Math.min(api.radius, 10))
    readonly property var themePalette: ({
        light: lightTheme,
        fontFamily: api.fontFamily,
        bodySize: api.bodySize,
        captionSize: api.captionSize,
        cardRadius: cardRadius,
        primary: primaryColor,
        secondary: secondaryColor,
        muted: mutedColor,
        accent: api.accent,
        tileFill: tileFillColor,
        tileBorder: tileBorderColor,
        track: trackColor,
        warn: warnColor,
        crit: critColor
    })

    function updateMenu() {
        if (typeof api.setMenu !== "function") return;
        api.setMenu(HardwareState.MODES.map(choice => ({
            id: choice.id,
            text: choice.label,
            checked: root.displayMode === choice.id,
            group: "Layout"
        })));
    }

    function applySaved(data) {
        applyingSaved = true;
        if (data && typeof data === "object" && "mode" in data)
            displayMode = HardwareState.normalizeMode(data.mode);
        applyingSaved = false;
        loaded = true;
        updateMenu();
    }

    function saveMode() {
        if (!loaded || !persistData) return;
        if (typeof api.saveInstanceData === "function")
            api.saveInstanceData({version: 1, mode: displayMode});
    }

    onDisplayModeChanged: {
        updateMenu();
        if (loaded && !applyingSaved) saveMode();
    }

    Component.onCompleted: {
        updateMenu();
        if (!persistData || api.instanceDataReady || !("instanceDataReady" in api))
            applySaved(api.instanceData);
    }

    Connections {
        target: root.api
        ignoreUnknownSignals: true
        function onInstanceDataLoaded() {
            root.applySaved(root.api.instanceData);
        }
        function onMenuTriggered(id) {
            if (id === "compact" || id === "detailed")
                root.displayMode = id;
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: root.api.radius
        color: root.ownSurface ? root.fallbackSurface : "transparent"
        border.width: root.ownSurface ? 1 : 0
        border.color: root.ownSurface ? root.tileBorderColor : "transparent"
        clip: true

        Item {
            anchors.fill: parent
            anchors.margins: 12
            visible: root.summary.state !== "ready"

            Text {
                anchors.centerIn: parent
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.summary.message
                textFormat: Text.PlainText
                color: root.summary.state === "error" ? root.critColor : root.secondaryColor
                font.family: root.api.fontFamily
                font.pixelSize: root.api.bodySize
            }
        }

        HardwareCompactView {
            anchors.fill: parent
            anchors.margins: 8
            visible: root.summary.state === "ready" && root.displayMode === "compact"
            summary: root.summary
            theme: root.themePalette
        }

        HardwareDetailedView {
            anchors.fill: parent
            anchors.margins: 12
            visible: root.summary.state === "ready" && root.displayMode === "detailed"
            summary: root.summary
            theme: root.themePalette
        }
    }
}
