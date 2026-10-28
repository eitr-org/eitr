import QtQuick

Behavior {
    id: resizeBehavior
    required property var ownerPanel
    enabled: ownerPanel.opened && ownerPanel.revealProgress > 0
    NumberAnimation {
        duration: {
            // Recompute the remaining time for each new target, without extending the reveal.
            const target = resizeBehavior.targetValue;
            return resizeBehavior.ownerPanel.remainingResizeDuration
                ? resizeBehavior.ownerPanel.remainingResizeDuration(target) : resizeBehavior.ownerPanel.transitionDuration;
        }
        easing.type: resizeBehavior.targetValue >= resizeBehavior.targetProperty.object[resizeBehavior.targetProperty.name] ? Easing.OutCubic : Easing.InCubic
    }
}
