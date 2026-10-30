function glyph(snapshot, blocked) {
    if (blocked === undefined ? snapshot.blocked : blocked) return "󰤮";
    for (const device of snapshot.devices || []) {
        const connected = (device.networks || []).find(network => network.connected);
        if (!connected) continue;
        const strength = Number(connected.strength);
        const thresholds = snapshot.backend === "networkmanager" ? [75, 55, 35, 15] : [100, 80, 60, 40];
        const icons = ["󰤨", "󰤥", "󰤢", "󰤟", "󰤯"];
        const index = thresholds.findIndex(threshold => strength >= threshold);
        return icons[index < 0 ? 4 : index];
    }
    return "";
}

if (typeof module !== "undefined") module.exports = {glyph, createOwner};

// The same demand and refresh state machine drives the shell and fake readers.
function createOwner(start, stop, changed) {
    const topics = {};
    for (const name of ["summary", "details", "latency"])
        topics[name] = {status: "loading", data: {}, updatedAt: 0, error: "", running: false, pending: false, cancelled: false};
    const tokens = {};
    let sequence = 0;
    function count(topic) {
        return Object.keys(tokens).filter(token => tokens[token].topic === topic).length;
    }
    function wanted(topic) { return topic === "summary" || count(topic) > 0; }
    function refresh(topic) {
        if (!wanted(topic)) return;
        const state = topics[topic];
        if (state.running) { state.pending = true; changed(); return; }
        state.running = true;
        state.cancelled = false;
        if (start(topic) === false) state.running = false;
        changed();
    }
    function finish(topic, text, code) {
        const state = topics[topic];
        if (!state.running) return;
        state.running = false;
        if (state.cancelled) {
            state.cancelled = false;
            const pending = state.pending;
            state.pending = false;
            changed();
            if (pending) refresh(topic);
            return;
        }
        try {
            const result = JSON.parse(text);
            if (result.error) {
                state.status = state.updatedAt ? "stale" : "unavailable";
                state.error = result.error;
            } else {
                if (code !== 0 || !result || typeof result !== "object"
                    || (topic !== "latency" && !Array.isArray(result.devices))
                    || (topic === "latency" && !("ping" in result))) throw new Error("Invalid network result");
                state.data = result;
                state.updatedAt = Date.now();
                state.status = "ready";
                state.error = "";
            }
        } catch (error) {
            state.status = state.updatedAt ? "stale" : "error";
            state.error = "WiFi unavailable";
        }
        const pending = state.pending;
        state.pending = false;
        changed();
        if (pending) refresh(topic);
    }
    function observe(owner, topic) {
        topic = topic || "details";
        if (topic !== "details" && topic !== "latency") throw new Error("Unknown network topic");
        const token = "network-" + (++sequence);
        tokens[token] = {owner: owner, topic: topic};
        refresh(topic);
        changed();
        return token;
    }
    function release(token) {
        if (!tokens[token]) return;
        const topic = tokens[token].topic;
        delete tokens[token];
        if (!wanted(topic)) {
            topics[topic].pending = false;
            if (topics[topic].running) {
                topics[topic].cancelled = true;
                stop(topic);
            }
        }
        changed();
    }
    function releaseOwner(owner) {
        Object.keys(tokens).filter(token => tokens[token].owner === owner).forEach(release);
    }
    return {releaseOwner: releaseOwner, topics: topics, count: count, refresh: refresh, finish: finish,
        observe: observe, release: release};
}
