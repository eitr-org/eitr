function createClient(send, changed) {
    const tokens = {};
    const states = {};
    let epoch = "";
    let sequence = 0;
    let online = false;
    let capturePresent = false;
    const actions = {};
    const captureActions = {};
    const powerActions = {};
    const powerDomain = {busy: false, name: ""};
    let powerReconcile = {"power.profile": true, "power.radios": true};
    let powerReconcileSeq = {"power.profile": -1, "power.radios": -1};
    function actPower(name, args, callback) {
        const topic = name === "profile" ? "power.profile" : "power.radios";
        if (!online || powerReconcile[topic] || !states[topic] || states[topic].status !== "ready" || powerDomain.busy) return "";
        const id = "action-" + (++sequence);
        actions[id] = callback; powerActions[id] = topic;
        powerDomain.busy = true; powerDomain.name = name;
        send({v: 1, op: "action", topic: "power", id: id, name: name, args: args});
        changed();
        return id;
    }
    let reconcile = true;
    let reconcileSeq = -1;
    const domain = {busy: false, name: ""};
    const captureDomain = {busy: false, name: ""};
    const reconciliation = {capture: true};
    let captureReconcileSeq = -1;
    function actCapture(name, args, callback) {
        const snapshot = states["capture.summary"];
        if (!online || reconciliation.capture || !snapshot || snapshot.status !== "ready" || captureDomain.busy) return "";
        const id = "action-" + (++sequence);
        actions[id] = callback;
        captureActions[id] = true;
        captureDomain.busy = true; captureDomain.name = name;
        send({v: 1, op: "action", topic: "capture", id: id, name: name, args: args});
        changed();
        return id;
    }
    function act(name, args, callback) {
        if (reconcile || !online || !states["network.summary"] || states["network.summary"].status !== "ready" || domain.busy) return "";
        const id = "action-" + (++sequence);
        actions[id] = callback;
        domain.busy = true; domain.name = name;
        send({v: 1, op: "action", topic: "network", id: id, name: name, args: args});
        changed();
        return id;
    }
    function detachAction(id) { if (actions[id]) actions[id] = function() {}; }
    function request(op, topic, token) {
        if (online) send({v: 1, op: op, topic: topic, token: token || "", id: "read-" + (++sequence), interval: tokens[token] ? tokens[token].interval : undefined});
    }
    function observe(topic, owner, interval) {
        if (Object.keys(tokens).length >= 256) throw new Error("Too many data observers");
        const token = "data-" + (++sequence);
        tokens[token] = {topic: topic, owner: owner, interval: interval};
        request("subscribe", topic, token);
        changed();
        return token;
    }
    function release(token) {
        if (!tokens[token]) return;
        request("unsubscribe", tokens[token].topic, token);
        delete tokens[token];
        changed();
    }
    function receive(text) {
        if (text.length > 262144) return;
        let frame;
        try { frame = JSON.parse(text); } catch (error) { return; }
        if (!frame || frame.v !== 1) return;
        if (frame.op === "hello") {
            if (online || typeof frame.epoch !== "string" || !frame.epoch) return;
            epoch = frame.epoch;
            online = true;
            if (capturePresent) send({v: 1, op: "presence", topic: "capture", present: true});
            Object.keys(tokens).forEach(token => request("subscribe", tokens[token].topic, token));
        } else if (online && frame.epoch === epoch && frame.topic === "power" && frame.op === "domain") {
            powerDomain.busy = frame.busy === true || Object.keys(powerActions).length > 0;
            if (frame.busy === true || !powerDomain.busy) powerDomain.name = frame.name || "";
        } else if (online && frame.epoch === epoch && frame.topic === "power" && frame.op === "result") {
            const callback = actions[frame.id];
            const actionTopic = powerActions[frame.id];
            delete actions[frame.id]; delete powerActions[frame.id];
            if (frame.error === "outcome-unknown") {
                powerReconcile[actionTopic] = true;
                powerReconcileSeq[actionTopic] = states[actionTopic] ? states[actionTopic].seq : -1;
            }
            if (callback) callback(frame.error || "", frame.message || "");
        } else if (online && frame.epoch === epoch && frame.topic === "capture" && frame.op === "domain") {
            captureDomain.busy = frame.busy === true || Object.keys(captureActions).length > 0;
            if (frame.busy === true || !captureDomain.busy) captureDomain.name = frame.name || "";
        } else if (online && frame.epoch === epoch && frame.topic === "capture" && frame.op === "result") {
            const callback = actions[frame.id];
            delete actions[frame.id]; delete captureActions[frame.id];
            if (frame.error === "outcome-unknown") {
                reconciliation.capture = true;
                captureReconcileSeq = states["capture.summary"] ? states["capture.summary"].seq : -1;
            }
            if (callback) callback(frame.error || "", frame.message || "");
        } else if (online && frame.epoch === epoch && frame.topic === "network" && frame.op === "domain") {
            domain.busy = frame.busy === true || Object.keys(actions).some(id => !captureActions[id] && !powerActions[id]);
            if (frame.busy === true || !domain.busy) domain.name = frame.name || "";
        } else if (online && frame.epoch === epoch && frame.topic === "network" && frame.op === "result") {
            if (typeof frame.busy === "boolean") {
                domain.busy = frame.busy;
                if (!frame.busy) domain.name = "";
            }
            const callback = actions[frame.id];
            delete actions[frame.id];
            if (frame.error === "outcome-unknown") {
                reconcile = true;
                reconcileSeq = states["network.summary"] ? states["network.summary"].seq : -1;
            }
            if (callback) callback(frame.error || "", frame.message || "");
        } else if (online && frame.epoch === epoch && frame.op === "state") {
            if (!["remote.availability", "remote.status", "hardware.details", "display.topology", "display.settings", "display.brightness", "display.nightlight", "power.battery", "power.profile", "power.radios", "network.summary", "network.details", "network.latency", "capture.summary", "capture.details", "capture.options"].includes(frame.topic)
                || !Number.isInteger(frame.seq) || frame.seq < 0
                || !["loading", "ready", "unavailable", "stale", "error"].includes(frame.status)
                || !frame.data || typeof frame.data !== "object") return;
            const previous = states[frame.topic];
            if (previous && previous.epoch === epoch && previous.seq > frame.seq) return;
            if (frame.topic === "network.summary" && frame.status === "ready" && frame.seq > reconcileSeq) reconcile = false;
            if (frame.topic === "capture.summary" && frame.status === "ready" && frame.seq > captureReconcileSeq) reconciliation.capture = false;
            if (frame.topic in powerReconcile && frame.status === "ready" && frame.seq > powerReconcileSeq[frame.topic]) powerReconcile[frame.topic] = false;
            // A restarted broker's loading snapshot must not erase retained good state.
            if (frame.status === "loading" && previous && previous.updatedAt) return;
            if (frame.status !== "ready" && previous && previous.updatedAt && frame.ageMs === null) {
                states[frame.topic] = Object.assign({}, frame, {
                    data: previous.data, status: "stale", updatedAt: previous.updatedAt
                });
                changed();
                return;
            }
            states[frame.topic] = Object.assign({}, frame, {
                updatedAt: frame.ageMs === null ? 0 : Date.now() - frame.ageMs
            });
        } else return;
        changed();
    }
    function died() {
        online = false;
        powerReconcile = {"power.profile": true, "power.radios": true}; powerReconcileSeq = {"power.profile": -1, "power.radios": -1};
        powerDomain.busy = false; powerDomain.name = "";
        Object.keys(powerActions).forEach(id => delete powerActions[id]);
        reconciliation.capture = true;
        captureReconcileSeq = -1;
        captureDomain.busy = false; captureDomain.name = "";
        Object.keys(captureActions).forEach(id => delete captureActions[id]);
        reconcile = true;
        reconcileSeq = -1;
        domain.busy = false; domain.name = "";
        Object.keys(actions).forEach(id => {
            const callback = actions[id]; delete actions[id]; callback("outcome-unknown");
        });
        Object.keys(states).forEach(topic => {
            states[topic] = Object.assign({}, states[topic], {
                status: states[topic].updatedAt ? "stale" : "unavailable", error: "broker-unavailable"
            });
        });
        changed();
    }
    return {setCapturePresence: present => {
            capturePresent = present;
            if (online) send({v: 1, op: "presence", topic: "capture", present: present});
        }, actPower: actPower, powerDomain: powerDomain, actCapture: actCapture, captureDomain: captureDomain, act: act, detachAction: detachAction, domain: domain, online: () => online, epoch: () => epoch, tokens: tokens, states: states, observe: observe, release: release, receive: receive, died: died,
        refresh: topic => request("refresh", topic),
        releaseOwner: owner => Object.keys(tokens).filter(token => tokens[token].owner === owner).forEach(release),
        count: topic => Object.keys(tokens).filter(token => tokens[token].topic === topic).length};
}
function restartDelay(failures, random) {
    return Math.round(Math.min(30000, 500 * Math.pow(2, failures - 1) * (0.8 + random * 0.4)));
}
if (typeof module !== "undefined") module.exports = {createClient, restartDelay};
