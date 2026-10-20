.pragma library

// Forecast glyphs for open-meteo WMO weather codes, grouped like
// weather_icon() in scripts/weather-status.sh.
var groups = [
    {codes: [0], icon: "󰖙"},
    {codes: [1, 2], icon: "󰖕"},
    {codes: [3], icon: "󰖐"},
    {codes: [45, 48], icon: "󰖑"},
    {codes: [51, 53, 55, 56, 57, 61], icon: "󰖗"},
    {codes: [63, 65, 66, 67, 80, 81, 82], icon: "󰖖"},
    {codes: [71, 73, 75, 77, 85, 86], icon: "󰖘"},
    {codes: [95, 96, 99], icon: "󰙾"}
];
var fallbackIcon = "󰖐";

function forecastIcon(code) {
    var text = String(code === undefined || code === null ? "" : code).trim();
    if (!/^\d+$/.test(text)) return fallbackIcon;
    var value = Number(text);
    for (var i = 0; i < groups.length; i++) {
        if (groups[i].codes.indexOf(value) >= 0) return groups[i].icon;
    }
    return fallbackIcon;
}
