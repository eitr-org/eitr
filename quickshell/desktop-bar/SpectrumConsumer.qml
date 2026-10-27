import QtQuick
import "Spectrum.js" as Spectrum

QtObject {
    id: consumer
    property bool active: false
    property int bars: 64
    property bool plugin: false
    property bool smoothing: false
    property int frameRate: 30
    property var spectrum: []
    readonly property bool audioActive: active && SpectrumProvider.audioActive
    property bool registered: false
    function sync() {
        if (active && !registered) { registered = true; SpectrumProvider.acquire(consumer); }
        else if (!active && registered) { registered = false; SpectrumProvider.release(consumer); spectrum = []; }
    }
    onBarsChanged: if (registered) SpectrumProvider.update()
    onFrameRateChanged: if (registered) SpectrumProvider.update()
    onSmoothingChanged: if (registered) SpectrumProvider.update()
    onPluginChanged: if (registered) SpectrumProvider.update()
    onActiveChanged: sync()
    Component.onCompleted: sync()
    Component.onDestruction: if (registered) SpectrumProvider.release(consumer)
    property Timer frames: Timer {
        interval: Math.ceil(1000 / Spectrum.count(consumer.frameRate, 1, 60))
        running: consumer.active
        repeat: true
        onTriggered: {
            if (!consumer.active) return;
            const values = Spectrum.resample(SpectrumProvider.levels, Spectrum.count(consumer.bars, 4, 128));
            consumer.spectrum = consumer.smoothing && !SpectrumProvider.config.smoothing
                ? Spectrum.smooth(values, consumer.spectrum) : values;
        }
    }
}
