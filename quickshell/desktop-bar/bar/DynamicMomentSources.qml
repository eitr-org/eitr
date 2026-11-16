import ".."
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Bluetooth
import Quickshell.Services.Pipewire
import Eitr as Eitr
import "../NotificationLogic.js" as NotificationLogic
import "../components/BluetoothDevices.js" as BluetoothDevices

Item {
    id: sources
    required property var host
    required property var barHost
    required property var owner
    property bool ready: false
    Component.onCompleted: Qt.callLater(() => { seenTrack = track; ready = true; syncPopups(); })
    readonly property var notifications: barHost.notificationsRef || null
    readonly property var popups: notifications ? notifications.popups : []
    readonly property var popupVersions: popups.map(notification => JSON.stringify([notification.id,
        notifications.timestamps ? notifications.timestamps[notification.id] : 0,
        notification.summary, notification.urgency, NotificationLogic.imageSource(notification)]))
    property var seenPopups: []
    onPopupVersionsChanged: syncPopups()
    function syncPopups() {
        const ids = popups.map(notification => notification.id);
        if (ready && notifications && !notifications.doNotDisturb) {
            popups.forEach((notification, index) => {
                if (seenPopups.indexOf(popupVersions[index]) !== -1) return;
                owner.submit({kind: "notification", id: notification.id, critical: notification.urgency === 2,
                    text: NotificationLogic.presentation(notification).summary,
                    image: NotificationLogic.imageSource(notification) || NotificationLogic.appIconSource(notification,
                        "", "", name => Quickshell.iconPath(name, true)), icon: "󰂚"});
            });
        }
        seenPopups = popupVersions.slice();
        owner.retainNotifications(ids);
    }
    Connections {
        target: sources.notifications
        function onDoNotDisturbChanged() {
            if (sources.notifications.doNotDisturb) sources.owner.retainNotifications([]);
        }
    }
    readonly property var sink: Pipewire.defaultAudioSink
    PwObjectTracker { objects: [sources.sink] }
    property var audio: sink && sink.ready ? sink.audio : null
    readonly property string audioState: audio ? Math.round(audio.volume * 100) + ":" + audio.muted : ""
    property string seenAudio: ""
    onAudioStateChanged: {
        if (ready && audioState && seenAudio && audioState !== seenAudio)
            owner.submit({kind: "volume", level: Math.round(audio.volume * 100), icon: audio.muted ? "󰖁" : "",
                text: audio.muted ? Eitr.I18n.tr("Mute") : Eitr.I18n.tr("Volume")});
        seenAudio = audioState;
    }
    onSinkChanged: seenAudio = ""
    // The key helper publishes a level event (brightnessctl supplies the brightness). File events replace polling and
    // preserve the display domain's demand-driven lifecycle.
    readonly property string brightnessPath: Quickshell.env("XDG_RUNTIME_DIR") + "/eitr-level-moment.json"
    FileView {
        id: brightness
        path: sources.brightnessPath
        watchChanges: true; printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                const data = JSON.parse(text());
                if (!sources.ready || Date.now() - data.at >= 1500 || data.at === sources.seenBrightness) return;
                if (data.kind === "volume" && sources.audio)
                    sources.owner.submit({kind: "volume", level: Math.round(sources.audio.volume * 100),
                        icon: sources.audio.muted ? "󰖁" : "", text: Eitr.I18n.tr("Volume")});
                else if (data.kind === "brightness" && Number.isFinite(data.level) && data.level >= 0 && data.level <= 100)
                    sources.owner.submit({kind: "brightness", level: data.level, icon: "󰃠", text: Eitr.I18n.tr("Brightness")});
                sources.seenBrightness = data.at;
            } catch (error) {}
        }
    }
    property real seenBrightness: 0
    PreferenceWatch { path: sources.brightnessPath; onChanged: brightness.reload() }
    property var adapter: Bluetooth.defaultAdapter
    readonly property var devices: adapter && adapter.devices ? adapter.devices.values : []
    Instantiator {
        model: sources.devices
        delegate: QtObject {
            required property var modelData
            property bool initialized: false
            property bool connected: modelData.connected
            Component.onCompleted: initialized = true
            onConnectedChanged: {
                if (!initialized || !sources.ready) return;
                const battery = BluetoothDevices.batteryText(modelData);
                sources.owner.submit({kind: "bluetooth", icon: BluetoothDevices.glyph(modelData),
                    text: [modelData.name || modelData.address,
                        connected ? Eitr.I18n.tr("Connected") : Eitr.I18n.tr("Disconnected"), battery].filter(Boolean).join(" · ")});
            }
        }
    }
    readonly property var keyboard: barHost.keyboardMenu || null
    readonly property string layout: keyboard ? keyboard.activeCode : ""
    property string seenLayout: ""
    onLayoutChanged: {
        if (ready && seenLayout && layout && layout !== seenLayout && keyboard.layouts.length > 1)
            owner.submit({kind: "layout", icon: "󰌌", text: seenLayout.toUpperCase() + " → " + layout.toUpperCase()});
        seenLayout = layout;
    }
    readonly property var player: barHost.mediaStrip ? barHost.mediaStrip.player : null
    readonly property string track: player ? [player.trackTitle, player.trackArtist].filter(Boolean).join(" · ") : ""
    property string seenTrack: ""
    onTrackChanged: songDelay.restart()
    // Metadata fields arrive separately. Coalesce them without treating pause as a track change.
    Timer {
        id: songDelay; interval: 80
        onTriggered: {
            if (sources.ready && sources.track && sources.track !== sources.seenTrack)
                sources.owner.submit({kind: "song", icon: "󰝚", text: sources.track});
            if (sources.track) sources.seenTrack = sources.track;
        }
    }
}
