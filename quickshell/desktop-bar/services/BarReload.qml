import ".."
import QtQuick
import Quickshell
import Quickshell.Io

Scope {
    id: coordinator
    property string versionPath: ""
    property string packageLockPath: ""
    property bool packageUnlocked: false
    readonly property bool ready: pending && !busy && (!packageLockPath || packageUnlocked)
    property string pluginRevision: ""
    property bool busy: false
    property bool pending: false
    property string loadedVersion: ""

    function request() {
        if (pending) return;
        packageUnlocked = false;
        pending = true;
    }

    property string previousPluginRevision: ""
    onPluginRevisionChanged: {
        if (!pluginRevision) return;
        if (previousPluginRevision && previousPluginRevision !== pluginRevision) request();
        previousPluginRevision = pluginRevision;
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
            if (coordinator.loadedVersion && coordinator.loadedVersion !== version) coordinator.request();
            coordinator.loadedVersion = version;
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

    // Pacman can replace the version stamp before it finishes writing the package,
    // and creates db.lck with mode 0000 so watching the file itself is denied.
    FileView {
        id: packageLock
        path: coordinator.pending ? coordinator.packageLockPath : ""
        watchChanges: false
        printErrors: false
        onLoaded: coordinator.packageUnlocked = false
        onLoadFailed: error => coordinator.packageUnlocked = error === FileViewError.FileNotFound
    }

    FileView {
        path: coordinator.pending && coordinator.packageLockPath
            ? coordinator.packageLockPath.slice(0, coordinator.packageLockPath.lastIndexOf("/")) : ""
        watchChanges: path !== ""
        printErrors: false
        onFileChanged: {
            watchChanges = false;
            reload();
            watchChanges = path !== "";
            coordinator.packageUnlocked = false;
            packageLock.reload();
        }
    }

    // Coalesce requests and let closing animations and queued click handlers settle.
    Timer {
        interval: 750
        running: coordinator.ready
        onTriggered: {
            if (!coordinator.ready) return;
            coordinator.pending = false;
            console.info("Reloading the desktop bar after an update");
            Quickshell.reload(false);
        }
    }
}
