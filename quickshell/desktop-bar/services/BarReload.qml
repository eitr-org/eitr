import ".."
import QtQuick
import Quickshell
import Quickshell.Io

Scope {
    id: coordinator
    property string versionPath: ""
    property string packageLockPath: ""
    property string updateMarkerPath: {
        const runtime = Quickshell.env("XDG_RUNTIME_DIR");
        return runtime ? runtime + "/eitr/system-update.pid" : "";
    }
    property bool updateUnlocked: false
    readonly property bool ready: pending && !busy
    property string pluginRevision: ""
    property bool busy: false
    property bool pending: false
    property string loadedVersion: ""
    property string installedVersion: ""
    property string loadedPluginRevision: ""
    property string refreshedVersion: ""
    property int requestSerial: 0
    readonly property bool versionChanged: loadedVersion !== installedVersion
    signal refreshPlugins()

    function request() {
        const changed = loadedVersion !== installedVersion
            || (pluginRevision !== "" && loadedPluginRevision !== pluginRevision);
        if (!pending && changed) updateUnlocked = false;
        pending = changed;
        if (changed) {
            requestSerial++;
            if (ready) quietPeriod.restart();
        }
    }

    onPluginRevisionChanged: {
        if (!pluginRevision) return;
        if (!loadedPluginRevision) loadedPluginRevision = pluginRevision;
        request();
    }

    FileView {
        id: versionFile
        path: coordinator.versionPath
        watchChanges: path !== ""
        printErrors: false
        onFileChanged: {
            watchChanges = false;
            reload();
            watchChanges = path !== "";
        }
        onLoaded: {
            const version = text().trim();
            if (!version) return;
            if (coordinator.installedVersion === version) return;
            if (!coordinator.loadedVersion) coordinator.loadedVersion = version;
            coordinator.installedVersion = version;
            coordinator.request();
        }
    }

    FileView {
        path: coordinator.versionPath ? coordinator.versionPath.slice(0, coordinator.versionPath.lastIndexOf("/")) : ""
        watchChanges: path !== ""
        printErrors: false
        onFileChanged: {
            watchChanges = false;
            reload();
            watchChanges = path !== "";
            versionFile.watchChanges = false;
            versionFile.reload();
            versionFile.watchChanges = coordinator.versionPath !== "";
        }
    }

    function reloadIfReady() {
        if (!ready) return;
        if (versionChanged && refreshedVersion !== installedVersion) {
            refreshedVersion = installedVersion;
            refreshPlugins();
            return;
        }
        pending = false;
        console.info("Reloading the desktop bar after an update");
        Quickshell.reload(false);
    }

    Process {
        id: updateProbe
        property int serial: 0
        // Pacman creates db.lck with mode 0000, so check its existence.
        command: ["sh", "-c",
            "if [ -e \"$1\" ]; then exit 0; fi\n"
                + "IFS= read -r owner 2>/dev/null < \"$2\" || exit 1\n"
                + "case \"$owner\" in \"\"|0*|*[!0-9]*) exit 1;; esac\n"
                + "kill -0 \"$owner\" 2>/dev/null || exit 1",
            "update-locks", coordinator.packageLockPath, coordinator.updateMarkerPath]
        onExited: code => {
            if (!coordinator.ready || serial !== coordinator.requestSerial) return;
            if (code === 1 && coordinator.updateUnlocked) coordinator.reloadIfReady();
            else {
                coordinator.updateUnlocked = code === 1;
                quietPeriod.restart();
            }
        }
    }

    // Give terminal upgrades time to settle after pacman's lock clears.
    Timer {
        id: quietPeriod
        interval: coordinator.updateUnlocked && coordinator.versionChanged
            && coordinator.refreshedVersion !== coordinator.installedVersion ? 5000 : 750
        running: coordinator.ready
        repeat: true
        onTriggered: {
            if (!coordinator.ready) return;
            if (!updateProbe.running) {
                updateProbe.serial = coordinator.requestSerial;
                updateProbe.running = true;
            }
        }
    }
}
