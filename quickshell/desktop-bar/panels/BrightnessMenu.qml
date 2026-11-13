import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle
import Quickshell
import Quickshell.Io

ThemedPopup {
    id: menu
    readonly property alias startField: nightlightSection.startFieldItem
    readonly property alias endField: nightlightSection.endFieldItem
    function revealSearchSetting(identifier) {
        if (identifier.indexOf("displays-schedule-") === 0) editingSchedule = true;
        if (settingsSection !== "nightlight" && monitors.length && !settingsFor) settingsFor = monitors[0].name;
    }
    implicitWidth: 428
    property string settingsSection: "all"
    property color mapHighlight: accent
    property int maximumHeight: 1000
    implicitHeight: Math.min(contentColumn.implicitHeight + (trialFooter.visible ? trialFooter.height + 8 : 0)
        + verticalContentInset, maximumHeight)
    keyTarget: content
    property var state: ({available: false, name: "Checking brightness", value: 0})
    property int requested: -1
    property int applied: -1
    property var nightlight: ({mode: "auto", enabled: false, available: false})
    property var monitors: DisplayService.topology.monitors
    property string primaryDisplay: DisplayService.topology.primary
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
    onMonitorsChanged: if (settingsFor && !monitors.some(monitor => monitor.name === settingsFor)) settingsFor = ""
    property string requestedMonitor: ""
    property var pendingMonitor: null
    property int trialSeconds: 0
    readonly property int trialLength: 15
    // Laptop-only: the helper reports unavailable without a system battery
    // or power-profiles-daemon, which hides the whole Power Profile section.
    property var power: PowerService.profile
    property string powerError: ""
    readonly property bool powerBusy: PowerService.busy
    property var powerTokens: []
    property string powerActionId: ""
    property string powerRequested: ""
    Component.onDestruction: { DisplayService.close(menu); DisplayService.resumeBrightness(menu); DisplayService.resumeNightlight(menu); DesktopData.releaseOwner(menu); DesktopData.client.detachAction(powerActionId); }
    Connections {
        target: PowerService
        function onProfileChanged() { menu.updateContent(function() { menu.power = PowerService.profile; }); }
    }
    readonly property var powerProfiles: [
        {name: "power-saver", label: "Power Saver"},
        {name: "balanced", label: "Balanced"},
        {name: "performance", label: "Performance"}
    ]

    function refresh() { DisplayService.refreshBrightness(); }
    function applyValue(value) {
        DisplayService.pauseBrightness(menu);
        requested = value;
        if (!operation.running) startSet();
    }
    function startSet() {
        if (requested < 0) return;
        applied = requested;
        operation.command = ["python3", helper, "set", String(applied), String(state.maximum || 100)];
        operation.running = true;
    }
    function refreshNightlight() { DesktopData.refresh("display.nightlight"); }
    function refreshDisplays() { DisplayService.refresh(); }
    function refreshDisplaySettings() { DesktopData.refresh("display.settings"); }
    readonly property var brightnessSnapshot: DesktopData.topics["display.brightness"]
    readonly property var nightSnapshot: DesktopData.topics["display.nightlight"]
    readonly property var topologySnapshot: DesktopData.topics["display.topology"]
    onTopologySnapshotChanged: if (topologySnapshot) {
        if (topologySnapshot.error) displayError = displayStatusError;
        else if (topologySnapshot.status === "ready" && displayError === displayStatusError) displayError = "";
    }
    readonly property var settingsSnapshot: DesktopData.topics["display.settings"]
    onBrightnessSnapshotChanged: if (brightnessSnapshot && brightnessSnapshot.status === "ready" && !operation.running && !slider.pressed && !settle.running) {
        const received = brightnessSnapshot.data;
        updateContent(function() { menu.state = received; });
    }
    onNightSnapshotChanged: if (nightSnapshot && nightSnapshot.status === "ready" && !nightOperation.running) {
        const received = nightSnapshot.data;
        updateContent(function() { menu.nightlight = received; menu.syncSchedule(); });
        if (nightlightError === nightlightStatusError) nightlightError = "";
    } else if (nightSnapshot && nightSnapshot.error) nightlightError = nightlightStatusError;
    onSettingsSnapshotChanged: if (settingsSnapshot && settingsSnapshot.status === "ready") {
        const received = settingsSnapshot.data;
        updateContent(function() { menu.displaySettings = received; });
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
        requestedMonitor = name;
        trialOperation.command = ["python3", settingsHelper, "set", name, key, value];
        trialOperation.running = true;
    }
    function finishTrial(action) {
        trialCountdown.stop();
        trialSeconds = 0;
        pendingMonitor = null;
        Quickshell.execDetached(["python3", settingsHelper, action]);
        afterTrial.restart();
    }
    function refreshPower() { PowerService.refresh(); }
    function setPowerProfile(name) {
        if (powerBusy || name === power.active) return;
        powerError = "";
        powerRequested = name;
        powerActionId = PowerService.act("profile", name, function(code) {
            menu.powerError = code ? "Could not change power profile" : "";
        });
        if (!powerActionId) powerError = "Could not change power profile";
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
        DisplayService.pauseNightlight(menu);
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
        DisplayService.pauseNightlight(menu);
        nightOperation.running = true;
    }
    onRevealed: { DisplayService.open(menu); refreshDisplays(); }
    onOpenedChanged: {
        PowerService.release(powerTokens);
        powerTokens = opened ? PowerService.observe(menu, 3, false) : [];
        if (!opened) {
            DisplayService.close(menu);
            editingSchedule = false;
            settingsFor = "";
            if (scheduleDirty) scheduleSettle.restart();
        }
    }
    Timer { id: scheduleSettle; interval: 650; onTriggered: if (menu.scheduleDirty && !nightOperation.running) menu.configureNightlight(menu.nightlight.mode) }
    Timer { id: settle; interval: 80; onTriggered: menu.applyValue(Math.round(slider.value)) }
    // Mirrors the revert timer display-settings.py starts; that timer reverts even if the panel closes.
    Timer {
        id: trialCountdown
        interval: 1000; repeat: true
        onTriggered: {
            menu.trialSeconds -= 1;
            if (menu.trialSeconds <= 0) { menu.pendingMonitor = null; stop(); afterTrial.restart(); }
        }
    }
    Timer { id: afterTrial; interval: 1200; onTriggered: { menu.refreshDisplays(); menu.refreshDisplaySettings(); } }
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
                menu.pendingMonitor = Object.assign({name: menu.requestedMonitor}, result);
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
            else DisplayService.resumeBrightness(menu);
        }
    }
    Process { id: brightnessOsd; command: ["swayosd-client", "--custom-icon", "display-brightness-symbolic", "--custom-progress", "0"] }
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
                menu.refreshDisplays();
                menu.primarySelected(result.primary || "");
                // The main display stays put and the others are placed around it, so positions change meaning.
                menu.refreshDisplaySettings();
            } catch (e) { menu.displayError = menu.displayStatusError; }
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
            DisplayService.resumeNightlight(menu);
        }
    }
    Item {
        id: content
        anchors.fill: parent
        anchors.margins: 0
        focus: true
        Keys.onEscapePressed: event => { if (menu.embedded) event.accepted = false; else menu.dismissPopup(); }
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
                PanelHeading { compact: menu.embedded; visible: !menu.embedded; text: Eitr.I18n.tr("Display"); foreground: menu.foreground; accent: menu.accent; rune: "display" }
                // Only built-in laptop screens get a slider; desktop monitors have their own controls.
                Row {
                    visible: menu.settingsSection !== "nightlight" && menu.state.kind === "backlight"
                    width: parent.width
                    spacing: 10
                    Text { width: 30; height: 30; text: "󰃟"; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: 18 }
                    PanelSlider {
                        id: slider
                        SettingsTarget { objectName: "setting-displays-brightness" }
                        accent: menu.accent
                        foreground: menu.foreground
                        width: parent.width - 100
                        from: 1
                        to: 100
                        stepSize: 1
                        valueText: Math.round(value) + "%"
                        enabled: menu.state.available
                        Binding { target: slider; property: "value"; value: menu.state.value || 1; when: !slider.pressed && !operation.running && !settle.running }
                        onMoved: {
                            if (menu.state.kind === "backlight") menu.applyValue(Math.round(value));
                            else settle.restart();
                        }
                    }
                    Text { width: 50; height: 30; text: Math.round(slider.value) + "%"; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter; color: menu.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize; font.features: PanelStyle.tabularFigures }
                }
                PowerProfileSection { menu: menu }
                PanelDivider { visible: menu.settingsSection === "all" && (menu.state.kind === "backlight" || menu.power.available); width: parent.width; height: 8; foreground: menu.foreground }
                NightLightSection { id: nightlightSection; menu: menu; scheduleSettle: scheduleSettle; nightOperation: nightOperation }
                PanelDivider { visible: menu.settingsSection === "all"; width: parent.width; height: 8; foreground: menu.foreground }
                DisplayListSection { menu: menu; trialOperation: trialOperation; setPrimary: setPrimary }
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
