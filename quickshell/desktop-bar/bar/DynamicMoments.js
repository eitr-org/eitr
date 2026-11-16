// Pure queue state. The QML owner supplies time and per-island interaction blocks.
var priorities = {critical: 6, volume: 5, brightness: 5, notification: 4, bluetooth: 3, layout: 2, song: 1};
var durations = {volume: 1500, brightness: 1500, notification: 4000, bluetooth: 3000, layout: 2000, song: 3000};
function create() { return {active: null, queue: []}; }
function island(moment) { return moment.kind === "song" ? "media" : "middle"; }
function priority(moment) { return moment.critical ? priorities.critical : priorities[moment.kind]; }
function advance(state, now, blocked) {
    let active = state.active;
    let queue = state.queue.filter(moment => now - moment.created < 6000);
    if (active && active.deadline && active.deadline <= now) active = null;
    if (active && blocked(island(active))) {
        if (now - active.created < 6000) queue.push(active);
        active = null;
    }
    queue.sort((first, second) => priority(second) - priority(first) || first.created - second.created);
    const index = queue.findIndex(moment => !blocked(island(moment)));
    if (index !== -1 && (!active || priority(queue[index]) > priority(active))) {
        if (active && now - active.created < 6000) queue.push(active);
        active = queue.splice(index, 1)[0];
        active = Object.assign({}, active, {deadline: active.critical ? 0 : now + (durations[active.kind] || 3000)});
    }
    return {active: active, queue: queue};
}
function push(state, payload, now, blocked) {
    const moment = Object.assign({}, payload, {created: now, deadline: 0});
    if (!priorities[moment.kind]) return state;
    const same = entry => entry.kind === moment.kind && !!entry.critical === !!moment.critical;
    const next = {active: state.active && !same(state.active) ? state.active : null,
        queue: state.queue.filter(entry => !same(entry)).concat([moment])};
    return advance(next, now, blocked);
}
function retainNotifications(state, ids) {
    const keep = moment => moment.kind !== "notification" || ids.indexOf(moment.id) !== -1;
    return {active: state.active && keep(state.active) ? state.active : null, queue: state.queue.filter(keep)};
}
function wakeAt(state, now) {
    const deadlines = state.queue.map(moment => moment.created + 6000);
    if (state.active && state.active.deadline) deadlines.push(state.active.deadline);
    return deadlines.length ? Math.max(1, Math.min.apply(null, deadlines) - now) : 0;
}
if (typeof module !== "undefined") module.exports = {create, push, advance, retainNotifications, wakeAt, island};
