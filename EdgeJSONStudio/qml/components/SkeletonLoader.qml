// 骨架屏组件，用于延迟加载占位。
import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: skeleton
    property int shimmerDuration: 1200
    implicitHeight: 12
    radius: 6
    color: Qt.rgba(1, 1, 1, 0.08)

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.05) }
            GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.12) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.05) }
        }
        SequentialAnimation on x {
            loops: Animation.Infinite
            NumberAnimation { from: -parent.width; to: parent.width; duration: skeleton.shimmerDuration }
        }
    }
}
