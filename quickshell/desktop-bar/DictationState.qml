import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Pipewire

Scope {
    id: dictation
    // Hold-to-talk dictation (walker/scripts/actions/tools/dictate.sh) turns the
    // recording dot into a live waveform while the microphone listens, then a
    // slow pulse while the speech is transcribed.
    property bool dictating: false
    property bool transcribing: false
    // Microphone levels for the waveform, newest first (drawn at the centre).
    property var dictationLevels: [0, 0, 0, 0]
    IpcHandler {
        target: "dictation"
        function start(): void { dictation.transcribing = false; dictation.dictating = true; dictationSafety.restart(); }
        function transcribe(): void { dictation.dictating = false; dictation.transcribing = true; dictationSafety.restart(); }
        function stop(): void { dictation.dictating = false; dictation.transcribing = false; dictationSafety.stop(); }
    }
    // A lost stop must not leave the dot on.
    Timer { id: dictationSafety; interval: 300000; onTriggered: { dictation.dictating = false; dictation.transcribing = false; } }
    // The waveform never outlives the recording: while it shows, check every few
    // seconds that a recorder still exists (dictate.sh keeps its pid in these files).
    Timer {
        interval: 3000; repeat: true; running: dictation.dictating
        onTriggered: dictationAlive.running = true
    }
    Process {
        id: dictationAlive
        command: ["sh", "-c", "for mode in dictation voice; do f=\"${XDG_RUNTIME_DIR:-/tmp}/eitr-$mode.pid\"; [ -f \"$f\" ] && kill -0 \"$(cat \"$f\")\" 2>/dev/null && exit 0; done; exit 1"]
        onExited: (code) => { if (code !== 0 && dictation.dictating) dictation.dictating = false; }
    }
    PwNodePeakMonitor {
        id: dictationPeak
        node: Pipewire.defaultAudioSource
        enabled: dictation.dictating && node !== null
    }
    Timer {
        interval: 70; repeat: true; running: dictation.dictating
        // Speech peaks sit low on a linear scale; the square root lifts them.
        onTriggered: dictation.dictationLevels = [Math.min(1, Math.sqrt(dictationPeak.peak) * 1.4)].concat(dictation.dictationLevels.slice(0, 3))
    }
    onDictatingChanged: if (!dictating) dictationLevels = [0, 0, 0, 0]
}
