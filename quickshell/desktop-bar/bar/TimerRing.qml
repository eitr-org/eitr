import ".."
import QtQuick

// A small ring beside the clock that fills as the active timer, focus phase, or stopwatch goes on.
ProgressRing {
    property color foreground
    width: 14; height: 14
    progress: ClockTimers.activityProgress
    trackColor: Qt.alpha(foreground, 0.3)
    accentColor: foreground
    lineWidth: 2
    ringPadding: 1.5
    minimumArc: 0.02
    animateProgress: false
}
