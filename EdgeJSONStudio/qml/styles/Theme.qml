// 主题配置，暴露常用颜色与圆角。
import QtQuick 2.15

QtObject {
    id: theme
    property color background: Qt.rgba(0.12, 0.12, 0.18, 0.9)
    property color accent: Qt.rgba(0.2, 0.6, 0.96, 1)
    property real radius: 12
}
