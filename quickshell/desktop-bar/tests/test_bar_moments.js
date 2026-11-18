const assert = require("node:assert/strict");
const queue = require("../bar/BarMoments.js");
const free = () => false;
let state = queue.create();
state = queue.push(state, {kind: "song", text: "Old song"}, 0, free);
state = queue.push(state, {kind: "notification", id: 1}, 10, free);
assert.equal(state.active.kind, "notification");
assert.equal(state.queue[0].kind, "song");
state = queue.push(state, {kind: "volume", level: 20}, 20, free);
state = queue.push(state, {kind: "volume", level: 30}, 1000, free);
assert.equal(state.active.level, 30);
assert.equal(state.active.deadline, 2500);
assert.equal(state.queue.length, 2);
state = queue.push(state, {kind: "notification", id: 2, critical: true}, 1100, free);
state = queue.push(state, {kind: "notification", id: 3}, 1200, free);
assert.equal(state.active.id, 2);
assert.equal(state.active.deadline, 0);
state = queue.advance(state, 20000, free);
assert.equal(state.active.id, 2);
assert.equal(state.queue.length, 0);
state = queue.retainNotifications(state, []);
assert.equal(state.active, null);
for (const reason of ["hover", "panel", "focus"]) {
    let blocked = true;
    const interaction = () => blocked;
    state = queue.push(queue.create(), {kind: "layout"}, 0, interaction);
    assert.equal(state.active, null, reason);
    blocked = false;
    state = queue.advance(state, 5000, interaction);
    assert.equal(state.active.kind, "layout", reason);
    blocked = true;
    state = queue.advance(state, 5100, interaction);
    assert.equal(state.active, null, reason);
    state = queue.advance(state, 6000, interaction);
    assert.equal(state.queue.length, 0, reason);
}
state = queue.push(queue.create(), {kind: "notification", id: 1}, 0, free);
state = queue.push(state, {kind: "song"}, 20, free);
state = queue.advance(state, 25, island => island === "middle");
assert.equal(state.active.kind, "song");
assert.equal(state.queue[0].id, 1);
state = queue.push(queue.create(), {kind: "layout"}, 0, () => true);
state = queue.push(state, {kind: "layout", text: "BR"}, 1, () => true);
assert.equal(state.queue.length, 1);
assert.equal(queue.wakeAt(state, 1), 6000);
state = queue.push(state, {kind: "bluetooth"}, 2, free);
assert.equal(state.active.kind, "bluetooth");
state = queue.push(state, {kind: "notification", id: 99}, 3, free);
state = queue.push(state, {kind: "brightness"}, 4, free);
assert.equal(state.active.kind, "brightness");
state = queue.advance(state, 1504, free);
assert.equal(state.active.kind, "notification");
console.log("Dynamic queue: priorities, preemption, repeat replacement, expiry, critical dismissal and interaction waiting passed");

// The pointer holds a moment: no deadline while hovered, a short linger after.
{
    const Queue = queue;
    let state = Queue.push(Queue.create(), {kind: "notification", id: 1, text: "Held"}, 1000, () => false, () => false);
    assert.equal(state.active.deadline, 5000);
    state = Queue.advance(state, 2000, () => true, () => true);
    assert.equal(state.active.text, "Held");
    assert.equal(state.active.deadline, 0);
    state = Queue.advance(state, 9000, () => true, () => true);
    assert.equal(state.active.text, "Held");
    state = Queue.advance(state, 9500, () => false, () => false);
    assert.equal(state.active.deadline, 11000);
    state = Queue.advance(state, 11000, () => false, () => false);
    assert.equal(state.active, null);
}

// Audio output change deduplication: ignore startup and <1s flapping, allow real switches.
{
    let audio = queue.createAudioOutputState();
    let res = queue.updateAudioOutput(audio, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"}, 100);
    audio = res.state;
    assert.equal(res.emit, null, "Initial device at startup must not emit");

    let delayed = queue.createAudioOutputState();
    delayed = queue.updateAudioOutput(delayed, null, 0).state;
    res = queue.updateAudioOutput(delayed, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"}, 500);
    assert.equal(res.emit, null, "First ready device after null startup must not emit");

    res = queue.updateAudioOutput(audio, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"}, 200);
    audio = res.state;
    assert.equal(res.emit, null, "Unchanged device must not emit");

    res = queue.updateAudioOutput(audio, {key: "bluez_output.1", label: "WH-1000XM5", icon: "󰋋"}, 2000);
    audio = res.state;
    assert.deepEqual(res.emit, {key: "bluez_output.1", label: "WH-1000XM5", icon: "󰋋"});

    // Device drops and reappears within 1s: flapping is debounced.
    audio = queue.updateAudioOutput(audio, null, 2400).state;
    res = queue.updateAudioOutput(audio, {key: "bluez_output.1", label: "WH-1000XM5", icon: "󰋋"}, 2900);
    audio = res.state;
    assert.equal(res.emit, null, "Reappearance within 1s must be debounced");

    // Transient switch to A and back to B within 1s: B is debounced.
    res = queue.updateAudioOutput(audio, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"}, 4000);
    audio = res.state;
    assert.equal(res.emit.key, "alsa_output.pci.analog");
    res = queue.updateAudioOutput(audio, {key: "bluez_output.1", label: "WH-1000XM5", icon: "󰋋"}, 4600);
    audio = res.state;
    assert.equal(res.emit, null, "Transient return within 1s must be debounced");

    // Switching back >= 1s later is announced.
    res = queue.updateAudioOutput(audio, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"}, 6000);
    assert.deepEqual(res.emit, {key: "alsa_output.pci.analog", label: "Built-in Audio", icon: "󰓃"});

    // Audio moments share queue priority/duration and replace previous audio moments.
    let q = queue.push(queue.create(), {kind: "audio", icon: "󰋋", text: "Now using: Headphones"}, 0, free);
    assert.equal(q.active.kind, "audio");
    assert.equal(q.active.deadline, 3000);
    q = queue.push(q, {kind: "audio", icon: "󰍹", text: "Now using: 34GL750"}, 200, free);
    assert.equal(q.active.text, "Now using: 34GL750");
    assert.equal(q.queue.length, 0);
}
console.log("Audio output moment dedup checks passed");
