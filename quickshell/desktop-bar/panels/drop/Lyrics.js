.pragma library

// Lyrics as lines: timed LRC ("[01:23.45] text", several stamps per line allowed) sorted by
// time, or plain lines with time -1 when nothing is timed.
function parse(source) {
    const timed = [];
    const plain = [];
    String(source || "").split(/\r?\n/).forEach(line => {
        const stamp = /\[(\d+):(\d+(?:\.\d+)?)\]/g;
        const words = line.replace(/\[[^\]]*\]/g, "").trim();
        let match, timedHere = false;
        while ((match = stamp.exec(line)) !== null) {
            timed.push({time: Number(match[1]) * 60 + Number(match[2]), text: words});
            timedHere = true;
        }
        if (!timedHere && words !== "") plain.push({time: -1, text: words});
    });
    return timed.length ? timed.sort((first, second) => first.time - second.time) : plain;
}

// The line sung at a position in seconds, or -1 for untimed lyrics.
function current(lines, position) {
    if (!lines.length || lines[0].time < 0) return -1;
    let found = 0;
    for (let index = 0; index < lines.length; index++) if (lines[index].time <= position) found = index;
    return found;
}
