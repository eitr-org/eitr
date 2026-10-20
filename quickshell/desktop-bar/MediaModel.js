.pragma library

function isMeeting(player) {
    var identity = [player.identity, player.desktopEntry, player.dbusName].join(" ").toLowerCase();
    if (/\b(zoom|teams|skype|webex|jitsi)\b|google.?meet/.test(identity)) return true;
    var metadata = player.metadata || {};
    var url = String(metadata["xesam:url"] || metadata.url || "").toLowerCase();
    var host = /^https?:\/\/([^/?#]+)/.exec(url);
    if (host && /^(meet\.google\.com|([\w-]+\.)?(zoom\.us|zoom\.com|webex\.com)|teams\.(microsoft\.com|live\.com|cloud\.microsoft)|meet\.jit\.si)(:\d+)?$/.test(host[1])) return true;
    return /\b(google meet|zoom meeting|microsoft teams|webex meeting)\b/i.test(String(player.trackTitle || ""));
}

function eligible(player) {
    return !String(player.dbusName || "").startsWith("org.mpris.MediaPlayer2.playerctld")
        && !isMeeting(player) && !!(player.trackTitle || player.trackArtist || player.isPlaying);
}
