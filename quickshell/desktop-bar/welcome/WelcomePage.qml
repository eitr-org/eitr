import ".."
import QtQuick
import Eitr as Eitr

// The first-login welcome at the top of the Handbook's Getting Started chapter:
// hero, tour, setup cards and the welcome's own switches, all from the chapter's
// `welcome` data (see tools/handbook-build.py). The rest of the chapter follows below.
Column {
    id: page
    required property var welcome
    required property color foreground
    required property color background
    required property color accent
    property url artSource: ""
    property string caption: ""
    // Titles of the chapter's remaining sections, read below once `expanded`.
    property var moreTitles: []
    property bool expanded: false
    property bool active: false
    property bool showAtLogin: false
    property bool offerProblemReports: false
    signal setupRequested(string route)
    signal showAtLoginToggled(bool checked)
    signal problemReportsToggled(bool checked)
    function step(delta) { tour.step(delta); }
    width: parent ? parent.width : 0
    spacing: 30
    WelcomeHero {
        title: page.welcome.title || ""
        caption: page.caption
        lead: page.welcome.lead || ""
        artSource: page.artSource
        foreground: page.foreground; background: page.background; accent: page.accent
    }
    WelcomeTour {
        id: tour
        visible: items.length > 0
        section: page.welcome.tour || null
        artSource: page.artSource
        active: page.active
        foreground: page.foreground; background: page.background; accent: page.accent
    }
    WelcomeSetupCards {
        visible: items.length > 0
        section: page.welcome.setup || null
        foreground: page.foreground; accent: page.accent
        onChosen: route => page.setupRequested(route)
    }
    ControlCard {
        surface: SettingsPalette.surface; line: SettingsPalette.line; gold: SettingsInk.gold; carved: true
        title: Eitr.I18n.tr("This welcome"); foreground: page.foreground
        ControlRow {
            text: Eitr.I18n.tr("Show this welcome at the next login")
            description: ""
            foreground: page.foreground
            controlWidth: 48
            PanelSwitch {
                objectName: "handbookShowAtLoginSwitch"
                anchors.right: parent.right
                checked: page.showAtLogin
                foreground: page.foreground
                accent: SettingsPalette.accent
                onToggled: page.showAtLoginToggled(checked)
            }
        }
        ControlRow {
            text: Eitr.I18n.tr("Offer to report problems when something breaks")
            description: Eitr.I18n.tr("Nothing is sent automatically. You read each report first and choose whether to email it or open a GitHub issue; your name, computer name and network addresses are removed.")
            foreground: page.foreground
            controlWidth: 48
            PanelSwitch {
                objectName: "handbookProblemReportsSwitch"
                anchors.right: parent.right
                checked: page.offerProblemReports
                foreground: page.foreground
                accent: SettingsPalette.accent
                onToggled: page.problemReportsToggled(checked)
            }
        }
    }
    WelcomeMore {
        visible: page.moreTitles.length > 0
        titles: page.moreTitles
        expanded: page.expanded
        foreground: page.foreground
        onToggled: page.expanded = !page.expanded
    }
}
