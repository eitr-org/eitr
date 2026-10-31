import ".."
import Eitr as Eitr
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "../PanelStyle.js" as PanelStyle
import "../WorkspaceModel.js" as WorkspaceModel

PanelWindow {
    id: overview
    // With a bar on every display, only the bar of the display in use answers IPC.
    property bool ipcEnabled: true
    required property color foreground
    required property color background
    required property color accent
    property bool opened: false
    property int selectedIndex: 0
    property real revealProgress: opened ? 1 : 0
    property real entranceElapsed: 0
    readonly property var workspaces: WorkspaceModel.occupied(Hyprland.toplevels.values)
    visible: opened
    color: "transparent"
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-overview"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    Behavior on revealProgress { enabled: overview.opened; NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    NumberAnimation {
        id: tileEntrances
        target: overview; property: "entranceElapsed"
        from: 0; to: 755; duration: DesktopStyle.motionDuration(755)
        easing.type: Easing.Linear
    }
    onOpenedChanged: if (opened) {
        entranceElapsed = 0;
        if (DesktopStyle.reduceMotion) entranceElapsed = 755;
        else tileEntrances.restart();
        // The service model is already event-driven; refresh after the entrance.
        refreshAfterEntrance.restart();
        var active = Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : 0;
        selectedIndex = Math.max(0, workspaces.findIndex(w => w.id === active));
        focusDelay.restart();
    } else tileEntrances.stop()
    onWorkspacesChanged: selectedIndex = Math.max(0, Math.min(selectedIndex, workspaces.length - 1))
    Timer {
        id: focusDelay
        interval: 100
        onTriggered: if (overview.opened && contentLoader.item) contentLoader.item.forceActiveFocus()
    }
    Timer { id: refreshAfterEntrance; interval: DesktopStyle.motionDuration(755); onTriggered: if (overview.opened) Hyprland.refreshToplevels() }
    Timer { interval: 1000; repeat: true; running: overview.opened; onTriggered: Hyprland.refreshToplevels() }
    function choose(id) {
        if (id < 1 || id > 10) return;
        opened = false;
        Quickshell.execDetached(WorkspaceModel.focusCommand(id));
    }
    IpcHandler {
        enabled: overview.ipcEnabled
        target: "overview"
        function close(): void { overview.opened = false; }
        function status(): string { return JSON.stringify({opened: overview.opened, workspaces: overview.workspaces.map(w => ({id: w.id, windows: w.windows.length}))}); }
    }
    Loader {
        id: contentLoader
        focus: overview.opened
        onLoaded: if (overview.opened) item.forceActiveFocus()
        anchors.fill: parent
        active: true
        asynchronous: true
        sourceComponent: Component {
            Rectangle {
                color: overview.background
                focus: overview.opened
                Keys.onEscapePressed: overview.opened = false
                Keys.onPressed: event => {
                    if (event.key === Qt.Key_Escape) { overview.opened = false; event.accepted = true; }
                    else if ([Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down].indexOf(event.key) !== -1) {
                        var direction = event.key === Qt.Key_Left ? "left" : event.key === Qt.Key_Right ? "right" : event.key === Qt.Key_Up ? "up" : "down";
                        overview.selectedIndex = WorkspaceModel.selection(overview.selectedIndex, direction, grid.columns, overview.workspaces.length);
                        event.accepted = true;
                    } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                        if (overview.workspaces.length) overview.choose(overview.workspaces[overview.selectedIndex].id);
                        event.accepted = true;
                    } else if (event.key === Qt.Key_Tab) {
                        overview.selectedIndex = (overview.selectedIndex + 1) % Math.max(1, overview.workspaces.length);
                        event.accepted = true;
                    } else if (event.key >= Qt.Key_1 && event.key <= Qt.Key_9) { overview.choose(event.key - Qt.Key_0); event.accepted = true; }
                    else if (event.key === Qt.Key_0) { overview.choose(10); event.accepted = true; }
                }
                MouseArea { anchors.fill: parent; onClicked: overview.opened = false }
                Column {
                    opacity: overview.revealProgress
                    anchors.centerIn: parent
                    width: Math.max(1, Math.min(parent.width - 96, 2160))
                    spacing: 18
                    PanelHeading { width: parent.width; height: 34; text: Eitr.I18n.tr("Overview"); foreground: overview.foreground; accent: overview.accent; rune: "general"; }
                    Grid {
                        id: grid
                        width: parent.width
                        columns: overview.workspaces.length <= 1 ? 1 : overview.workspaces.length <= 4 ? 2 : 3
                        spacing: 18
                        readonly property int rows: Math.max(1, Math.ceil(overview.workspaces.length / columns))
                        readonly property real cellHeight: Math.max(1, Math.min((overview.height - 150 - (rows - 1) * spacing) / rows,
                            (width - (columns - 1) * spacing) / columns / Math.max(1, ...overview.workspaces.map(w => { var f = WorkspaceModel.frame(w); return f.width / f.height; }))))
                        Repeater {
                            model: overview.workspaces
                            Item {
                                id: cell
                                required property var modelData
                                required property int index
                                width: (grid.width - (grid.columns - 1) * grid.spacing) / grid.columns
                                height: grid.cellHeight
                                readonly property var frame: WorkspaceModel.frame(modelData)
                                OverviewTileReveal {
                                    anchors.centerIn: parent
                                    width: Math.min(parent.width, parent.height * parent.frame.width / parent.frame.height)
                                    height: width * parent.frame.height / parent.frame.width
                                    opened: overview.opened
                                    order: cell.index
                                    elapsed: overview.entranceElapsed
                                    WorkspaceOverviewTile {
                                        anchors.fill: parent
                                        workspace: cell.modelData
                                        foreground: overview.foreground; background: overview.background; accent: overview.accent
                                        capturing: overview.visible
                                        selected: overview.selectedIndex === cell.index
                                        current: Hyprland.focusedWorkspace !== null && Hyprland.focusedWorkspace.id === cell.modelData.id
                                        onChosen: id => overview.choose(id)
                                        onHovered: overview.selectedIndex = cell.index
                                    }
                                }
                            }
                        }
                    }
                    Text {
                        visible: overview.workspaces.length === 0
                        width: parent.width; height: 100
                        text: Eitr.I18n.tr("No occupied workspaces")
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        color: overview.foreground; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.bodySize
                    }
                }
            }
        }
    }
}
