import "../.."
import QtQuick
import Quickshell.Io
import Eitr as Eitr

// Where Drop's lyrics come from: the player's own (xesam:asText) when it sends them,
// otherwise LRCLIB once the owner has turned online lyrics on. That choice is kept in the
// machine-local eitr/lyrics.json; looking a song up sends its title, artist, album and
// length to lrclib.net through the bar's data service.
QtObject {
    id: source
    required property var player
    required property bool active
    property bool online: false
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
        online = value;
        store.setText(JSON.stringify({online: value}, null, 2) + "\n");
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
    property FileView store: FileView {
        path: Eitr.Paths.config("eitr/lyrics.json")
        atomicWrites: true; printErrors: false
        onLoaded: {
            try { source.online = JSON.parse(text()).online === true; }
            catch (error) { source.online = false; }
        }
        onLoadFailed: source.online = false
    }
}
