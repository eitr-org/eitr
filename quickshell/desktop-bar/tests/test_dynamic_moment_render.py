"""Production Dynamic surfaces, queue and content on inert offscreen bars."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bar_frame_source import eager_projection
from layout_render import BAR, EDGES, copy_runtime, render_environment, render, capture_path


TIMER = '''
            property var samples: [
                {kind:"notification", id:1, icon:"󰂚", text:"Screenshot saved", image:"THUMBNAIL"},
                {kind:"volume", icon:"", text:"Volume", level:64},
                {kind:"brightness", icon:"󰃠", text:"Brightness", level:42},
                {kind:"song", icon:"󰝚", text:"Northern Lights · Eitr Ensemble"},
                {kind:"bluetooth", icon:"󰋋", text:"Headphones · Connected · 80%"},
                {kind:"layout", icon:"󰌌", text:"US → BR"},
                {kind:"volume", icon:"󰖁", text:"Mute", level:0},
                {kind:"notification", id:2, critical:true, icon:"󰂚", text:"Critical alert"}
            ]
            property var names: ["notification", "volume", "brightness", "song", "bluetooth", "layout", "mute", "critical"]
            property int sampleIndex: -1
            property real restingWidth: 0
            Timer {
                id: frames; interval: 40; repeat: true
                property int frame: 0
                onTriggered: {
                    const filename = FRAMEPATH + "/notification-" + frame + ".png";
                    bar.grabToImage(result => result.saveToFile(filename));
                    if (++frame === 8) stop();
                }
            }
            Timer {
                id: captureMoment; interval: 500; running: true; repeat: false
                onTriggered: {
                    try {
                        const middle = dynamic.middleIsland;
                        const centre = middle.mapToItem(bar, middle.width / 2, middle.height / 2);
                        const expected = (shell.verticalBar ? bar.height : bar.width) / 2;
                        if (Math.abs((shell.verticalBar ? centre.y : centre.x) - expected) > 0.01)
                            throw new Error("Moment moved clock island off centre");
                        if (bar.sampleIndex === -1) bar.restingWidth = middle.extent;
                        else {
                            const active = dynamic.moments.current;
                            if (!active || active.kind !== bar.samples[bar.sampleIndex].kind) throw new Error("Wrong active moment");
                            const island = active.kind === "song" ? dynamic.mediaIsland : middle;
                            if (!island.momentActive) throw new Error("Moment did not replace normal content");
                            if (!shell.verticalBar && island.extent <= 60) throw new Error("Moment did not grow");
                            if (!shell.verticalBar && bar.sampleIndex === 0 && middle.extent <= bar.restingWidth) throw new Error("Notification did not grow");
                        }
                        const name = bar.sampleIndex < 0 ? "rest" : bar.names[bar.sampleIndex];
                        bar.grabToImage(result => {
                            result.saveToFile(CAPTURE + "/moment-" + name + "-" + THEME + SUFFIX + ".png");
                            if (++bar.sampleIndex === bar.samples.length) {
                                dynamic.trackPointer(true, Qt.point(dynamic.middleIsland.x + dynamic.middleIsland.width / 2,
                                    dynamic.middleIsland.y + dynamic.middleIsland.height / 2));
                                clickPreview.start(); return;
                            }
                            dynamic.moments.queueState = {active:null, queue:[]};
                            dynamic.moments.submit(bar.samples[bar.sampleIndex]);
                            if (bar.sampleIndex === 0 && FRAMES) frames.start();
                            captureMoment.restart();
                        });
                    } catch (error) { console.error(error); Qt.exit(1); }
                }
            }
            TestEvent { id: pointer }
            Timer {
                id: clickPreview; interval: 180
                onTriggered: {
                    try {
                        if (dynamic.moments.current) throw new Error("Hovered moment remained visible");
                        pointer.mouseClick(dynamic.middleIsland, dynamic.middleIsland.width / 2, dynamic.middleIsland.height / 2,
                            Qt.LeftButton, Qt.NoModifier, 1);
                        if (bar.lastKind !== "notifications") throw new Error("Click aimed at notification did not open its centre");
                        dynamic.trackPointer(false, Qt.point(0, 0));
                        dynamic.moments.queueState = {active:null, queue:[]};
                        bar.dynamicLayout = false;
                        dynamic.moments.submit({kind:"volume", level:99});
                        if (dynamic.moments.current || dynamic.moments.queueState.queue.length)
                            throw new Error("Another layout received a moment");
                        console.log("DYNAMIC_MOMENTS_OK"); Qt.quit();
                    } catch (error) { console.error(error); Qt.exit(1); }
                }
            }
        }
    }
}
'''


class DynamicMomentRenderTests(unittest.TestCase):
    def test_moments_all_edges_and_themes(self):
        with tempfile.TemporaryDirectory(prefix='eitr-moments-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            shutil.copytree(BAR / 'assets', folder / 'assets', dirs_exist_ok=True)
            thumbnail = folder / 'thumbnail.svg'
            thumbnail.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="90">'
                                 '<rect width="160" height="90" fill="#70ba9a"/>'
                                 '<rect x="14" y="12" width="132" height="66" rx="6" fill="#18212b"/>'
                                 '<path d="M35 34h90M35 45h65M35 56h80" stroke="#e9eef1" stroke-width="5"/></svg>')
            base = (BAR / 'tests/fixtures/layout/dynamic.qml.in').read_text().split('            property int stage: 0')[0]
            base = base.replace('import QtQuick\n', 'import QtQuick\nimport QtTest\n', 1)
            base = base.replace('function togglePanel(panel)', 'property string lastKind: \"\"\n            function toggleKind(kind) { lastKind = kind; }\n            function togglePanel(panel)')
            source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
            geometry = 'width: host.verticalBar ? bar.thinThickness' + source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
            reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
            base = base.replace('GEOMETRY', geometry.replace('host.', 'shell.')).replace('RESERVED', reserved)
            # No inherited capture activity: rest is the time alone for comparison.
            base = base.replace('property bool shown: true', 'property bool shown: false')
            base = base.replace('width: 24; height: 24', 'width: 24; height: 24; implicitWidth: 24; implicitHeight: 24')
            for edge in (*EDGES, "compact"):
                compact = edge == "compact"
                edge = "top" if compact else edge
                for light in (False, True):
                    theme = 'light' if light else 'dark'
                    capture = capture_path('MOMENT', directory, '')
                    frame_path = capture / 'frames'
                    frame_path.mkdir(exist_ok=True)
                    suffix = '-compact' if compact else '' if edge == 'top' else '-' + edge
                    fixture = base + TIMER
                    if compact:
                        fixture = fixture.replace('1920', '640')
                    replacements = {'FRAMEPATH': json.dumps(str(frame_path)), 'FRAMES': str(edge == 'top' and not light and not compact).lower(),
                                    'THUMBNAIL': thumbnail.as_uri(), 'THEME': json.dumps(theme), 'SUFFIX': json.dumps(suffix),
                                    'CAPTURE': json.dumps(str(capture)), 'EDGE': json.dumps(edge), 'LIGHT': str(light).lower(), 'WEBSITE': 'false'}
                    for token, value in replacements.items():
                        fixture = fixture.replace(token, value)
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    code, output = render(path, render_environment(directory), 15)
                    with self.subTest(edge=edge, theme=theme):
                        self.assertEqual(code, 0, output)
                        self.assertIn('DYNAMIC_MOMENTS_OK', output)
                        for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                            self.assertNotIn(error, output)
                        for name in ('rest', 'notification', 'volume', 'brightness', 'song', 'bluetooth', 'layout', 'mute', 'critical'):
                            self.assertTrue((capture / f'moment-{name}-{theme}{suffix}.png').is_file())
