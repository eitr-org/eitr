"""Render isolated production panels and reject a second opening size motion.

Set EITR_PANEL_REVIEW_RENDERS to a directory outside the checkout.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
bar=Path(__file__).resolve().parents[1]
shots=Path(os.environ['EITR_PANEL_REVIEW_RENDERS'])
shots.mkdir(parents=True, exist_ok=True)
panels={
'AiUsageMenu':('', 'panel.usage = {providers:[{name:"Claude",accounts:[{label:"Preview",plan:"Pro",windows:[{label:"Session",used:42}]}]}]};'),
'SystemMonitorMenu':('', 'panel.error=""; panel.sections = [{title:"CPU",usage:23,name:"Fixture CPU",details:[]}];'),
'WifiMenu':('', ''), 'BluetoothMenu':('', ''), 'BrightnessMenu':('', ''),
'AudioMenu':('', ''), 'KeyboardLayoutMenu':('', 'panel.layouts = [{index:0,label:"English (US)",short:"US"},{index:1,label:"Portuguese (Brazil)",short:"BR"}];'),
'ObsMenu':('', ''), 'RecordingMenu':('controller: mock', 'panel.details={recordingSeconds:42,recordingBytes:3200000};'),
'WeatherMenu':('', 'panel.weatherData={temp:"24°C",condition:"Clear",location:"Preview city",forecast:[]};'),
'CalendarMenu':('', ''),
'RemoteAccessMenu':('service: mock', 'panel.snapshot={tailscale:{status:"Connected",facts:[{label:"Network",value:"Preview"}],actions:[]}};'),
'BatteryMenu':('battery: ({available:true,percent:74,status:"Discharging",health:92,hours:3}); displayControl: mock',''),
'WorkspaceStyleMenu':('currentStyle: "Runes"; selectedForeground: "#18212b"',''),
'NotificationCenter':('service: mock',''),
'PluginPanel':('', ''),
'ControlCenter-style':('service: mock; wifiControl: mock; bluetoothControl: mock; displayControl: mock; keyboardControl: mock; battery: ({}); mediaPlayer: null; idleEnabled: true; idleBusy: false; page: "style"; folds: ({"Bar":true})','panel.page="style"; panel.folds={"Bar":true};'),
'ControlCenter-plugins':('service: mock; wifiControl: mock; bluetoothControl: mock; displayControl: mock; keyboardControl: mock; battery: ({}); mediaPlayer: null; idleEnabled: true; idleBusy: false; page: "plugins"','panel.page="plugins"; Bar.PluginRegistry.installed = [{id:"preview",name:"Preview Plugin",author:"Example",version:"1.0",description:"A review fixture",enabled:true,repository:"https://example.invalid/plugins.git",repositoryPath:"plugins/preview",icon:"",preview:""}];'),
}
template='''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    QtObject {
        id: mock
        property var state: ({kind:"backlight",available:true,percent:65})
        property var power: ({available:false,profiles:[]})
        property bool powerBusy: false
        property string powerError: ""
        property var nightlight: ({enabled:false,mode:"off",start:"20:00",end:"07:00"})
        property string nightlightError: ""
        property var monitors: []
        property string primaryDisplay: ""
        property var layouts: []
        property int activeLayout: 0
        property string error: ""
        property bool busy: false
        property bool controlsReady: true
        property string message: ""
        property var device: null
        property var connected: null
        property var adapter: null
        property bool doNotDisturb: false
        property bool centerOpen: false
        property int count: 0
        property var groups: []
        property var timestamps: ({})
        property string actionError: ""
        property string pendingAction: ""
        property string pendingArgument: ""
        property string controlScript: "missing.py"
        property color foreground: "FG"
        property color background: "BG"
        property color accent: "#509475"
        property var obsState: ({ready:false,recording:true,streaming:false,paused:false})
        function refresh() {}
        function refreshNightlight() {}
        function refreshPower() {}
        function refreshDisplays() {}
        function displayTime(value) { return value || "20:00"; }
    }
    FloatingWindow {
        id: window
        visible: true; implicitWidth: 760; implicitHeight: 1000
        property bool centeredLayout: false
        property bool notchLayout: false
        property var outerGaps: [12,12,12,12]
        property Item stripItem: strip
        property real panelGap: 12
        property var panelFocusWindows: [window]
        Rectangle {
            id: sample; anchors.fill: parent; color: "BG"
            Rectangle { id: strip; width: parent.width; height: 30; color: "BG" }
        }
        Bar.TYPE {
            id: panel; parent: sample; target: strip
            foreground: "FG"; background: "BG"; accent: "#509475"
            EXTRA
        }
        property double started: 0
        property double finalAt: 0
        property double revealAt: 0
        property double revealEnd: 0
        property real previousExtent: 0
        property bool moving: false
        property int motions: 0
        property real finalHeight: 0
        property bool secondMotion: false
        Timer { id: frames; interval: 16; repeat: true; onTriggered: {
            const extent = panel.height * panel.revealProgress;
            const movingNow = Math.abs(extent - window.previousExtent) > 0.001;
            if (movingNow && !window.moving) window.motions++;
            window.moving = movingNow;
            window.previousExtent = extent;
            if (panel.revealProgress > 0 && window.revealAt === 0) window.revealAt=Date.now();
            if (window.revealEnd && panel.height !== window.finalHeight) window.secondMotion=true;
            if (panel.revealProgress === 1 && !window.revealEnd) {
                window.revealEnd=Date.now(); window.finalAt=Date.now()-window.started; window.finalHeight=panel.height;
            }
        } }
        function selectPlugin(item) {
            if (item.hasOwnProperty("selectedPlugin")) { item.selectedPlugin = "preview"; console.log("SELECT_PLUGIN"); }
            for (const child of item.children || []) window.selectPlugin(child);
            if (item.contentItem) window.selectPlugin(item.contentItem);
        }
        Timer { interval: 100; running: true; onTriggered: { Bar.DesktopStyle.reduceMotion=false; DATA window.started=Date.now(); panel.opened=true; frames.start(); } }


        Timer { interval: 900; running: true; onTriggered: {
            frames.stop();
            console.log("PANEL_MEASURE " + JSON.stringify({panel:"NAME",timeToFinalMs:window.finalAt,revealMs:window.revealEnd-window.revealAt,motions:window.motions,secondMotion:window.secondMotion}));
            if (window.motions !== 1 || window.secondMotion) { console.error("MOTION_FAILED"); Qt.exit(1); return; }
            sample.grabToImage(function(result) { result.saveToFile("CAPTURE"); console.log("RENDER_OK"); Qt.quit(); });
        } }
    }
}'''
panels["ControlCenter-plugin-details"] = (panels["ControlCenter-plugins"][0], panels["ControlCenter-plugins"][1] + ' window.selectPlugin(panel);')
panels['MediaMenu'] = ('player: null', '')
panels['AudioMenu-mic'] = ('microphone: true', '')
panels['RemoteAccessMenu-streaming'] = ('service: mock; kind: "streaming"', '')
for page in ['general', 'tools', 'settings']:
 panels['ControlCenter-'+page] = (panels['ControlCenter-style'][0].replace('page: "style"', 'page: "'+page+'"'), 'panel.page="'+page+'";')
panels['PluginPanel'] = ('', 'panel.entry={kind:"panels",plugin:"preview",id:"preview",qml:"FixturePlugin.qml",source:Qt.resolvedUrl("FixturePlugin.qml").toString(),title:"Preview",disabled:false,surface:"panel"};')
for name, (extra, data) in panels.items():
    for theme in ['dark', 'light']:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for source in bar.iterdir():
                if source.suffix in ('.qml', '.js', '.json') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            (folder / 'FixturePlugin.qml').write_text(
                'import QtQuick; Item { required property var api; implicitHeight: 280; '
                'Text { text: "Plugin preview"; color: parent.api.foreground } }')
            background, foreground = ('#18212b', '#e9eef1') if theme == 'dark' else ('#f5f0e7', '#252936')
            capture = shots / (name + '-' + theme + '.png')
            fixture = template.replace('NAME', name).replace('TYPE', name.split('-')[0])
            for key, value in {'EXTRA': extra, 'DATA': data, 'BG': background,
                               'FG': foreground, 'CAPTURE': str(capture)}.items():
                fixture = fixture.replace(key, value)
            (folder / 'fixture.qml').write_text(fixture)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=temporary, HOME=temporary,
                XDG_CONFIG_HOME=temporary, XDG_STATE_HOME=temporary, XDG_DATA_HOME=temporary,
                XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='',
                LC_ALL='C.UTF-8')
            result = subprocess.run(['quickshell', '-p', str(folder / 'fixture.qml')],
                env=environment, text=True, capture_output=True, timeout=5)
            output = result.stdout + result.stderr
            (shots / (name + '-' + theme + '.log')).write_text(output)
            measurement = next((line for line in output.splitlines() if 'PANEL_MEASURE ' in line), '')
            print(name, theme, measurement, flush=True)
            if result.returncode or 'RENDER_OK' not in output or 'MOTION_FAILED' in output:
                raise RuntimeError(name + ' ' + theme + ' failed; see capture log')
