import ".."
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr
import Quickshell
import "../PanelStyle.js" as PanelStyle

Column {
    id: root
    required property var centerRef
    required property bool shown
    required property color foreground
    required property color background
    required property color accent
    property var windowData: null
    property var workspaces: []
    property bool loading: false
    property bool busy: false
    property string errorText: ""
    property string queryId: ""

    readonly property string appId: windowData ? (windowData.class || windowData.initialClass || "") : ""
    readonly property var desktopEntry: {
        if (!appId) return null;
        return DesktopEntries.heuristicLookup(appId)
            || DesktopEntries.applications.values.find(app => app.id === appId || app.startupClass === appId)
            || null;
    }
    readonly property string appName: desktopEntry && desktopEntry.name
        ? desktopEntry.name
        : (appId || (windowData ? windowData.process : "") || Eitr.I18n.tr("Unknown"))
    readonly property string iconSource: desktopEntry && desktopEntry.icon
        ? Quickshell.iconPath(desktopEntry.icon, true) : ""

    function cancelPending() {
        if (queryId) {
            DesktopData.cancelQuery(queryId);
            queryId = "";
        }
    }

    function applyResult(error, data) {
        queryId = "";
        loading = false;
        busy = false;
        if (error) {
            errorText = Eitr.I18n.tr("Could not read window information.");
            return;
        }
        errorText = "";
        if (data && Array.isArray(data.workspaces)) workspaces = data.workspaces;
        windowData = data && data.window ? data.window : null;
    }

    function refresh() {
        cancelPending();
        loading = true;
        errorText = "";
        const address = centerRef && centerRef.lastActiveWindowAddress ? centerRef.lastActiveWindowAddress : "";
        queryId = DesktopData.queryWindow("info", {address: address}, root, function(error, data) {
            root.applyResult(error, data);
        });
    }

    function act(actionName, extraArgs) {
        if (!windowData || !windowData.address || busy) return;
        cancelPending();
        busy = true;
        errorText = "";
        const args = Object.assign({address: windowData.address}, extraArgs || {});
        queryId = DesktopData.queryWindow(actionName, args, root, function(error, data) {
            root.applyResult(error, data);
        });
    }

    onShownChanged: {
        if (shown) refresh();
        else cancelPending();
    }
    Component.onCompleted: if (shown) refresh()
    Component.onDestruction: cancelPending()

    width: parent ? parent.width : 0
    spacing: 12

    Rectangle {
        visible: !!root.windowData
        width: parent.width
        implicitHeight: headerRow.implicitHeight + 20
        radius: DesktopStyle.radius(10)
        color: Qt.alpha(root.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(root.foreground, 0.15)

        RowLayout {
            id: headerRow
            anchors.left: parent.left; anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 12
            spacing: 10
            Image {
                visible: root.iconSource !== ""
                source: root.iconSource
                Layout.preferredWidth: 32; Layout.preferredHeight: 32
                sourceSize: Qt.size(32, 32)
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
            Text {
                visible: root.iconSource === ""
                text: "󰖯"
                color: root.accent
                font.family: DesktopFonts.family
                font.pixelSize: 24
            }
            Column {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    width: parent.width
                    text: root.appName
                    color: root.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.bodySize
                    font.weight: Font.Bold
                    elide: Text.ElideRight
                }
                Text {
                    width: parent.width
                    text: root.windowData ? (root.windowData.title || Eitr.I18n.tr("Untitled")) : ""
                    color: root.foreground
                    opacity: PanelStyle.secondaryTextOpacity
                    font.family: DesktopFonts.family
                    font.pixelSize: PanelStyle.captionSize
                    elide: Text.ElideRight
                }
            }
            PanelButton {
                width: 28; height: 28; icon: true
                text: "󰑐"
                foreground: root.foreground
                available: !root.loading && !root.busy
                Accessible.name: Eitr.I18n.tr("Refresh")
                onClicked: root.refresh()
            }
        }
    }

    Rectangle {
        visible: !!root.windowData
        width: parent.width
        implicitHeight: detailsCol.implicitHeight + 20
        radius: DesktopStyle.radius(10)
        color: Qt.alpha(root.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(root.foreground, 0.15)

        Column {
            id: detailsCol
            x: 12; y: 10
            width: parent.width - 24
            spacing: 6
            Repeater {
                model: root.windowData ? [
                    {label: Eitr.I18n.tr("Title"), value: root.windowData.title || Eitr.I18n.tr("Untitled")},
                    {label: Eitr.I18n.tr("Class"), value: root.windowData.class || root.windowData.initialClass || "—"},
                    {label: Eitr.I18n.tr("Process"), value: (root.windowData.pid > 0 ? String(root.windowData.pid) : "—") + (root.windowData.process ? " (" + root.windowData.process + ")" : "")},
                    {label: Eitr.I18n.tr("Workspace"), value: root.windowData.workspace ? (root.windowData.workspace.name || String(root.windowData.workspace.id)) : "—"},
                    {label: Eitr.I18n.tr("Size"), value: root.windowData.size ? (root.windowData.size[0] + " × " + root.windowData.size[1]) : "—"},
                    {label: Eitr.I18n.tr("Position"), value: root.windowData.at ? (root.windowData.at[0] + ", " + root.windowData.at[1]) : "—"},
                    {label: Eitr.I18n.tr("Floating"), value: root.windowData.floating ? Eitr.I18n.tr("Yes") : Eitr.I18n.tr("No")},
                    {label: Eitr.I18n.tr("Pinned"), value: root.windowData.pinned ? Eitr.I18n.tr("Yes") : Eitr.I18n.tr("No")},
                    {label: Eitr.I18n.tr("Fullscreen"), value: root.windowData.fullscreen ? Eitr.I18n.tr("Yes") : Eitr.I18n.tr("No")}
                ] : []
                RowLayout {
                    required property var modelData
                    width: detailsCol.width
                    spacing: 12
                    Text {
                        Layout.preferredWidth: 110
                        text: modelData.label
                        color: root.foreground
                        opacity: PanelStyle.secondaryTextOpacity
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.value
                        color: root.foreground
                        font.family: DesktopFonts.family
                        font.pixelSize: PanelStyle.captionSize
                        font.features: PanelStyle.tabularFigures
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }

    ChoiceDropdown {
        visible: !!root.windowData && root.workspaces.length > 0
        width: parent.width
        foreground: root.foreground
        background: root.background
        floatingLabel: Eitr.I18n.tr("Move to workspace")
        available: !root.busy && !root.loading
        choices: root.workspaces.map(entry => ({
            value: String(entry.id),
            label: entry.name && entry.name !== String(entry.id)
                ? Eitr.I18n.tr("Workspace %1 (%2)", [String(entry.id), entry.name])
                : Eitr.I18n.tr("Workspace %1", [String(entry.id)])
        }))
        current: root.windowData && root.windowData.workspace ? String(root.windowData.workspace.id) : ""
        onChosen: function(value) { root.act("move", {workspace: Number(value)}); }
    }

    RowLayout {
        visible: !!root.windowData
        width: parent.width
        spacing: 8
        PanelButton {
            Layout.fillWidth: true
            height: 32
            text: root.windowData && root.windowData.floating ? Eitr.I18n.tr("Tile") : Eitr.I18n.tr("Float")
            leadingIcon: "󰖲"
            foreground: root.foreground
            available: !root.busy && !root.loading
            onClicked: root.act("float", {})
        }
        PanelButton {
            Layout.fillWidth: true
            height: 32
            text: root.windowData && root.windowData.pinned ? Eitr.I18n.tr("Unpin") : Eitr.I18n.tr("Pin")
            leadingIcon: "󰐃"
            foreground: root.foreground
            available: !root.busy && !root.loading
            onClicked: root.act("pin", {})
        }
        PanelButton {
            Layout.fillWidth: true
            height: 32
            text: Eitr.I18n.tr("Close")
            leadingIcon: "󰅖"
            foreground: root.foreground
            available: !root.busy && !root.loading
            onClicked: root.act("close", {})
        }
    }

    Rectangle {
        visible: !root.windowData && !root.loading
        width: parent.width
        implicitHeight: emptyCol.implicitHeight + 24
        radius: DesktopStyle.radius(10)
        color: Qt.alpha(root.foreground, 0.04)
        border.width: 1
        border.color: Qt.alpha(root.foreground, 0.15)
        Column {
            id: emptyCol
            x: 12; y: 12
            width: parent.width - 24
            spacing: 8
            Text {
                width: parent.width
                text: Eitr.I18n.tr("No active window")
                color: root.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
                font.weight: Font.Bold
            }
            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                text: Eitr.I18n.tr("Focus a window before opening Control Center to inspect it.")
                color: root.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.captionSize
            }
            PanelButton {
                width: 110; height: 30
                text: Eitr.I18n.tr("Refresh")
                leadingIcon: "󰑐"
                foreground: root.foreground
                onClicked: root.refresh()
            }
        }
    }

    Text {
        visible: root.errorText !== ""
        width: parent.width
        wrapMode: Text.WordWrap
        text: root.errorText
        color: root.foreground
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.captionSize
    }
}
