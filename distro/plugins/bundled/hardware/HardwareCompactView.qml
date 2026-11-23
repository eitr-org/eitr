// SPDX-License-Identifier: MIT
// Copyright (c) 2026 The Eitr project
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts

Item {
    id: view
    required property var summary
    required property var theme
    readonly property bool wide: width >= 400

    function levelColor(level) {
        if (level === "critical") return theme.crit;
        if (level === "warning") return theme.warn;
        if (level === "normal") return theme.accent;
        return theme.muted;
    }

    RowLayout {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.right: parent.right
        visible: view.wide
        spacing: 5

        Repeater {
            model: view.summary.metrics
            delegate: Rectangle {
                id: metricCard
                required property var modelData
                Layout.fillWidth: true
                Layout.minimumWidth: 68
                implicitHeight: 58
                radius: view.theme.cardRadius
                color: view.theme.tileFill
                border.width: 1
                border.color: view.theme.tileBorder

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 6
                    anchors.topMargin: 6
                    anchors.bottomMargin: 6
                    spacing: 5

                    HardwareRing {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        Layout.alignment: Qt.AlignVCenter
                        progress: (metricCard.modelData.usage || 0) / 100
                        hasValue: metricCard.modelData.usage !== null
                        ringColor: view.levelColor(metricCard.modelData.level)
                        trackColor: view.theme.track
                        strokeWidth: 3.0
                    }

                    Column {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 0

                        Text {
                            width: parent.width
                            text: metricCard.modelData.title
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: view.theme.muted
                            font.family: view.theme.fontFamily
                            font.pixelSize: Math.max(10, view.theme.captionSize - 1)
                            font.weight: Font.Medium
                        }

                        Text {
                            width: parent.width
                            text: metricCard.modelData.usageText
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: metricCard.modelData.level === "normal"
                                ? view.theme.primary
                                : view.levelColor(metricCard.modelData.level)
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.bodySize
                            font.weight: Font.DemiBold
                            font.features: ({"tnum": 1})
                        }

                        Text {
                            width: parent.width
                            visible: metricCard.modelData.temp !== ""
                            text: metricCard.modelData.temp
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: view.theme.secondary
                            font.family: view.theme.fontFamily
                            font.pixelSize: 10
                            font.features: ({"tnum": 1})
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: view.summary.metrics.length <= 3 ? 120 : 100
            Layout.minimumWidth: 92
            implicitHeight: 58
            radius: view.theme.cardRadius
            color: view.theme.tileFill
            border.width: 1
            border.color: view.theme.tileBorder

            Column {
                anchors.fill: parent
                anchors.leftMargin: 7
                anchors.rightMargin: 7
                anchors.topMargin: 6
                anchors.bottomMargin: 6
                spacing: 1

                Text {
                    width: parent.width
                    text: "Network"
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: view.theme.muted
                    font.family: view.theme.fontFamily
                    font.pixelSize: Math.max(10, view.theme.captionSize - 1)
                    font.weight: Font.Medium
                }

                RowLayout {
                    width: parent.width
                    spacing: 4
                    Text {
                        text: "↓"
                        textFormat: Text.PlainText
                        color: view.theme.accent
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.weight: Font.Bold
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: view.summary.network.downloadText
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.primary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.weight: Font.DemiBold
                        font.features: ({"tnum": 1})
                    }
                }

                RowLayout {
                    width: parent.width
                    spacing: 4
                    Text {
                        text: "↑"
                        textFormat: Text.PlainText
                        color: view.theme.secondary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.weight: Font.Bold
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: view.summary.network.uploadText
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.primary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.weight: Font.DemiBold
                        font.features: ({"tnum": 1})
                    }
                }
            }
        }
    }

    Grid {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.right: parent.right
        visible: !view.wide
        columns: 2
        columnSpacing: 6
        rowSpacing: 6

        Repeater {
            model: view.summary.metrics
            delegate: Rectangle {
                id: narrowCard
                required property var modelData
                width: (parent.width - 6) / 2
                height: 28
                radius: view.theme.cardRadius
                color: view.theme.tileFill
                border.width: 1
                border.color: view.theme.tileBorder

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 6
                    Text {
                        text: narrowCard.modelData.title
                        textFormat: Text.PlainText
                        color: view.theme.secondary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: narrowCard.modelData.temp !== ""
                            ? narrowCard.modelData.usageText + " · " + narrowCard.modelData.temp
                            : narrowCard.modelData.usageText
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: narrowCard.modelData.level === "normal"
                            ? view.theme.primary
                            : view.levelColor(narrowCard.modelData.level)
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.weight: Font.DemiBold
                        font.features: ({"tnum": 1})
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 26
            radius: view.theme.cardRadius
            color: view.theme.tileFill
            border.width: 1
            border.color: view.theme.tileBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8
                Text {
                    text: "Network"
                    textFormat: Text.PlainText
                    color: view.theme.muted
                    font.family: view.theme.fontFamily
                    font.pixelSize: view.theme.captionSize
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignRight
                    text: "↓ " + view.summary.network.downloadText + "   ↑ " + view.summary.network.uploadText
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: view.theme.primary
                    font.family: view.theme.fontFamily
                    font.pixelSize: view.theme.captionSize
                    font.weight: Font.DemiBold
                    font.features: ({"tnum": 1})
                }
            }
        }
    }
}
