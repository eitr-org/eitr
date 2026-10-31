const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = ['BarWindow', 'BarHorizontalCenter', 'BarVerticalCenter', 'BarHorizontalStatus', 'BarVerticalStatus']
    .map(name => fs.readFileSync(`${__dirname}/../${name}.qml`, 'utf8').replace(/^/gm, name === 'BarWindow' ? '            ' : '')).join('\n').replace(/\bhost\b/g, 'shell');
const expression = source.match(/readonly property bool expanded: ([^\n]+)/)[1];
const context = {centeredLayout: true, shell: {barPinned: false, barPointerHeld: false},
    hoverExpanded: false, panelOpen: false, pendingPanel: null};
const expanded = () => vm.runInNewContext(expression, context);
assert.equal(expanded(), false);
for (const reason of ['hoverExpanded', 'panelOpen', 'pendingPanel']) {
    context[reason] = reason === 'pendingPanel' ? {} : true;
    assert.equal(expanded(), true);
    context[reason] = reason === 'pendingPanel' ? null : false;
}
for (const reason of ['barPinned', 'barPointerHeld']) {
    context.shell[reason] = true;
    assert.equal(expanded(), true);
    context.shell[reason] = false;
}
context.centeredLayout = false;
assert.equal(expanded(), true);
assert.ok(source.includes('interval: 350'));
assert.ok(source.includes('anchors.right: barHost.centeredLayout ? barPin.left : barCapture.left'));
// The recording/dictation indicator sits between the pin (or media) and the clock.
assert.ok(/id: barCapture\s+anchors.right: centerInfo.left/.test(source));
assert.ok(/id: barPin\s+visible: barHost.centeredLayout && barHost.expanded\s+anchors.right: barCapture.left/.test(source));
assert.ok(source.includes('id: barPin'));
assert.equal((source.match(/BarSection \{/g) || []).length, 2);
const corners = fs.readFileSync(`${__dirname}/../BarSection.qml`, 'utf8');
for (const edge of ['top', 'bottom', 'left', 'right']) {
    const radius = corner => vm.runInNewContext(corners.match(new RegExp(`${corner}: ([^\\n]+)`))[1], {edge, radius: 6});
    assert.equal(radius('topLeftRadius'), edge === 'top' || edge === 'left' ? 0 : 6);
    assert.equal(radius('topRightRadius'), edge === 'top' || edge === 'right' ? 0 : 6);
    assert.equal(radius('bottomLeftRadius'), edge === 'bottom' || edge === 'left' ? 0 : 6);
    assert.equal(radius('bottomRightRadius'), edge === 'bottom' || edge === 'right' ? 0 : 6);
}
console.log('Centered bar hover, pin, panel and drag checks passed');
// Independent animated sides keep the clock on the screen axis throughout reveal.
for (const edge of ['top', 'bottom', 'left', 'right']) {
    for (const progress of [0, 0.25, 0.75, 1]) {
        const bar = {width: 1920, height: 1080, centeredLayout: true,
            centerExtent: 80, leadingReveal: 380 * progress, trailingReveal: 210 * progress};
        const shell = {verticalBar: edge === 'left' || edge === 'right', barEdge: edge, barHeight: 32};
        const contents = source.split('id: barContents\n')[1];
        const evaluate = name => vm.runInNewContext(contents.match(new RegExp(`^                    ${name}: ([^\\n]+)`, 'm'))[1], {bar, shell});
        const length = evaluate(shell.verticalBar ? 'height' : 'width');
        const start = evaluate(shell.verticalBar ? 'y' : 'x');
        const axis = (shell.verticalBar ? bar.height : bar.width) / 2;
        assert.equal(length, 80 + 590 * progress);
        assert.equal(start + length / 2 + (bar.leadingReveal - bar.trailingReveal) / 2, axis);
        assert.equal(start, axis - 40 - bar.leadingReveal);
        assert.equal(start + length, axis + 40 + bar.trailingReveal);
    }
}
assert.ok(!source.includes('sideExtent'));
// Centered layout panels center on the screen axis, independently of the strip midpoint.
const panels = fs.readFileSync(`${__dirname}/../DockPanel.qml`, 'utf8');
assert.ok(panels.includes('centeredPlacement ? (parent.width - width) / 2'));
assert.ok(panels.includes('centeredPlacement ? (parent.height - height) / 2'));
assert.ok(panels.includes('strip.x + strip.width + attachmentGap'));
assert.ok(panels.includes('strip.y + strip.height + attachmentGap'));
assert.ok(source.includes('anchors.horizontalCenterOffset: barHost.centeredLayout ? (barHost.leadingReveal - barHost.trailingReveal) / 2 : 0'));
assert.ok(source.includes('anchors.verticalCenterOffset: barHost.centeredLayout ? (barHost.leadingReveal - barHost.trailingReveal) / 2 : 0'));
// Measure the packed strip using the production extent and margin expressions.
// Check the production anchors as well as the extent arithmetic: a changed margin
// must not leave the fixture passing with an unrelated, idealised row.
function itemProperty(id, property) {
    const item = source.split(`id: ${id}\n`)[1];
    return item.match(new RegExp(`^ +${property.replaceAll('.', '\\.')}:+ ([^\\n]+)`, 'm'))[1];
}
const centeredContext = {bar: {centeredLayout: true, itemGap: 4, endPadding: 12}, shown: true};
centeredContext.barHost = centeredContext.bar;
for (const [id, property] of [['barPin', 'anchors.rightMargin'], ['barCapture', 'anchors.rightMargin'],
    ['mediaStrip', 'anchors.rightMargin'], ['verticalPin', 'anchors.bottomMargin'],
    ['verticalCapture', 'anchors.bottomMargin'], ['verticalMedia', 'anchors.bottomMargin'],
    ['verticalMedia', 'spacing'], ['mediaStrip', 'itemSpacing'], ['mediaStrip', 'indicatorSpacing']]) {
    assert.equal(vm.runInNewContext(itemProperty(id, property), centeredContext), 4, `${id}.${property}`);
}
assert.equal(vm.runInNewContext(itemProperty('notificationIcon', 'anchors.rightMargin'), centeredContext), 12);
assert.equal(vm.runInNewContext(itemProperty('verticalStart', 'y'), centeredContext), 12);
assert.equal(vm.runInNewContext(itemProperty('verticalEnd', 'anchors.bottomMargin'), centeredContext), 12);
const os = require('node:os');
const path = require('node:path');
const childProcess = require('node:child_process');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'eitr-centered-'));
// The offscreen render needs Quickshell; without it (CI) only the geometry above is checked.
const hasQuickshell = childProcess.spawnSync('quickshell', ['--version']).status === 0;
function propertyExpression(name) {
    return source.match(new RegExp(`readonly property real ${name}: ([\\s\\S]*?)\\n                (?:readonly )?property`))[1];
}
try {
    for (const edge of ['top', 'bottom', 'left', 'right']) {
        for (const withMedia of [false, true]) {
            for (const shown of [false, true]) {
                for (const workspaceCount of [5, 10]) {
                    const verticalBar = edge === 'left' || edge === 'right';
                    const gap = 4, padding = verticalBar ? 8 : 12;
                    const shell = {verticalBar, workspaceItemSpacing: gap};
                    const slots = count => Array(count).fill(24);
                    const span = sizes => sizes.reduce((sum, size) => sum + size, 0) + Math.max(0, sizes.length - 1) * gap;
                    const workspaceSizes = slots(workspaceCount + 2), hardwareSizes = slots(3);
                    const mediaSizes = withMedia ? (verticalBar ? slots(4) : [18, 18, 18, 14]) : [];
                    const leftSizes = [...workspaceSizes, ...hardwareSizes, ...mediaSizes, 24, ...(shown ? [verticalBar ? 24 : 22] : [])];
                    const clockSize = verticalBar ? 40 : 156;
                    const rightSizes = [verticalBar ? 24 : 50, ...slots(9), 24];
                    const centerExtent = verticalBar ? 56 : clockSize + 24;
                    const context = {shell, endPadding: padding, centerPadding: (centerExtent - clockSize) / 2, itemGap: gap,
                        leftGroup: {workspaces: {width: span(workspaceSizes)}, hardwareStatus: {width: span(hardwareSizes)}},
                        mediaStrip: {player: withMedia ? {} : null, visible: withMedia, width: span(mediaSizes)},
                        barPin: {width: 24}, barCapture: {width: shown ? 22 : 0, shown},
                        barWeather: {width: 50}, rightSide: {width: span(slots(9))}, notificationIcon: {width: 24},
                        verticalStart: {height: span([...workspaceSizes, ...hardwareSizes])}, verticalEnd: {height: span([...slots(9), 24])},
                        verticalPin: {height: 24}, verticalCapture: {shown, height: shown ? 24 : 0},
                        verticalMedia: {height: span(mediaSizes)}, verticalWeatherIcon: {height: 24}};
                    const leading = vm.runInNewContext(propertyExpression('leadingExtent'), context);
                    const trailing = vm.runInNewContext(propertyExpression('trailingExtent'), context);
                    const axis = 1000;
                    const start = axis - centerExtent / 2 - leading;
                    const end = axis + centerExtent / 2 + trailing;
                    let cursor = start + padding;
                    const items = [];
                    for (const size of [...leftSizes, clockSize, ...rightSizes]) {
                        items.push({start: cursor, size});
                        cursor += size + gap;
                    }
                    const clock = items[leftSizes.length];
                    assert.equal(clock.start + clock.size / 2, axis, `${edge}: clock centre`);
                    for (let index = 1; index < items.length; index++) {
                        assert.equal(items[index].start - items[index - 1].start - items[index - 1].size, gap);
                    }
                    assert.equal(items[0].start - start, padding);
                    assert.equal(end - (cursor - gap), padding);
                    if (!['top', 'left'].includes(edge) || shown || workspaceCount !== 5) continue;
                    // Offscreen rectangles show the measured slots, without connecting to desktop services.
                    const capture = path.join(process.env.EITR_CENTERED_RENDERS || directory, `${edge}-${withMedia}.png`);
                    const axisStart = verticalBar ? 'top' : 'left';
                    const axisEnd = verticalBar ? 'bottom' : 'right';
                    const axisPosition = verticalBar ? 'y' : 'x';
                    const axisSize = verticalBar ? 'height' : 'width';
                    function rectangle(index, placement) {
                        const item = items[index];
                        return `Rectangle { id: slot${index}; ${verticalBar ? 'x: 12; width: 24; height' : 'y: 12; height: 24; width'}: ${item.size}; ${placement}; radius: 3; color: "${index === leftSizes.length ? '#e8bc68' : '#84a6bd'}" }`;
                    }
                    const clockIndex = leftSizes.length;
                    const hardwareEndIndex = workspaceSizes.length + hardwareSizes.length - 1;
                    const rectangles = items.map((item, index) => {
                        if (index === clockIndex) return rectangle(index, `${axisPosition}: ${axis - start - clockSize / 2}`);
                        if (index === 0) return rectangle(index, `${axisPosition}: ${padding}`);
                        if (index <= hardwareEndIndex) return rectangle(index, `anchors.${axisStart}: slot${index - 1}.${axisEnd}; anchors.${axisStart}Margin: ${gap}`);
                        if (index < clockIndex) return rectangle(index, `anchors.${axisEnd}: slot${index + 1}.${axisStart}; anchors.${axisEnd}Margin: ${gap}`);
                        if (index === clockIndex + 1) return rectangle(index, `anchors.${axisStart}: slot${clockIndex}.${axisEnd}; anchors.${axisStart}Margin: ${gap}`);
                        if (index === items.length - 1) return rectangle(index, `anchors.${axisEnd}: parent.${axisEnd}; anchors.${axisEnd}Margin: ${padding}`);
                        return rectangle(index, `anchors.${axisEnd}: slot${index + 1}.${axisStart}; anchors.${axisEnd}Margin: ${gap}`);
                    }).join('\n');
                    const measuredItems = items.map((item, index) => `slot${index}`).join(',');
                    const fixture = `import QtQuick
import Quickshell
ShellRoot {
 FloatingWindow {
  visible: true; implicitWidth: ${verticalBar ? 48 : end - start}; implicitHeight: ${verticalBar ? end - start : 48}
  Item { id: sample; anchors.fill: parent
   Rectangle { anchors.fill: parent; color: "#202430"; radius: 6 }
   ${rectangles}
  }
  Timer { interval: 100; running: true; onTriggered: {
   var slots = [${measuredItems}];
   function check(condition, label) { if (!condition) throw new Error(label); }
   for (var index = 1; index < slots.length; index++)
    check(Math.abs(slots[index].${axisPosition} - slots[index - 1].${axisPosition} - slots[index - 1].${axisSize} - ${gap}) < 0.01, "uneven gap " + index);
   check(slots[0].${axisPosition} === ${padding}, "leading padding");
   check(Math.abs(sample.${axisSize} - slots[slots.length - 1].${axisPosition} - slots[slots.length - 1].${axisSize} - ${padding}) < 0.01, "trailing padding");
   check(Math.abs(slot${clockIndex}.${axisPosition} + slot${clockIndex}.${axisSize} / 2 + ${start} - ${axis}) < 0.01, "clock centre");
   console.log("CENTERED_MEASURED");
   sample.grabToImage(function(result) { result.saveToFile(${JSON.stringify(capture)}); Qt.quit(); });
  } }
 }
}`;
                    if (!hasQuickshell) continue;
                    const fixturePath = path.join(directory, 'fixture.qml');
                    fs.writeFileSync(fixturePath, fixture);
                    const result = childProcess.spawnSync('quickshell', ['-p', fixturePath], {encoding: 'utf8', timeout: 10000,
                        env: {...process.env, QT_QPA_PLATFORM: 'offscreen', QT_QUICK_BACKEND: 'software', HOME: directory,
                            XDG_CONFIG_HOME: directory, XDG_CACHE_HOME: directory, XDG_STATE_HOME: directory,
                            XDG_RUNTIME_DIR: directory, DBUS_SESSION_BUS_ADDRESS: 'unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE: ''}});
                    assert.equal(result.status, 0, result.stdout + result.stderr);
                    assert.ok(fs.existsSync(capture), result.stdout + result.stderr);
                    assert.ok(result.stdout.includes('CENTERED_MEASURED'), result.stdout + result.stderr);
                }
            }
        }
    }
} finally {
    fs.rmSync(directory, {recursive: true, force: true});
}
console.log('Centered slots: gap 4 px; equal end padding 12 px horizontal / 8 px vertical; clock centred on all edges');
