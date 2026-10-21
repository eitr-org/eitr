.pragma library

// Human names and type glyphs for PipeWire audio devices. ALSA descriptions
// carry the controller and channel layout ("GA104 High Definition Audio
// Controller Digital Stereo (HDMI) [34GL750]"); people know the device.

const connectors = {HDMI: "HDMI", DisplayPort: "DisplayPort", IEC958: "Optical"};

function friendlyName(description, nick) {
    let text = String(description || nick || "").trim();
    if (!text) return "";
    // An HDMI/DisplayPort sink names the monitor in brackets: that is the device.
    const monitor = text.match(/\[([^\]]+)\]\s*$/);
    if (monitor) return monitor[1].trim();
    let connector = "";
    const port = text.match(/\((HDMI|DisplayPort|IEC958)[^)]*\)\s*$/);
    if (port) {
        connector = connectors[port[1]];
        text = text.slice(0, port.index).trim();
    }
    text = text.replace(/\s+(Analog|Digital|Pro)?\s*(Stereo|Mono|Surround(\s+[\d.]+)?)\s*$/i, "")
               .replace(/\s+(Analog|Digital)\s*$/i, "").trim();
    if (!text) text = String(nick || description).trim();
    return connector ? text + " (" + connector + ")" : text;
}

// Glyph for the device type, from PipeWire's form factor and bus properties.
function glyph(properties, description, microphone) {
    const props = properties || {};
    const form = String(props["device.form-factor"] || "");
    const text = String(description || "");
    if (props["device.bus"] === "bluetooth" || ["headset", "headphone", "hands-free"].includes(form)) return "\u{F02CB}";
    if (form === "webcam") return "\u{F0567}";
    if (/\[[^\]]+\]\s*$|\((HDMI|DisplayPort)/.test(text)) return "\u{F0379}";
    if (/IEC958/.test(text)) return "\u{F0A17}";
    return microphone ? "\u{F036C}" : "\u{F04C3}";
}
