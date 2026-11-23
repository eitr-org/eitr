// SPDX-License-Identifier: MIT
// Copyright (c) 2026 The Eitr project
.pragma library

var MODES = [
    {id: "compact", label: "Compact"},
    {id: "detailed", label: "Detailed"}
];

function normalizeMode(value) {
    return value === "compact" ? "compact" : "detailed";
}

function clampUsage(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return null;
    return Math.max(0, Math.min(100, value));
}

function usageLevel(value) {
    const usage = clampUsage(value);
    if (usage === null) return "muted";
    if (usage >= 90) return "critical";
    if (usage >= 75) return "warning";
    return "normal";
}

function formatUsage(value) {
    const usage = clampUsage(value);
    return usage === null ? "—" : Math.round(usage) + "%";
}

function formatSpeed(bytesPerSec) {
    if (typeof bytesPerSec !== "number" || !Number.isFinite(bytesPerSec) || bytesPerSec < 0)
        return "—";
    const units = ["B/s", "KB/s", "MB/s", "GB/s"];
    let value = bytesPerSec;
    let unitIndex = 0;
    while (value >= 1000 && unitIndex < units.length - 1) {
        value /= 1000;
        unitIndex += 1;
    }
    const decimals = (unitIndex === 0 || value >= 100) ? 0 : 1;
    return value.toFixed(decimals) + " " + units[unitIndex];
}

function findRowValue(section, needle) {
    if (!section || !Array.isArray(section.rows)) return "";
    const target = String(needle).toLowerCase();
    for (let index = 0; index < section.rows.length; index++) {
        const row = section.rows[index];
        if (!Array.isArray(row) || row.length < 2) continue;
        const label = String(row[0] || "").toLowerCase();
        if (label === target || label.indexOf(target) >= 0) {
            return String(row[1] || "").trim();
        }
    }
    return "";
}

function extractTemp(section) {
    if (!section || !Array.isArray(section.rows)) return "";
    for (let index = 0; index < section.rows.length; index++) {
        const row = section.rows[index];
        if (!Array.isArray(row) || row.length < 2) continue;
        const label = String(row[0] || "").toLowerCase();
        if (label.indexOf("temp") < 0) continue;
        const value = String(row[1] || "");
        const match = value.match(/(-?\d+(?:\.\d+)?)\s*°\s*C/i);
        if (match) return Math.round(Number(match[1])) + "°C";
    }
    return "";
}

function extractFrequency(section) {
    const freqTemp = findRowValue(section, "frequency");
    if (!freqTemp) return "";
    const parts = freqTemp.split("·").map(part => part.trim()).filter(part => part && part.toLowerCase() !== "unavailable");
    const nonTemp = parts.filter(part => !/(-?\d+(?:\.\d+)?)\s*°\s*C/i.test(part));
    return nonTemp.length > 0 ? nonTemp[0] : "";
}

function isUnavailableText(text) {
    const clean = String(text || "").trim().toLowerCase();
    return !clean || clean === "unavailable" || clean.indexOf("telemetry unavailable") >= 0;
}

function hasGpuSection(section) {
    if (!section) return false;
    if (clampUsage(section.usage) !== null) return true;
    return Array.isArray(section.rows) && section.rows.length > 0;
}

function buildCpuMetric(section) {
    const usage = section ? clampUsage(section.usage) : null;
    const model = section && !isUnavailableText(section.name) ? String(section.name).trim() : "";
    const temp = extractTemp(section);
    const parts = [];
    const cores = findRowValue(section, "cores");
    if (cores && !isUnavailableText(cores)) parts.push(cores);
    const freq = extractFrequency(section);
    if (freq) parts.push(freq);
    return {
        id: "cpu",
        title: "CPU",
        usage: usage,
        usageText: formatUsage(usage),
        level: usageLevel(usage),
        temp: temp,
        primary: model,
        detail: parts.join(" · ")
    };
}

function buildGpuMetric(section) {
    const usage = section ? clampUsage(section.usage) : null;
    const model = section && !isUnavailableText(section.name) ? String(section.name).trim() : "";
    const temp = extractTemp(section);
    const parts = [];
    const vram = findRowValue(section, "vram");
    if (vram && !isUnavailableText(vram)) parts.push("VRAM " + vram);
    const power = findRowValue(section, "power");
    if (power && !isUnavailableText(power)) parts.push(power);
    return {
        id: "gpu",
        title: "GPU",
        usage: usage,
        usageText: formatUsage(usage),
        level: usageLevel(usage),
        temp: temp,
        primary: model,
        detail: parts.join(" · ")
    };
}

