// qmllint disable Quick.property-changes-parsed
import ".."
import QtQuick

Item {
    id: dynamic
    required property var host
    required property var barHost
    anchors.fill: parent
    z: 1
    visible: barHost.dynamicLayout && !FocusMode.enabled
    // Takes the bar's pieces one beat after becoming visible, so a layout switching away
    // (Dynamic and Drop move the same clock) has always given them back first.
    property bool holding: false
    onVisibleChanged: if (!visible) holding = false; else Qt.callLater(() => { dynamic.holding = dynamic.visible; })
    Component.onCompleted: holding = visible
    readonly property var surfaces: [leading, media, middle, trailing]
    readonly property alias leadingIsland: leading
    readonly property alias mediaIsland: media
    readonly property alias middleIsland: middle
    readonly property alias trailingIsland: trailing
    readonly property bool vertical: host.verticalBar
    readonly property real length: vertical ? height : width
    readonly property real spacing: barHost.islandGap * 2
    readonly property real insetStart: host.screenGaps[vertical ? 0 : 3]
    readonly property real insetEnd: host.screenGaps[vertical ? 2 : 1]
    readonly property real clockExtent: vertical ? barHost.verticalCalendarIcon.height : barHost.centerInfo.width
    readonly property real weatherExtent: vertical ? barHost.verticalWeatherIcon.height : barHost.barWeather.width
    // The clock island holds [capture] clock [weather]. At rest: the time plus what is
    // happening beside it (recording, timer, next event, bell); hover adds date and weather.
    // It stays centred as a whole, so the clock shifts by half the difference of its sides.
    readonly property bool captureShown: vertical ? barHost.verticalCapture.shown : barHost.barCapture.shown
    readonly property real captureLength: captureShown ? (vertical ? barHost.verticalCapture.height + 3 : barHost.barCapture.width + 6) : 0
    // While a player is there, its controls and equalizer are an island of their own
    // between the logo and the clock.
    readonly property bool mediaAvailable: barHost.mediaStrip.present
    readonly property real mediaExtent: (vertical ? barHost.verticalMedia.implicitHeight : barHost.mediaStrip.width) + 16
    // The room the media island takes before the clock island, gap included.
    readonly property real mediaRun: mediaAvailable ? media.targetExtent + spacing : 0
    readonly property real weatherLength: host.workspaceItemSpacing + weatherExtent
    readonly property real middleExtent: clockExtent + 8 + captureLength + weatherLength
    // Space the clock island takes when the side islands expand: a card's full size, or its widest hover.
    readonly property real middleRoom: middle.morphed ? middle.targetExtent : middleExtent
    readonly property real middleLeading: captureLength
    readonly property real middleTrailing: middle.expanded ? weatherLength : 0
    property real clockShift: (middleLeading - middleTrailing) / 2
    Behavior on clockShift { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    property real weatherReveal: middleTrailing
    Behavior on weatherReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    readonly property real leadingExtent: (vertical ? barHost.verticalStart.height : barHost.leftGroup.implicitWidth) + 8
    readonly property real trailingExtent: (vertical ? barHost.verticalEnd.height : barHost.rightSide.width + host.workspaceItemSpacing + barHost.notificationIcon.width) + 8
    HoverHandler {
        id: pointer
        onHoveredChanged: Qt.callLater(dynamic.updateHover)
    }
    readonly property point pointerPosition: pointer.point.position
    onPointerPositionChanged: Qt.callLater(updateHover)
    function updateHover() { trackPointer(pointer.hovered, pointerPosition); }
    function trackPointer(inside, position) {
        surfaces.forEach(island => {
            island.hovered = inside && position.x >= island.x && position.x < island.x + island.width
                && position.y >= island.y && position.y < island.y + island.height;
        });
    }
    function owns(panel, names) { return names.indexOf(panel) !== -1; }
    function active(names) { return names.some(panel => panel.visible || panel === barHost.pendingPanel); }
    readonly property var leftPanels: [barHost.aiMenu, barHost.hardwareMenu, barHost.workspaceMenu]
    readonly property var middlePanels: [barHost.calendarMenu, barHost.weatherMenu, barHost.recordingMenu].filter(panel => !!panel)
    // Control Center can be opened from the logo or externally; retain its source island.
    property string controlCenterOwner: "left"
    function rememberOwner(panel) {
        // Keep the source island when Control Center is reached from a card's arrows.
        if (panel === barHost.controlCenter && (trailing.hovered || leading.hovered)) controlCenterOwner = trailing.hovered ? "right" : "left";
    }
    Connections {
        target: barHost
        function onPendingPanelChanged() { dynamic.rememberOwner(barHost.pendingPanel); }
    }
    readonly property bool controlCenterOpen: barHost.controlCenter.visible || barHost.pendingPanel === barHost.controlCenter
    // Each panel belongs to one island, which grows into it while it is open.
    function islandFor(panel) {
        if (owns(panel, leftPanels) || (panel === barHost.controlCenter && controlCenterOwner === "left")) return leading;
        if (panel === barHost.mediaMenu) return mediaAvailable ? media : middle;
        if (owns(panel, middlePanels)) return middle;
        return owns(panel, barHost.dockPanels) ? trailing : null;
    }
    // While switching panels the next one is pending: the island goes straight to its size.
    function openPanel(island) {
        const showing = barHost.dockPanels.find(panel => (panel.opened || panel === barHost.pendingPanel) && islandFor(panel) === island);
        return showing || null;
    }
    function inside(item, ancestor) {
        for (let current = item; current; current = current.parent) if (current === ancestor) return true;
        return false;
    }
    // The island's panels in the order of their bar icons, counting only icons it shows.
    function panelsOf(island) {
        const axis = vertical ? "y" : "x";
        const iconOf = panel => panel.morphAnchor || panel.attachmentTarget;
        return barHost.dockPanels.filter(panel => {
            const icon = iconOf(panel);
            return icon && icon.visible && icon.width > 0 && icon.height > 0 && inside(icon, island);
        }).map(panel => ({panel: panel, at: iconOf(panel).mapToItem(island, 0, 0)[axis]}))
          .sort((first, second) => first.at - second.at).map(entry => entry.panel);
    }
    function step(panel, delta) {
        const island = islandFor(panel);
        if (island === trailing || island === leading) controlCenterOwner = island === trailing ? "right" : "left";
        const panels = island ? panelsOf(island) : [];
        const index = panels.indexOf(panel);
        if (panels.length < 2 || index < 0) return;
        barHost.showPanel(panels[(index + delta + panels.length) % panels.length]);
    }
    // Where an island settles along the bar: the clock island centred, the others one
    // gap away from it, kept on screen.
    // The clock island is centred unless a side card needs the room: then it moves along,
    // and the island after it follows, keeping the gaps.
    function middleStartFor(leadingExtent, middleExtent, trailingExtent) {
        const centred = (length - middleExtent) / 2;
        const lowest = insetStart + leadingExtent + spacing + mediaRun;
        const highest = length - insetEnd - trailingExtent - spacing - middleExtent;
        return Math.max(lowest, Math.min(centred, highest));
    }
    function settledStart(island) {
        const middleStart = middleStartFor(leading.targetExtent, middle.targetExtent, trailing.targetExtent);
        if (island === middle) return middleStart;
        if (island === media) return Math.max(insetStart, middleStart - spacing - media.targetExtent);
        if (island === leading) return Math.max(insetStart, middleStart - mediaRun - spacing - leading.targetExtent);
        return Math.min(length - insetEnd - trailing.targetExtent, middleStart + middle.targetExtent + spacing);
    }
    // The open panel sits exactly where its island settles, in the panel's coordinates.
    function panelOrigin(panel, stripX, stripY) {
        const island = islandFor(panel);
        if (!island || !panel.parent) return Qt.point(stripX, stripY);
        const origin = dynamic.mapToItem(panel.parent, 0, 0);
        const start = settledStart(island);
        const offset = island.farEdge ? island.thickness - island.targetDepth : 0;
        return vertical ? Qt.point(origin.x + offset, origin.y + start) : Qt.point(origin.x + start, origin.y + offset);
    }
    // The three islands sit together at the centre: the clock stays screen-centred, the
    // others keep one gap from it and grow outward, sliding out when the clock grows.
    DynamicIsland {
        id: leading
        host: dynamic.host; barHost: dynamic.barHost
        readonly property var after: dynamic.mediaAvailable ? media : middle
        x: vertical ? depthOffset : Math.max(insetStart, after.x - spacing - width)
        y: vertical ? Math.max(insetStart, after.y - spacing - height) : depthOffset
        panel: dynamic.openPanel(leading)
        restingExtent: host.workspaceItemSize + 8
        contentExtent: leadingExtent
        fullExtent: Math.max(restingExtent, Math.min(leadingExtent, (length - middleRoom) / 2 - insetStart - spacing - mediaRun))
        held: dynamic.active(leftPanels) || barHost.pendingOverview || barHost.overviewOpen || (dynamic.controlCenterOpen && dynamic.controlCenterOwner === "left")
    }
    DynamicIsland {
        id: media
        host: dynamic.host; barHost: dynamic.barHost
        visible: dynamic.mediaAvailable
        x: vertical ? depthOffset : Math.max(insetStart, middle.x - spacing - width)
        y: vertical ? Math.max(insetStart, middle.y - spacing - height) : depthOffset
        panel: dynamic.openPanel(media)
        restingExtent: dynamic.mediaExtent
        fullExtent: restingExtent
        held: barHost.mediaMenu.visible || barHost.pendingPanel === barHost.mediaMenu
    }
    DynamicIsland {
        id: middle
        host: dynamic.host; barHost: dynamic.barHost
        x: vertical ? depthOffset : dynamic.middleStartFor(leading.extent, extent, trailing.extent)
        y: vertical ? dynamic.middleStartFor(leading.extent, extent, trailing.extent) : depthOffset
        panel: dynamic.openPanel(middle)
        restingExtent: clockExtent + 8 + captureLength
        // Beside a card from another island, expand only into the space that is left.
        fullExtent: Math.max(restingExtent, Math.min(middleExtent, length - 2 * Math.max(
            insetStart + (leading.morphed ? leading.targetExtent : leading.restingExtent) + spacing + dynamic.mediaRun,
            insetEnd + (trailing.morphed ? trailing.targetExtent : trailing.restingExtent) + spacing)))
        held: dynamic.active(middlePanels)
    }
    DynamicIsland {
        id: trailing
        host: dynamic.host; barHost: dynamic.barHost
        x: vertical ? depthOffset : Math.min(dynamic.width - insetEnd - width, middle.x + middle.width + spacing)
        y: vertical ? Math.min(dynamic.height - insetEnd - height, middle.y + middle.height + spacing) : depthOffset
        panel: dynamic.openPanel(trailing)
        restingExtent: host.workspaceItemSize * (host.battery.available ? 2 : 1) + (host.battery.available ? host.workspaceItemSpacing : 0) + 8
        contentExtent: trailingExtent
        trailingAnchor: true
        fullExtent: Math.max(restingExtent, Math.min(trailingExtent, (length - middleRoom) / 2 - insetEnd - spacing))
        held: barHost.dockPanels.some(panel => !dynamic.owns(panel, leftPanels) && !dynamic.owns(panel, middlePanels)
            && panel !== barHost.controlCenter && (panel.visible || panel === barHost.pendingPanel))
            || (dynamic.controlCenterOpen && dynamic.controlCenterOwner === "right")
    }
    Item {
        parent: trailing
        width: vertical ? trailing.thickness : trailing.width
        height: vertical ? trailing.height : trailing.thickness
        x: vertical && trailing.farEdge ? trailing.width - width : 0
        y: !vertical && trailing.farEdge ? trailing.height - height : 0
        visible: !trailing.expanded && !trailing.morphed
        Grid {
            objectName: "dynamicRestingStatus"
            anchors.centerIn: parent
            // Only as many cells as icons: an empty battery cell would keep its spacing
            // and push WiFi off centre.
            readonly property int count: host.battery.available ? 2 : 1
            columns: dynamic.vertical ? 1 : count
            rows: dynamic.vertical ? count : 1
            spacing: host.workspaceItemSpacing
            RestingGlyph {
                glyph: host.focusNetworkGlyph; tooltip: "WiFi"
                onClicked: barHost.togglePanel(barHost.wifiMenu)
            }
            RestingGlyph {
                visible: host.battery.available
                glyph: host.batteryIcon; tooltip: Math.round(host.battery.percent) + "% · " + host.battery.status
                onClicked: barHost.togglePanel(barHost.batteryMenu)
            }
        }
    }
    // Glyphs such as WiFi's fan are not centred in their font box; centre the drawn shape.
    component RestingGlyph: Item {
        id: restingGlyph
        property string glyph: ""
        property string tooltip: ""
        signal clicked()
        width: host.workspaceItemSize; height: host.workspaceItemSize
        TextMetrics { id: ink; font: label.font; text: restingGlyph.glyph }
        Text {
            id: label
            text: restingGlyph.glyph; color: host.fg
            font.family: DesktopFonts.family; font.pixelSize: 15; font.bold: true
            x: (restingGlyph.width - ink.tightBoundingRect.width) / 2 - ink.tightBoundingRect.x
            y: (restingGlyph.height - ink.tightBoundingRect.height) / 2 - label.baselineOffset - ink.tightBoundingRect.y
        }
        MouseArea { id: glyphArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: restingGlyph.clicked() }
        BarTooltip { target: restingGlyph; hovered: glyphArea.containsMouse; text: restingGlyph.tooltip; foreground: host.fg; background: host.barBackground() }
    }
    // Anchored groups move into the islands through a plain parent change: ParentChange
    // would write their entry geometry back as fixed values on leaving, freezing their sizes.
    states: [
        State {
            name: "horizontal"; when: dynamic.holding && !dynamic.vertical
            PropertyChanges { target: barHost.leftGroup; parent: leading.content; x: 4; y: (leading.thickness - barHost.leftGroup.height) / 2 }
            PropertyChanges { target: barHost.leftGroup; width: barHost.leftGroup.implicitWidth }
            PropertyChanges { target: barHost.barHorizontalCenter; parent: middle.content }
            PropertyChanges { target: barHost.centerInfo; timeOnly: !middle.expanded; anchors.horizontalCenterOffset: dynamic.clockShift }
            PropertyChanges { target: barHost.rightSide; parent: trailing.content }
            PropertyChanges { target: barHost.notificationIcon; parent: trailing.content }
            PropertyChanges { target: barHost.notificationIcon; anchors.rightMargin: 4; opacity: trailing.expanded ? 1 : 0; enabled: trailing.expanded }
            PropertyChanges { target: barHost.rightSide; opacity: trailing.expanded ? 1 : 0; enabled: trailing.expanded }
            AnchorChanges { target: barHost.mediaStrip; anchors.right: undefined; anchors.verticalCenter: undefined }
            PropertyChanges { target: barHost.mediaStrip; parent: media.content; x: 8; y: (media.thickness - barHost.mediaStrip.height) / 2 }
            PropertyChanges { target: barHost.mediaStrip; availableWidth: 460; opacity: 1; enabled: true }
        },
        State {
            name: "vertical"; when: dynamic.holding && dynamic.vertical
            PropertyChanges { target: barHost.verticalStart; parent: leading.content; y: 4 }
            PropertyChanges { target: barHost.verticalMiddle; parent: middle.content }
            PropertyChanges { target: barHost.verticalCalendarIcon; timeOnly: !middle.expanded; anchors.verticalCenterOffset: dynamic.clockShift }
            PropertyChanges { target: barHost.verticalEnd; parent: trailing.content }
            PropertyChanges { target: barHost.verticalEnd; anchors.bottomMargin: 4; opacity: trailing.expanded ? 1 : 0; enabled: trailing.expanded }
            AnchorChanges { target: barHost.verticalMedia; anchors.bottom: undefined; anchors.horizontalCenter: undefined }
            PropertyChanges { target: barHost.verticalMedia; parent: media.content; y: 8; x: (media.thickness - barHost.verticalMedia.width) / 2 }
            PropertyChanges { target: barHost.verticalMedia; visible: dynamic.mediaAvailable }
        }
    ]
}
