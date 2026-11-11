import ".."
import QtQuick
import Quickshell

// Where lyrics come from (Media panel, Drop's pill, the bar's media wave): the player's own (xesam:asText) when it sends them,
// otherwise LRCLIB once the owner has turned online lyrics on (the bar setting "lyrics",
// also in Settings > Desktop Bar and Walker). Looking a song up sends its title, artist,
// album and length to lrclib.net through the bar's data service.
QtObject {
    id: source
    required property var player
    required property bool active
    required property var host
    readonly property bool online: !!host.barLyrics
    // "", "loading", "none" (nothing known for the song) or "unavailable".
    property string state: ""
    property string fetched: ""
    property string request: ""
    property string fetchedFor: ""
    readonly property string fromPlayer: player && player.metadata ? String(player.metadata["xesam:asText"] || "") : ""
    readonly property string text: fromPlayer || (online ? fetched : "")
    readonly property var track: player ? {
        title: String(player.trackTitle || ""), artist: String(player.trackArtist || ""),
        album: String(player.trackAlbum || ""), duration: player.lengthSupported ? Math.round(player.length) : 0
    } : null
    readonly property string trackKey: track && track.title ? JSON.stringify(track) : ""
    readonly property bool wanted: active && online && !fromPlayer && trackKey !== ""
    onWantedChanged: lookUp()
    onTrackKeyChanged: lookUp()

    function setOnline(value) {
        Quickshell.execDetached(["python3", Quickshell.shellDir + "/scripts/bar-settings.py", "set", "lyrics", value ? "yes" : "no"]);
    }
    function lookUp() {
        if (!wanted || fetchedFor === trackKey) return;
        if (request) DesktopData.cancelQuery(request);
        const key = trackKey;
        fetched = ""; state = "loading"; fetchedFor = key;
        request = DesktopData.queryLyrics({title: track.title.slice(0, 300), artist: track.artist.slice(0, 300),
                                           album: track.album.slice(0, 300), duration: Math.min(36000, Math.max(0, track.duration))},
            source, function(error, data) {
                if (key !== source.fetchedFor) return;
                source.request = "";
                if (error || data.error) { source.state = "unavailable"; source.fetchedFor = ""; retry.restart(); return; }
                source.fetched = data.synced || data.plain || "";
                source.state = source.fetched ? "" : "none";
            });
    }

    // A failed lookup (the data service still starting, LRCLIB unreachable) tries again.
    property Timer retry: Timer { interval: 8000; onTriggered: source.lookUp() }
}
