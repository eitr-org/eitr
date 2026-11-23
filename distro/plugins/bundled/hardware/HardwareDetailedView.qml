// SPDX-License-Identifier: MIT
// Copyright (c) 2026 The Eitr project
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts

Flickable {
    id: view
    required property var summary
    required property var theme
    readonly property bool twoCol: width >= 360

    clip: true
    boundsBehavior: Flickable.StopAtBounds
    contentWidth: width
    contentHeight: Math.max(height, column.implicitHeight)

    function levelColor(level) {
        if (level === "critical") return theme.crit;
        if (level === "warning") return theme.warn;
        if (level === "normal") return theme.accent;
        return theme.muted;
    }

    ColumnLayout {
        id: column
        width: view.width
        height: Math.max(view.height, implicitHeight)
        spacing: 8

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: view.twoCol ? 2 : 1
            columnSpacing: 8
            rowSpacing: 8

            Repeater {
                model: view.summary.metrics
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    required property int index
                    readonly property bool oddSpan: view.twoCol
                        && view.summary.metrics.length % 2 === 1
                        && index === view.summary.metrics.length - 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.columnSpan: oddSpan ? 2 : 1
                    implicitHeight: 90
                    radius: view.theme.cardRadius
                    color: view.theme.tileFill
                    border.width: 1
                    border.color: view.theme.tileBorder

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 2

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Text {
                                        text: card.modelData.title
                                        textFormat: Text.PlainText
                                        color: view.theme.primary
                                        font.family: view.theme.fontFamily
                                        font.pixelSize: view.theme.bodySize
                                        font.weight: Font.DemiBold
                                    }

                                    Rectangle {
                                        visible: card.modelData.temp !== ""
                                        implicitWidth: tempText.implicitWidth + 10
                                        implicitHeight: tempText.implicitHeight + 4
                                        radius: 4
                                        color: Qt.alpha(view.theme.primary, view.theme.light ? 0.08 : 0.1)

                                        Text {
                                            id: tempText
                                            anchors.centerIn: parent
                                            text: card.modelData.temp
                                            textFormat: Text.PlainText
                                            color: view.theme.secondary
                                            font.family: view.theme.fontFamily
                                            font.pixelSize: Math.max(10, view.theme.captionSize - 1)
                                            font.weight: Font.Medium
                                            font.features: ({"tnum": 1})
                                        }
                                    }

                                    Item { Layout.fillWidth: true }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    visible: card.modelData.primary !== ""
                                    text: card.modelData.primary
                                    textFormat: Text.PlainText
                                    elide: Text.ElideRight
                                    color: view.theme.secondary
                                    font.family: view.theme.fontFamily
                                    font.pixelSize: view.theme.captionSize
                                }
                            }

                            HardwareRing {
                                Layout.preferredWidth: 36
                                Layout.preferredHeight: 36
                                Layout.alignment: Qt.AlignVCenter
                                progress: (card.modelData.usage || 0) / 100
                                hasValue: card.modelData.usage !== null
                                ringColor: view.levelColor(card.modelData.level)
                                trackColor: view.theme.track
                                strokeWidth: 3.5
                                centerText: card.modelData.usageText
                                centerColor: view.theme.primary
                                centerFontFamily: view.theme.fontFamily
                                centerFontPixelSize: 10
                            }
                        }

                        Item { Layout.fillHeight: true }

                        Text {
                            Layout.fillWidth: true
                            visible: card.modelData.detail !== ""
                            text: card.modelData.detail
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: view.theme.muted
                            font.family: view.theme.fontFamily
                            font.pixelSize: Math.max(10, view.theme.captionSize - 1)
                            font.features: ({"tnum": 1})
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: view.twoCol ? 48 : 62
            radius: view.theme.cardRadius
            color: view.theme.tileFill
            border.width: 1
            border.color: view.theme.tileBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                spacing: 10
                visible: view.twoCol

                Column {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1

                    Text {
                        width: parent.width
                        text: "Network"
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.primary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.bodySize
                        font.weight: Font.DemiBold
                    }

                    Text {
                        width: parent.width
                        visible: view.summary.network.connection !== ""
                        text: view.summary.network.connection
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.muted
                        font.family: view.theme.fontFamily
                        font.pixelSize: Math.max(10, view.theme.captionSize - 1)
                    }
                }

                Row {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 14

                    Row {
                        spacing: 5
                        Text {
                            anchors.baseline: downValue.baseline
                            text: "↓"
                            textFormat: Text.PlainText
                            color: view.theme.accent
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                            font.weight: Font.Bold
                        }
                        Text {
                            anchors.baseline: downValue.baseline
                            text: "Download"
                            textFormat: Text.PlainText
                            color: view.theme.muted
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                        }
                        Text {
                            id: downValue
                            text: view.summary.network.downloadText
                            textFormat: Text.PlainText
                            color: view.theme.primary
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                            font.weight: Font.DemiBold
                            font.features: ({"tnum": 1})
                        }
                    }

                    Row {
                        spacing: 5
                        Text {
                            anchors.baseline: upValue.baseline
                            text: "↑"
                            textFormat: Text.PlainText
                            color: view.theme.secondary
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                            font.weight: Font.Bold
                        }
                        Text {
                            anchors.baseline: upValue.baseline
                            text: "Upload"
                            textFormat: Text.PlainText
                            color: view.theme.muted
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                        }
                        Text {
                            id: upValue
                            text: view.summary.network.uploadText
                            textFormat: Text.PlainText
                            color: view.theme.primary
                            font.family: view.theme.fontFamily
                            font.pixelSize: view.theme.captionSize
                            font.weight: Font.DemiBold
                            font.features: ({"tnum": 1})
                        }
                    }
                }
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 3
                visible: !view.twoCol

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Network"
                        textFormat: Text.PlainText
                        color: view.theme.primary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.bodySize
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        visible: view.summary.network.connection !== ""
                        text: view.summary.network.connection
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.muted
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Text {
                        text: "Download  " + view.summary.network.downloadText
                        textFormat: Text.PlainText
                        color: view.theme.secondary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.features: ({"tnum": 1})
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: "Upload  " + view.summary.network.uploadText
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: view.theme.secondary
                        font.family: view.theme.fontFamily
                        font.pixelSize: view.theme.captionSize
                        font.features: ({"tnum": 1})
                    }
                }
            }
        }
    }
}
