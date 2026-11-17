"""Isolated runtime for lazy-window tests and construction measurements."""
from pathlib import Path
import shutil

from layout_render import copy_runtime, render_environment

BAR = Path(__file__).resolve().parents[1]


def prepare_runtime(folder):
    copy_runtime(folder)
    shutil.copytree(BAR / 'handbook', folder / 'handbook', dirs_exist_ok=True)
    (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var topics: ({})
 property var client: ({detachAction: function(id) {}})
 function observe(topic, owner, interval) { return ""; }
 function release(token) {}
 function releaseOwner(owner) {}
 function refresh(topic) {}
 function queryCatalog(name, args, owner, callback) { callback("", {}); }
}
''')
    environment = render_environment(folder)
    environment['EITR_CODE_ROOT'] = str(folder)
    environment.pop('WAYLAND_DISPLAY', None)
    return environment


def expose_ipc(folder, relative, aliases):
    """Call the production IpcHandler bodies when sandboxing forbids Unix sockets."""
    path = folder / relative
    source = path.read_text()
    for index, alias in enumerate(aliases):
        marker = '    IpcHandler {'
        start = source.index(marker) if index == 0 else source.index(marker, start + len(marker) + 1)
        source = source[:start] + source[start:].replace(marker, marker + '\n        id: ' + alias[0].lower() + alias[1:], 1)
    position = source.index('\n    id:')
    source = source[:position] + ''.join('\n    property alias test' + alias + ': ' + alias[0].lower() + alias[1:] for alias in aliases) + source[position:]
    path.write_text(source)


WINDOW_FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 id: host
 property color fg: "#cdd6f4"
 property color activeBg: "#759456"
 signal handbookOpened()
 function targetScreens() { return Quickshell.screens; }
 function barBackground() { return "#181824"; }
 function showSettings(page) { settings.show(page); }
 function showClock(page) { clock.show(page); }
 Bar.SettingsWindow { id: settings; networkService: null; notifications: null; live: false; foreground: host.fg; background: host.barBackground(); accent: host.activeBg }
 Bar.Catalog { id: catalog; foreground: host.fg; background: host.barBackground(); accent: host.activeBg }
 Bar.ClockWindow { id: clock; live: false; foreground: host.fg; background: host.barBackground(); accent: host.activeBg }
 Bar.WelcomeSession { id: welcome; host: host }
 Bar.BeautifyWindow { id: beautify; foreground: host.fg; background: host.barBackground(); accent: host.activeBg }
 TEST_BODY
}
'''


def dynamic_switch_fixture():
    """Real Dynamic state must return borrowed bar items before Loader teardown."""
    from bar_frame_source import eager_projection
    from layout_render import layout_fixture
    source=eager_projection((BAR/'bar/BarWindow.qml').read_text())
    geometry=source.split('        width: host.verticalBar ? bar.thinThickness',1)[1].split('        BarTabs {',1)[0]
    geometry=('width: host.verticalBar ? bar.thinThickness'+geometry).replace('host.','shell.')
    reserved=source.split('readonly property real reservedThickness: ',1)[1].split('\n',1)[0]
    fixture=layout_fixture('dynamic').split('            Bar.DockPanel {',1)[0]
    fixture=fixture.replace('GEOMETRY',geometry).replace('RESERVED',reserved).replace('EDGE','"top"').replace('LIGHT','false').replace('WEBSITE','false')
    fixture=fixture.replace('property alias dynamicSurfaces: dynamic','property var dynamicSurfaces: dynamicLoader.item')
    fixture=fixture.replace('dynamic.middleIsland.expanded','(dynamicLoader.item && dynamicLoader.item.middleIsland.expanded)').replace('dynamic.weatherReveal','(dynamicLoader.item ? dynamicLoader.item.weatherReveal : 0)')
    fixture=fixture.replace('Bar.BarDynamic { id: dynamic; host: shell; barHost: bar }','Loader { id: dynamicLoader; anchors.fill: parent; z: 1; active: false; sourceComponent: Bar.BarDynamic { host: shell; barHost: bar } }')
    fixture+='''
                Timer {
                    interval: 50; running: true; repeat: true
                    property int step: 0
                    property var samples: []
                    property var initialLeft: null
                    onTriggered: {
                        if (step === 0) initialLeft = left.parent;
                        if (step % 2 === 0) {
                            const start = Date.now();
                            dynamicLoader.active = true;
                            samples.push(Date.now() - start);
                            if (!dynamicLoader.item) throw new Error("layout did not load synchronously");
                        } else {
                            dynamicLoader.active = false;
                            if (!left || left.parent !== initialLeft) throw new Error("layout teardown lost left group");
                            if (!clock || clock.parent !== center) throw new Error("layout teardown lost clock");
                        }
                        if (++step === 20) { console.log("LAYOUT_SWITCH_MS", JSON.stringify(samples)); Qt.quit(); }
                    }
                }
            }
        }
    }
    '''
    return fixture
