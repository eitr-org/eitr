import QtQuick
import Eitr as Eitr
import QtQuick.Controls.Basic as Controls
import "PanelStyle.js" as PanelStyle
import "JsonState.js" as JsonState
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    implicitWidth: 428
    property int maximumHeight: 1000
    implicitHeight: Math.min(contentColumn.implicitHeight + (trialFooter.visible ? trialFooter.height + 8 : 0)
        + verticalContentInset, maximumHeight)
    keyTarget: content
    property var state: ({available: false, name: "Checking brightness", value: 0})
    property int requested: -1
    property int applied: -1
    property var nightlight: ({mode: "auto", enabled: false, available: false})
    property var monitors: []
    property string primaryDisplay: ""
    property string displayError: ""
    signal primarySelected(string name)
    property string nightlightError: ""
    // Status-read failures clear on the next successful read; action and
    // validation errors stay until the user acts again.
    readonly property string displayStatusError: "Display status unavailable"
    readonly property string nightlightStatusError: "Nightlight status unavailable"
    property bool scheduleDirty: false
    property bool editingSchedule: false
    readonly property var timeLocale: Qt.locale()
    readonly property string helper: Quickshell.shellDir + "/scripts/brightness.py"
    readonly property string nightlightHelper: Eitr.Paths.code("walker/scripts/actions/toggle/nightlight.py")
    readonly property string displayHelper: Quickshell.shellDir + "/scripts/display-primary.py"
    // Display settings apply at once; a new resolution or refresh rate is kept only on Keep.
    readonly property string settingsHelper: Quickshell.shellDir + "/scripts/display-settings.py"
    property var displaySettings: ({monitors: []})
    property string settingsFor: ""
    property int trialSeconds: 0
    readonly property int trialLength: 15
    // Laptop-only: the helper reports unavailable without a system battery
    // or power-profiles-daemon, which hides the whole Power Profile section.
    property var power: ({available: false, active: "", profiles: []})
    property string powerError: ""
    readonly property bool powerBusy: powerOperation.running
    readonly property string powerHelper: Quickshell.shellDir + "/scripts/power-profile.py"
    readonly property var powerProfiles: [
        {name: "power-saver", label: "Power Saver"},
        {name: "balanced", label: "Balanced"},
        {name: "performance", label: "Performance"}
    ]

    function refresh() {
        if (!query.running && !operation.running && !slider.pressed && !settle.running) query.running = true;
    }
    function applyValue(value) {
        requested = value;
        if (!operation.running) startSet();
    }
    function startSet() {
        if (requested < 0) return;
        applied = requested;
        operation.command = ["python3", helper, "set", String(applied), String(state.maximum || 100)];
        operation.running = true;
    }
    function refreshNightlight() {
        if (!nightQuery.running && !nightOperation.running) nightQuery.running = true;
    }
    function refreshDisplays() {
        if (!displayQuery.running && !setPrimary.running) displayQuery.running = true;
    }
    function refreshDisplaySettings() {
        if (!settingsQuery.running) settingsQuery.running = true;
    }
    // Displays this one can be placed beside: any other except those already placed
    // beside it (directly or through others), which would make the two follow each other.
    function placeableBeside(name) {
        const anchors = {};
        for (const item of (displaySettings.monitors || [])) if (item.anchor) anchors[item.name] = item.anchor.of;
        return monitors.map(item => item.name).filter(other => {
            if (other === name) return false;
            for (let step = other, guard = 0; step && guard < 16; step = anchors[step], guard++)
                if (step === name) return false;
            return true;
        });
    }
    function trySetting(name, key, value) {
        if (trialOperation.running) return;
        displayError = "";
        trialOperation.command = ["python3", settingsHelper, "set", name, key, value];
        trialOperation.running = true;
    }
    function finishTrial(action) {
        trialCountdown.stop();
        trialSeconds = 0;
        Quickshell.execDetached(["python3", settingsHelper, action]);
        afterTrial.restart();
    }
    function refreshPower() {
        if (!powerQuery.running && !powerOperation.running) powerQuery.running = true;
    }
    function setPowerProfile(name) {
        if (powerOperation.running || name === power.active) return;
        powerError = "";
        powerOperation.command = ["python3", powerHelper, "set", name];
        powerOperation.running = true;
    }
    function selectPrimary(name) {
        if (setPrimary.running || name === primaryDisplay) return;
        displayError = "";
        setPrimary.command = ["python3", displayHelper, "set", name];
        setPrimary.running = true;
    }
    function setNightlight(mode) {
        if (nightOperation.running) return;
        if (scheduleDirty) { configureNightlight(mode); return; }
        nightlightError = "";
        nightOperation.command = ["python3", nightlightHelper, "set", mode];
        nightOperation.running = true;
    }
    function displayTime(value) {
        if (!value) return "";
        let parts = value.split(":");
        return new Date(2000, 0, 1, Number(parts[0]), Number(parts[1])).toLocaleTimeString(timeLocale, Locale.ShortFormat);
    }
    function parseTime(value) {
        let date = Date.fromLocaleTimeString(timeLocale, value.trim(), Locale.ShortFormat);
        if (!date || isNaN(date.getTime())) return "";
        return String(date.getHours()).padStart(2, "0") + ":" + String(date.getMinutes()).padStart(2, "0");
    }
    function syncSchedule() {
        if (scheduleDirty) return;
        startField.text = displayTime(nightlight.start || "18:00");
        endField.text = displayTime(nightlight.end || "09:00");
    }
    function configureNightlight(mode) {
        configureNightlightTimes(startField.text, endField.text, mode);
    }
    function configureNightlightTimes(startText, endText, mode) {
        let start = parseTime(startText);
        let end = parseTime(endText);
        if (!start || !end || start === end) {
            nightlightError = "Enter two different valid times";
            return;
        }
        if (nightOperation.running) return;
        nightlightError = "";
        nightOperation.command = ["python3", nightlightHelper, "configure", start, end, mode];
        nightOperation.running = true;
    }
    // Fetch once in the background after the bar starts, so the first opening already
    // has its data; later openings query only after the unfold (DockPanel.revealed),
    // since starting the helpers during it stalls the animation.
    Timer { interval: 8000; running: true; onTriggered: { menu.refresh(); menu.refreshNightlight(); menu.refreshDisplays(); menu.refreshPower(); } }
    onRevealed: { refresh(); refreshNightlight(); refreshDisplays(); refreshPower(); }
    onOpenedChanged: {
        if (!opened) {
            editingSchedule = false;
            settingsFor = "";
            if (scheduleDirty) scheduleSettle.restart();
        }
    }
    // DDC monitors are not polled: only this panel changes their brightness.
    Timer { interval: 3000; repeat: true; running: menu.opened; onTriggered: { if (menu.state.kind !== "ddc") menu.refresh(); menu.refreshNightlight(); menu.refreshPower(); } }
    Timer { interval: 6000; repeat: true; running: menu.opened; onTriggered: menu.refreshDisplays() }
    Timer { id: scheduleSettle; interval: 650; onTriggered: if (menu.scheduleDirty && !nightOperation.running) menu.configureNightlight(menu.nightlight.mode) }
    Timer { id: settle; interval: 80; onTriggered: menu.applyValue(Math.round(slider.value)) }
    // Mirrors the revert timer display-settings.py starts; that timer reverts even if the panel closes.
    Timer {
        id: trialCountdown
        interval: 1000; repeat: true
        onTriggered: {
            menu.trialSeconds -= 1;
            if (menu.trialSeconds <= 0) { stop(); afterTrial.restart(); }
        }
    }
    Timer { id: afterTrial; interval: 1200; onTriggered: { menu.refreshDisplays(); menu.refreshDisplaySettings(); } }
    Process {
        id: settingsQuery
        command: ["python3", menu.settingsHelper, "list"]
        stdout: StdioCollector { id: settingsOutput }
        onExited: {
            const received = settingsOutput.text;
            menu.updateContent(function() { try { let settings = JSON.parse(received); if (JsonState.changed(menu.displaySettings, settings)) menu.displaySettings = settings; } catch (e) {}
            });
        }
    }
    Process {
        id: trialOperation
        stdout: StdioCollector { id: trialOutput }
        stderr: StdioCollector { id: trialErrors }
        onExited: function(code) {
            if (code !== 0) {
                // The helper explains refusals, such as two displays that would overlap.
                const reason = trialErrors.text.trim().replace(/^display-settings: /, "");
                menu.displayError = reason || Eitr.I18n.tr("Could not change display settings");
                return;
            }
            menu.displayError = "";
            // A new resolution, refresh rate or HDR toggle is tried with a countdown; it could leave
            // a screen black. Every other change is already saved.
            let result = {};
            try { result = JSON.parse(trialOutput.text); } catch (e) {}
            if (result.trial) {
                menu.trialSeconds = menu.trialLength;
                trialCountdown.restart();
                // The display change takes a moment while the monitor resynchronizes.
                afterTrial.restart();
            } else {
                menu.refreshDisplays();
                menu.refreshDisplaySettings();
            }
        }
    }
    Process {
        id: query
        command: ["python3", menu.helper, "status"]
        stdout: StdioCollector { id: queryOutput }
        onExited: {
            const received = queryOutput.text;
            menu.updateContent(function() {
                let state;
                try { state = JSON.parse(received); }
                catch (e) { state = {available: false, name: Eitr.I18n.tr("Brightness unavailable"), value: 0}; }
                if (JsonState.changed(menu.state, state)) menu.state = state;

            });
        }
    }
    Process {
        id: operation
        stdout: StdioCollector { id: operationOutput }
        onExited: {
            try { menu.state = JSON.parse(operationOutput.text); }
            catch (e) { menu.state = {available: false, name: Eitr.I18n.tr("Brightness unavailable"), value: 0}; }
            if (menu.state.available) {
                brightnessOsd.command = ["swayosd-client", "--custom-icon", "display-brightness-symbolic", "--custom-progress", String(menu.state.value / 100)];
                if (!brightnessOsd.running) brightnessOsd.running = true;
            }
            if (menu.requested !== menu.applied) menu.startSet();
        }
    }
    Process { id: brightnessOsd; command: ["swayosd-client", "--custom-icon", "display-brightness-symbolic", "--custom-progress", "0"] }
    Process {
        id: powerQuery
        command: ["python3", menu.powerHelper, "status"]
        stdout: StdioCollector { id: powerQueryOutput }
        onExited: {
            const received = powerQueryOutput.text;
            menu.updateContent(function() {
                let power;
                try { power = JSON.parse(received); }
                catch (e) { power = {available: false, active: "", profiles: []}; }
                if (JsonState.changed(menu.power, power)) menu.power = power;

            });
        }
    }
    Process {
        id: powerOperation
        stdout: StdioCollector { id: powerOperationOutput }
        onExited: function(code) {
            if (code !== 0) {
                menu.powerError = "Could not change power profile";
                menu.refreshPower();
                return;
            }
            try { menu.power = JSON.parse(powerOperationOutput.text); }
            catch (e) { menu.refreshPower(); }
        }
    }
    Process {
        id: displayQuery
        command: ["python3", menu.displayHelper, "status"]
        stdout: StdioCollector { id: displayOutput }
        onExited: {
            const received = displayOutput.text;
            menu.updateContent(function() {
                try {
                    let result = JSON.parse(received);
                    if (JsonState.changed(menu.monitors, result.monitors || [])) menu.monitors = result.monitors || [];
                    menu.primaryDisplay = result.primary || "";
                    if (menu.displayError === menu.displayStatusError) menu.displayError = "";
                } catch (e) { menu.displayError = menu.displayStatusError; }

            });
        }
    }
    Process {
        id: setPrimary
        stdout: StdioCollector { id: setPrimaryOutput }
        onExited: function(code) {
            if (code !== 0) {
                menu.displayError = Eitr.I18n.tr("Could not set the main display");
                menu.refreshDisplays();
                return;
            }
            try {
                let result = JSON.parse(setPrimaryOutput.text);
                menu.monitors = result.monitors || [];
                menu.primaryDisplay = result.primary || "";
                menu.primarySelected(menu.primaryDisplay);
                // The main display stays put and the others are placed around it, so positions change meaning.
                menu.refreshDisplaySettings();
            } catch (e) { menu.displayError = menu.displayStatusError; }
        }
    }
    Process {
        id: nightQuery
        command: ["python3", menu.nightlightHelper, "status"]
        stdout: StdioCollector { id: nightQueryOutput }
        onExited: {
            const received = nightQueryOutput.text;
            menu.updateContent(function() {
                try {
                    let nightlight = JSON.parse(received);
                    if (JsonState.changed(menu.nightlight, nightlight)) { menu.nightlight = nightlight; menu.syncSchedule(); }
                    if (menu.nightlightError === menu.nightlightStatusError) menu.nightlightError = "";
                }
                catch (e) { menu.nightlightError = menu.nightlightStatusError; }

            });
        }
    }
    Process {
        id: nightOperation
        stdout: StdioCollector { id: nightOperationOutput }
        onExited: function(code) {
            if (code !== 0) menu.nightlightError = "Could not update nightlight";
            else {
                try {
                    menu.nightlight = JSON.parse(nightOperationOutput.text);
                    let command = nightOperation.command;
                    let changedDuringRequest = command[2] === "configure" &&
                        (menu.parseTime(startField.text) !== command[3] || menu.parseTime(endField.text) !== command[4]);
                    if (changedDuringRequest) scheduleSettle.restart();
                    else { menu.scheduleDirty = false; menu.syncSchedule(); }
                }
                catch (e) { menu.nightlightError = menu.nightlightStatusError; }
            }
            menu.refreshNightlight();
        }
    }
    Item {
        id: content
        anchors.fill: parent
        anchors.margins: 0
        focus: true
        Keys.onEscapePressed: menu.opened = false
        Flickable {
            id: displayScroll
            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
            anchors.bottom: trialFooter.visible ? trialFooter.top : parent.bottom
            anchors.bottomMargin: trialFooter.visible ? 8 : 0
            contentHeight: contentColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: contentColumn
                width: parent.width
                spacing: 12
                PanelHeading { text: Eitr.I18n.tr("Display"); foreground: menu.foreground; accent: menu.accent; rune: "display" }
                // Only built-in laptop screens get a slider; desktop monitors have their own controls.
                Row {
                    visible: menu.state.kind === "backlight"
                    width: parent.width
                    spacing: 10
                    Text { width: 30; height: 30; text: "󰃟"; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 18 }
                    PanelSlider {
                        id: slider
                        accent: menu.accent
                        foreground: menu.foreground
                        width: parent.width - 100
                        from: 1
                        to: 100
                        stepSize: 1
                        enabled: menu.state.available
                        Binding { target: slider; property: "value"; value: menu.state.value || 1; when: !slider.pressed && !operation.running && !settle.running }
                        onMoved: {
                            if (menu.state.kind === "backlight") menu.applyValue(Math.round(value));
                            else settle.restart();
                        }
                    }
                    Text { width: 50; height: 30; text: Math.round(slider.value) + "%"; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.features: PanelStyle.tabularFigures }
                }
                Column {
                    visible: menu.power.available
                    width: parent.width
                    spacing: 12
                    PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
                    Text { text: Eitr.I18n.tr("Power Profile"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                    Row {
                        id: powerRow
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: menu.powerProfiles
                            PanelButton {
                                required property var modelData
                                width: (powerRow.width - powerRow.spacing * 2) / 3
                                text: modelData.label
                                foreground: menu.foreground
                                available: menu.power.profiles.indexOf(modelData.name) >= 0
                                loading: powerOperation.running && powerOperation.command[3] === modelData.name
                                selected: menu.power.active === modelData.name
                                onClicked: menu.setPowerProfile(modelData.name)
                            }
                        }
                    }
                    Text {
                        visible: menu.powerError !== ""
                        text: menu.powerError
                        color: menu.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                    }
                }
                PanelDivider { visible: menu.state.kind === "backlight" || menu.power.available; width: parent.width; height: 8; foreground: menu.foreground }
                Row {
                    width: parent.width
                    height: 40
                    Column {
                        width: parent.width - 88
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2
                        Text { text: Eitr.I18n.tr("Night Light"); color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                        Text { width: parent.width; elide: Text.ElideRight; text: menu.nightlight.mode === "auto" ? Eitr.I18n.tr("Automatic · {start} - {end}", {start: menu.displayTime(menu.nightlight.start || "18:00"), end: menu.displayTime(menu.nightlight.end || "09:00")}) : Eitr.I18n.tr("Manual"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                    }
                    PanelButton {
                        id: editButton
                        icon: true
                        width: 28
                        height: 28
                        anchors.verticalCenter: parent.verticalCenter
                        text: "󰏫"
                        foreground: menu.foreground
                        available: menu.nightlight.available
                        selected: menu.editingSchedule
                        onClicked: {
                            if (menu.editingSchedule && menu.scheduleDirty) scheduleSettle.restart();
                            if (!menu.editingSchedule) menu.syncSchedule();
                            menu.editingSchedule = !menu.editingSchedule;
                        }
                        HoverHandler { id: editHover }
                        BarTooltip { target: editButton; hovered: editHover.hovered; text: Eitr.I18n.tr("Edit schedule"); background: menu.background; foreground: menu.foreground }
                    }
                    Item { width: 8; height: 1 }
                    PanelSwitch {
                        anchors.verticalCenter: parent.verticalCenter
                        checked: menu.nightlight.enabled
                        enabled: menu.nightlight.available && !nightOperation.running
                        foreground: menu.foreground
                        accent: menu.accent
                        onClicked: menu.setNightlight(checked ? "on" : "off")
                    }
                }
                Column {
                    visible: menu.editingSchedule
                    width: parent.width
                    height: visible ? 58 : 0
                    spacing: 2
                    Row {
                        width: parent.width
                        height: 16
                        spacing: 8
                        Text { width: (parent.width - 68) / 2; height: parent.height; text: Eitr.I18n.tr("Start"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { width: (parent.width - 68) / 2; height: parent.height; text: Eitr.I18n.tr("End"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                        Text { width: 52; height: parent.height; text: Eitr.I18n.tr("Auto"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                    }
                    Row {
                        width: parent.width
                        height: 40
                        spacing: 8
                        Controls.TextField {
                            id: startField
                            width: (parent.width - 68) / 2
                            height: parent.height
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            selectByMouse: true
                            onTextEdited: { menu.scheduleDirty = true; scheduleSettle.restart(); }
                            HoverHandler { cursorShape: Qt.IBeamCursor }
                            background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08); border.width: 1; border.color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.2) }
                        }
                        Controls.TextField {
                            id: endField
                            width: (parent.width - 68) / 2
                            height: parent.height
                            color: menu.foreground
                            font.family: DesktopFonts.family
                            font.pixelSize: PanelStyle.bodySize
                            selectByMouse: true
                            onTextEdited: { menu.scheduleDirty = true; scheduleSettle.restart(); }
                            HoverHandler { cursorShape: Qt.IBeamCursor }
                            background: Rectangle { radius: DesktopStyle.radius(PanelStyle.controlRadius); color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.08); border.width: 1; border.color: Qt.rgba(menu.foreground.r, menu.foreground.g, menu.foreground.b, 0.2) }
                        }
                        PanelSwitch {
                            anchors.verticalCenter: parent.verticalCenter
                            checked: menu.nightlight.mode === "auto"
                            enabled: menu.nightlight.available && !nightOperation.running
                            foreground: menu.foreground
                            accent: menu.accent
                            onClicked: {
                                scheduleSettle.stop();
                                menu.configureNightlight(checked ? "auto" : (menu.nightlight.enabled ? "on" : "off"));
                            }
                        }
                    }
                }
                Text {
                    visible: menu.nightlightError !== ""
                    text: menu.nightlightError
                    color: menu.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                }
                PanelDivider { width: parent.width; height: 8; foreground: menu.foreground }
                Item {
                    width: content.width
                    height: 28
                    Text { anchors.verticalCenter: parent.verticalCenter; text: Eitr.I18n.tr("Displays"); color: menu.foreground; opacity: PanelStyle.secondaryTextOpacity; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                }
                Text { visible: menu.displayError !== ""; text: menu.displayError; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                Text {
                    visible: menu.monitors.length === 0
                    height: visible ? 36 : 0
                    text: Eitr.I18n.tr("No active displays")
                    color: menu.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                }
                Column {
                width: content.width; spacing: PanelStyle.selectionRowGap
                Repeater {
                    model: menu.monitors
                    // Each display's row; when selected, its settings open right under it.
                    Item {
                    id: displayEntry
                    required property var modelData
                    readonly property bool editing: menu.settingsFor === modelData.name
                    readonly property bool isMain: modelData.name === menu.primaryDisplay
                    width: content.width
                    height: entryColumn.implicitHeight
                    Column {
                    id: entryColumn
                    width: displayEntry.width
                    spacing: 10
                    Rectangle {
                        width: parent.width
                        height: PanelStyle.selectionRowHeight
                        radius: DesktopStyle.radius(PanelStyle.controlRadius)
                        color: Qt.alpha(menu.foreground, PanelStyle.selectionAlpha(displayEntry.editing, displayHover.hovered))
                        border.width: PanelStyle.selectionBorderWidth(displayEntry.editing)
                        border.color: Qt.alpha(menu.foreground, PanelStyle.selectionBorderAlpha)
                        HoverHandler { id: displayHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler {
                            onTapped: {
                                menu.settingsFor = displayEntry.editing ? "" : displayEntry.modelData.name;
                                if (menu.settingsFor) menu.refreshDisplaySettings();
                            }
                        }
                        BarTooltip { target: parent; hovered: displayHover.hovered; text: displayEntry.editing ? Eitr.I18n.tr("Close its settings") : Eitr.I18n.tr("Resolution, position and more"); background: menu.background; foreground: menu.foreground }
                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 10
                            spacing: 8
                            Text { width: 22; height: parent.height; text: "󰍹"; verticalAlignment: Text.AlignVCenter; color: displayEntry.editing ? menu.accent : menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 16 }
                            Text { width: parent.width - 250; height: parent.height; text: displayEntry.modelData.name + (displayEntry.modelData.model ? " · " + displayEntry.modelData.model : ""); elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize }
                            // Beside the name, well clear of the resolution on the right.
                            Text { width: 62; height: parent.height; text: displayEntry.isMain ? Eitr.I18n.tr("Main") : ""; horizontalAlignment: Text.AlignLeft; verticalAlignment: Text.AlignVCenter; color: menu.accent; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize; font.bold: true }
                            Text { width: 112; height: parent.height; text: Eitr.I18n.tr("{width}×{height} · {rate} Hz", {width: displayEntry.modelData.width, height: displayEntry.modelData.height, rate: Math.round(displayEntry.modelData.refreshRate)}); horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter; color: menu.foreground; opacity: 0.75; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.captionSize }
                            Text { width: 16; height: parent.height; text: displayEntry.editing ? "󰅀" : "󰅂"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; color: menu.accent; font.family: DesktopFonts.family; font.pixelSize: 16 }
                        }
                    }
                    DisplaySettingsEditor {
                        readonly property var details: (menu.displaySettings.monitors || []).find(item => item.name === displayEntry.modelData.name)
                        visible: displayEntry.editing && !!details
                        height: visible ? implicitHeight : 0
                        width: parent.width
                        monitor: details || ({})
                        others: menu.monitors.map(item => item.name).filter(name => name !== displayEntry.modelData.name)
                        placeable: menu.placeableBeside(displayEntry.modelData.name)
                        isMain: displayEntry.isMain
                        foreground: menu.foreground
                        background: menu.background
                        accent: menu.accent
                        busy: trialOperation.running || setPrimary.running || menu.trialSeconds > 0
                        onTryChange: function(key, value) { menu.trySetting(displayEntry.modelData.name, key, value); }
                        onMakeMain: menu.selectPrimary(displayEntry.modelData.name)
                    }
                    }
                    }
                }
                }
                PanelFooterLink {
                    id: handEditButton
                    width: content.width
                    text: Eitr.I18n.tr("Edit layout by hand…")
                    foreground: menu.foreground
                    onClicked: Quickshell.execDetached(["python3", menu.settingsHelper, "edit"])
                    HoverHandler { id: handEditHover }
                    BarTooltip { target: handEditButton; hovered: handEditHover.hovered; text: Eitr.I18n.tr("Rotation, pixel offsets and more in local.lua"); background: menu.background; foreground: menu.foreground }
                }
            }
        }
        // Pinned below the scrolling content, so Keep is visible however tall the editor is.
        Rectangle {
            id: trialFooter
            visible: menu.trialSeconds > 0
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            height: visible ? 44 : 0
            radius: DesktopStyle.radius(PanelStyle.controlRadius)
            color: Qt.alpha(menu.foreground, 0.08)
            Text {
                anchors.left: parent.left; anchors.leftMargin: 10
                anchors.right: revertButton.left; anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                text: menu.trialSeconds === 1 ? Eitr.I18n.tr("Keep these settings? Reverting in {seconds} second", {seconds: menu.trialSeconds}) : Eitr.I18n.tr("Keep these settings? Reverting in {seconds} seconds", {seconds: menu.trialSeconds})
                elide: Text.ElideRight
                color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.secondarySize
            }
            PanelButton {
                id: revertButton
                anchors.right: keepButton.left; anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: 72; height: 30
                text: Eitr.I18n.tr("Revert")
                outlined: true
                foreground: menu.foreground
                onClicked: menu.finishTrial("revert")
            }
            PanelButton {
                id: keepButton
                anchors.right: parent.right; anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: 72; height: 30
                text: Eitr.I18n.tr("Keep")
                selected: true
                foreground: menu.foreground
                onClicked: menu.finishTrial("keep")
            }
        }
    }
}
