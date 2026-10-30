function createClient(send, changed) {
    const tokens = {};
    const states = {};
    let epoch = "";
    let sequence = 0;
    let online = false;
    function request(op, topic, token) {
        if (online) send({v: 1, op: op, topic: topic, token: token || "", id: "read-" + (++sequence)});
    }
    function observe(topic, owner) {
        if (Object.keys(tokens).length >= 256) throw new Error("Too many data observers");
        const token = "data-" + (++sequence);
        tokens[token] = {topic: topic, owner: owner};
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
            Object.keys(tokens).forEach(token => request("subscribe", tokens[token].topic, token));
        } else if (online && frame.epoch === epoch && frame.op === "state") {
            if (!["network.summary", "network.details", "network.latency"].includes(frame.topic)
                || !Number.isInteger(frame.seq) || frame.seq < 0
                || !["loading", "ready", "unavailable", "stale", "error"].includes(frame.status)
                || !frame.data || typeof frame.data !== "object") return;
            const previous = states[frame.topic];
            if (previous && previous.epoch === epoch && previous.seq > frame.seq) return;
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
        Object.keys(states).forEach(topic => {
            states[topic] = Object.assign({}, states[topic], {
                status: states[topic].updatedAt ? "stale" : "unavailable", error: "broker-unavailable"
            });
        });
        changed();
    }
    return {epoch: () => epoch, tokens: tokens, states: states, observe: observe, release: release, receive: receive, died: died,
        refresh: topic => request("refresh", topic),
        releaseOwner: owner => Object.keys(tokens).filter(token => tokens[token].owner === owner).forEach(release),
        count: topic => Object.keys(tokens).filter(token => tokens[token].topic === topic).length};
}
function restartDelay(failures, random) {
    return Math.round(Math.min(30000, 500 * Math.pow(2, failures - 1) * (0.8 + random * 0.4)));
}
if (typeof module !== "undefined") module.exports = {createClient, restartDelay};
