import QtQuick

Behavior {
    id: resizeBehavior
    required property var ownerPanel
    enabled: ownerPanel.opened && ownerPanel.revealProgress === 1
    NumberAnimation {
        duration: resizeBehavior.ownerPanel.transitionDuration
        easing.type: resizeBehavior.targetValue >= resizeBehavior.targetProperty.object[resizeBehavior.targetProperty.name] ? Easing.OutCubic : Easing.InCubic
    }
}
