from qml_source import control_center_source
from qml_test_paths import qml_path
from bar_frame_source import frame_source
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PanelLayeringTests(unittest.TestCase):
    def test_open_and_closing_panels_use_foreground_layer(self):
        shell = frame_source(ROOT)
        self.assertIn("readonly property bool panelOpen: dockPanels.some(panel => panel.visible)", shell)
        self.assertIn("WlrLayershell.layer: panelOpen && !notificationPopups.visible ? WlrLayer.Overlay : WlrLayer.Top", shell)
        self.assertIn("Region { item: notificationCenter.opened ? notificationCenter : null }", shell)
        dock = (ROOT / "components/DockPanel.qml").read_text()
        self.assertIn("visible: opened || revealProgress > 0", dock)

    def test_notification_popups_also_use_overlay(self):
        shell = frame_source(ROOT)
        self.assertIn("id: notificationPopups", shell)
        self.assertIn("panelOpen && !notificationPopups.visible", shell)
        self.assertIn("WlrLayershell.layer: WlrLayer.Overlay",
                      (ROOT / "notifications/NotificationPopups.qml").read_text())

    def test_panel_focus_grabs_allow_notification_window(self):
        shell = frame_source(ROOT)
        self.assertIn("notificationPopups.visible ? [bar, notificationPopups] : [bar]", shell)
        self.assertIn("hostWindow.panelFocusWindows || [hostWindow]", (ROOT / "components/DockPanel.qml").read_text())
        self.assertIn("windows: popup.focusWindows", (ROOT / "components/ThemedPopup.qml").read_text())

    def test_bar_panels_share_themed_popup_grab_and_focus(self):
        themed = (ROOT / "components/ThemedPopup.qml").read_text()
        self.assertIn("popup.keyTarget.forceActiveFocus();", themed)
        self.assertIn("Keys.onEscapePressed: if (!popup.escapeHandler || !popup.escapeHandler()) popup.opened = false", themed)
        center = control_center_source(ROOT)
        self.assertIn('escapeHandler: () => center.page === "plugins" ? pluginManager.back() : plugins.back()', center)
        for filename in ("AudioMenu.qml", "SystemMonitorMenu.qml", "WorkspaceStyleMenu.qml"):
            with self.subTest(filename=filename):
                source = (ROOT / qml_path(filename)).read_text()
                self.assertIn("\nThemedPopup {", source)
                self.assertNotIn("HyprlandFocusGrab", source)
                self.assertNotIn("BarGeometry.js", source)
