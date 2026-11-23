"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadQmlLibrary(relativePath) {
    const filePath = path.resolve(__dirname, "../../..", relativePath);
    const source = fs.readFileSync(filePath, "utf8").replace(".pragma library", "");
    const sandbox = {module: {exports: {}}};
    vm.runInNewContext(source, sandbox, {filename: filePath});
    return sandbox.module.exports;
}

const HardwareState = loadQmlLibrary("distro/plugins/bundled/hardware/HardwareState.js");

assert.strictEqual(HardwareState.normalizeMode("compact"), "compact");
assert.strictEqual(HardwareState.normalizeMode("detailed"), "detailed");
assert.strictEqual(HardwareState.normalizeMode("unknown"), "detailed");

assert.strictEqual(HardwareState.formatSpeed(null), "—");
assert.strictEqual(HardwareState.formatSpeed(undefined), "—");
assert.strictEqual(HardwareState.formatSpeed(-10), "—");
assert.strictEqual(HardwareState.formatSpeed(0), "0 B/s");
assert.strictEqual(HardwareState.formatSpeed(512), "512 B/s");
assert.strictEqual(HardwareState.formatSpeed(1500), "1.5 KB/s");
assert.strictEqual(HardwareState.formatSpeed(12400000), "12.4 MB/s");
assert.strictEqual(HardwareState.formatSpeed(250000000), "250 MB/s");
assert.strictEqual(HardwareState.formatSpeed(1800000000), "1.8 GB/s");

assert.strictEqual(HardwareState.usageLevel(null), "muted");
assert.strictEqual(HardwareState.usageLevel(0), "normal");
assert.strictEqual(HardwareState.usageLevel(74.9), "normal");
assert.strictEqual(HardwareState.usageLevel(75), "warning");
assert.strictEqual(HardwareState.usageLevel(89.9), "warning");
assert.strictEqual(HardwareState.usageLevel(90), "critical");

assert.strictEqual(HardwareState.extractTemp({rows: [["Frequency / temperature", "3.85 GHz · 48°C"]]}), "48°C");
assert.strictEqual(HardwareState.extractTemp({rows: [["Temperature", "44.0 °C"]]}), "44°C");
assert.strictEqual(HardwareState.extractTemp({rows: [["Frequency / temperature", "3.85 GHz · Unavailable"]]}), "");
assert.strictEqual(HardwareState.extractTemp({rows: [["Temperature", "Unavailable"]]}), "");
assert.strictEqual(HardwareState.extractTemp({rows: []}), "");

assert.strictEqual(HardwareState.summarize(null).state, "loading");
assert.strictEqual(HardwareState.summarize({status: "loading", sections: []}).message, "Loading...");

const failed = HardwareState.summarize({
    status: "error",
    error: "timeout",
    sections: [],
    network: {status: "error", download: null, upload: null}
});
assert.strictEqual(failed.state, "error");
assert.strictEqual(failed.message, "Hardware information unavailable");

const full = HardwareState.summarize({
    status: "ready",
    error: "",
    sections: [
        {title: "CPU", name: "AMD Ryzen 7 7840U", usage: 34, rows: [["Cores / threads", "8 / 16"], ["Frequency / temperature", "3.85 GHz · 52°C"]]},
        {title: "GPU", name: "AMD Radeon 780M", usage: 18, rows: [["VRAM used / total", "1.2 / 4.0 GiB"], ["Temperature", "47.0 °C"]]},
        {title: "RAM", name: "Memory", usage: 46, rows: [["Used / total", "14.4 GiB / 31.3 GiB"], ["Available", "16.9 GiB"]]},
        {title: "Storage", name: "Root", usage: 55, rows: [["Type / device", "NVMe SSD · nvme0n1"], ["Used / total", "240 GiB / 460 GiB"], ["Free", "220 GiB"]]}
    ],
    network: {status: "ready", download: 12400000, upload: 1800000, interfaces: ["wlan0"], connection: "Studio WiFi"}
});
assert.strictEqual(full.state, "ready");
assert.deepStrictEqual(Array.from(full.metrics.map(metric => metric.title)), ["CPU", "GPU", "RAM", "Storage"]);
assert.strictEqual(full.metrics[0].temp, "52°C");
assert.strictEqual(full.metrics[1].temp, "47°C");
assert.strictEqual(full.network.downloadText, "12.4 MB/s");
assert.strictEqual(full.network.uploadText, "1.8 MB/s");

const noGpuNoTemp = HardwareState.summarize({
    status: "ready",
    error: "",
    sections: [
        {title: "CPU", name: "Intel Core i5-1240P", usage: 82, rows: [["Cores / threads", "12 / 16"], ["Frequency / temperature", "Unavailable"]]},
        {title: "GPU", name: "GPU telemetry unavailable", usage: null, rows: []},
        {title: "RAM", name: "Memory", usage: 92, rows: [["Used / total", "14.7 GiB / 16.0 GiB"], ["Available", "1.3 GiB"]]},
        {title: "Storage", name: "Root", usage: 40, rows: [["Used / total", "100 GiB / 250 GiB"], ["Free", "150 GiB"]]}
    ],
    network: {status: "loading", download: null, upload: null, interfaces: ["enp4s0"], connection: ""}
});
assert.strictEqual(noGpuNoTemp.state, "ready");
assert.deepStrictEqual(Array.from(noGpuNoTemp.metrics.map(metric => metric.title)), ["CPU", "RAM", "Storage"]);
assert.strictEqual(noGpuNoTemp.metrics[0].temp, "");
assert.strictEqual(noGpuNoTemp.metrics[0].level, "warning");
assert.strictEqual(noGpuNoTemp.metrics[1].level, "critical");
assert.strictEqual(noGpuNoTemp.network.downloadText, "—");
assert.strictEqual(noGpuNoTemp.network.connection, "enp4s0");

console.log("Hardware widget state checks passed");
