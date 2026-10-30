import QtQuick
import Quickshell
import Quickshell.Io

// Directory watches cover missing files and atomic replacement of parent symlinks.
Scope {
    id: watcher
    required property string path
    property string ancestor: ""
    signal changed()
    function reattach() {
        file.watchChanges = false;
        directory.watchChanges = false;
        file.reload();
        directory.reload();
        file.watchChanges = true;
        directory.watchChanges = true;
        changed();
    }
    FileView {
        id: file
        path: watcher.path
        watchChanges: true; printErrors: false
        onFileChanged: { reload(); watcher.changed(); }
    }
    FileView {
        id: directory
        path: watcher.path.slice(0, watcher.path.lastIndexOf("/"))
        watchChanges: true; printErrors: false
        onFileChanged: reattachDelay.restart()
    }
    FileView {
        path: watcher.ancestor
        watchChanges: watcher.ancestor !== ""; printErrors: false
        onFileChanged: reattachDelay.restart()
    }
    Timer { id: reattachDelay; interval: 20; onTriggered: watcher.reattach() }
}
