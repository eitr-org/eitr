import ".."
pragma ComponentBehavior: Bound
import QtQuick
import Eitr as Eitr
import QtQuick.Layouts

Column {
    id: section
    required property var centerRef
    visible: section.centerRef.page === "tools"; width: parent.width; spacing: 12
    // The same timer as Drop's dashboard; the clock's timer ring opens this fold.
    ControlCenterFold { centerRef: section.centerRef;
    title: section.centerRef.timerFold
    FocusTimerControls {
        width: parent.width; ringSize: 112
        foreground: section.centerRef.foreground; accent: section.centerRef.accent; background: section.centerRef.background
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Screenshots")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Selection"); glyph: "󰄀"; onClicked: section.centerRef.menuAction("screenshot", "Selection") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Full Screen"); glyph: "󰹑"; onClicked: section.centerRef.menuAction("screenshot", "Full Screen") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Window"); glyph: "󰖯"; onClicked: section.centerRef.menuAction("screenshot", "Window") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Selection: Copy"); glyph: "󰆏"; onClicked: section.centerRef.menuAction("screenshot", "Selection: Copy") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Recording")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("OBS Controls"); glyph: "󰻂"; onClicked: section.centerRef.panelRequested("obs") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Record"); glyph: "󰑊"; onClicked: section.centerRef.menuAction("screenrecord", "Record") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Record + Audio"); glyph: "󰕾"; onClicked: section.centerRef.menuAction("screenrecord", "Record + Audio") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Stop Recording"); glyph: "󰓛"; onClicked: section.centerRef.menuAction("screenrecord", "Stop Recording") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Text & Color")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("OCR Text"); glyph: "󰴑"; onClicked: section.centerRef.menuAction("tools", "OCR Text") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("QR Code"); glyph: "󰐲"; onClicked: section.centerRef.menuAction("tools", "QR Code") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Color Picker"); glyph: "󰈊"; onClicked: section.centerRef.menuAction("tools", "Color") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Transcode"); glyph: "󰈫"; onClicked: section.centerRef.menuAction("tools", "Transcode") }
    }
    }
    ControlCenterFold { centerRef: section.centerRef;
    title: Eitr.I18n.tr("Reminders & Sharing")
    GridLayout { width: parent.width; columns: 2; columnSpacing: 8; rowSpacing: 8
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("New Reminder"); glyph: "󰀠"; onClicked: section.centerRef.menuAction("reminders", "New Reminder") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Upcoming"); glyph: "󰃰"; onClicked: section.centerRef.menuAction("reminders", "Upcoming Reminders") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Share Clipboard"); glyph: "󰅌"; onClicked: section.centerRef.menuAction("share", "Clipboard") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Share File"); glyph: "󰈔"; onClicked: section.centerRef.menuAction("share", "File") }
        ControlCenterGridAction { centerRef: section.centerRef; title: Eitr.I18n.tr("Share Folder"); glyph: "󰉋"; onClicked: section.centerRef.menuAction("share", "Folder") }
    }
    }
}