function buildRamMetric(section) {
    const usage = section ? clampUsage(section.usage) : null;
    const usedTotal = findRowValue(section, "used / total");
    const primary = usedTotal && !isUnavailableText(usedTotal)
        ? usedTotal
        : (section && !isUnavailableText(section.name) ? String(section.name).trim() : "");
    const parts = [];
    const available = findRowValue(section, "available");
    if (available && !isUnavailableText(available)) parts.push("Available " + available);
    const swap = findRowValue(section, "swap");
    if (swap && !isUnavailableText(swap) && swap.indexOf("0 B / 0 B") !== 0) parts.push("Swap " + swap);
    return {
        id: "ram",
        title: "RAM",
        usage: usage,
        usageText: formatUsage(usage),
        level: usageLevel(usage),
        temp: "",
        primary: primary,
        detail: parts.join(" · ")
    };
}

function buildStorageMetric(section) {
    const usage = section ? clampUsage(section.usage) : null;
    const usedTotal = findRowValue(section, "used / total");
    const capacity = findRowValue(section, "capacity");
    const primary = usedTotal && !isUnavailableText(usedTotal)
        ? usedTotal
        : (capacity && !isUnavailableText(capacity)
            ? capacity
            : (section && !isUnavailableText(section.name) ? String(section.name).trim() : ""));
    const parts = [];
    const freeSpace = findRowValue(section, "free");
    if (freeSpace && !isUnavailableText(freeSpace)) parts.push(freeSpace + " free");
    const device = findRowValue(section, "type / device");
    if (device && !isUnavailableText(device)) parts.push(device);
    return {
        id: "storage",
        title: "Storage",
        usage: usage,
        usageText: formatUsage(usage),
        level: usageLevel(usage),
        temp: "",
        primary: primary,
        detail: parts.join(" · ")
    };
}

function buildNetwork(snapshot) {
    const net = snapshot && snapshot.network ? snapshot.network : ({});
    const interfaces = Array.isArray(net.interfaces) ? net.interfaces.filter(item => !!item) : [];
    const connection = typeof net.connection === "string" && net.connection.trim()
        ? net.connection.trim()
        : (interfaces.length > 0 ? interfaces.join(", ") : "");
    return {
        status: net.status || "loading",
        downloadText: formatSpeed(net.download),
        uploadText: formatSpeed(net.upload),
        connection: connection,
        hasReading: typeof net.download === "number" || typeof net.upload === "number"
    };
}

function summarize(snapshot) {
    if (!snapshot) {
        return {state: "loading", message: "Loading...", metrics: [], network: buildNetwork(null)};
    }
    const sections = Array.isArray(snapshot.sections) ? snapshot.sections : [];
    const byTitle = {};
    for (let index = 0; index < sections.length; index++) {
        const section = sections[index];
        if (section && section.title) byTitle[String(section.title).toLowerCase()] = section;
    }
    const network = buildNetwork(snapshot);
    const hasSections = sections.length > 0;
    const loading = snapshot.status === "loading" && !hasSections;
    if (loading) {
        return {state: "loading", message: "Loading...", metrics: [], network: network};
    }
    if (!hasSections && (snapshot.status === "error" || snapshot.status === "unavailable" || snapshot.error || !network.hasReading)) {
        return {state: "error", message: "Hardware information unavailable", metrics: [], network: network};
    }

    const metrics = [];
    if (byTitle.cpu) metrics.push(buildCpuMetric(byTitle.cpu));
    if (hasGpuSection(byTitle.gpu)) metrics.push(buildGpuMetric(byTitle.gpu));
    if (byTitle.ram) metrics.push(buildRamMetric(byTitle.ram));
    if (byTitle.storage) metrics.push(buildStorageMetric(byTitle.storage));
    if (metrics.length === 0 && !network.hasReading) {
        return {state: "error", message: "Hardware information unavailable", metrics: [], network: network};
    }
    return {state: "ready", message: "", metrics: metrics, network: network};
}

if (typeof module !== "undefined") {
    module.exports = {
        MODES: MODES,
        normalizeMode: normalizeMode,
        clampUsage: clampUsage,
        usageLevel: usageLevel,
        formatUsage: formatUsage,
        formatSpeed: formatSpeed,
        extractTemp: extractTemp,
        hasGpuSection: hasGpuSection,
        summarize: summarize
    };
}
