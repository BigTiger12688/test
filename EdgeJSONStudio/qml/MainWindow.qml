// 主窗口 QML，包含自定义标题栏、导航、工作区和属性面板。
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

ApplicationWindow {
    id: root
    visible: true
    width: 1440
    height: 900
    color: "transparent"
    title: qsTr("锋芒 JSON Studio")

    background: Rectangle {
        anchors.fill: parent
        radius: 16
        color: Qt.application.palette.window
        layer.enabled: true
        layer.blurRadius: 32
        layer.color: Qt.rgba(0.1, 0.1, 0.1, 0.6)
    }

    header: Rectangle {
        id: titleBar
        height: 48
        width: parent.width
        color: Qt.rgba(0.1, 0.1, 0.1, 0.2)
        radius: 16
        Text {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 16
            text: root.title
            font.bold: true
            color: "white"
        }
        MouseArea {
            anchors.fill: parent
            drag.target: root
        }
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            Button {
                text: "—"
                onClicked: root.showMinimized()
            }
            Button {
                text: root.visibility === Window.FullScreen ? "🗗" : "🗖"
                onClicked: root.visibility === Window.FullScreen ? root.showNormal() : root.showFullScreen()
            }
            Button {
                text: "✕"
                onClicked: Qt.quit()
            }
        }
    }

    footer: Rectangle {
        height: 36
        color: Qt.rgba(0.1, 0.1, 0.1, 0.2)
        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            Label { text: qsTr("任务: 空闲") }
            Item { Layout.fillWidth: true }
            Label { text: qsTr("内存: --") }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                id: navigation
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                color: Qt.rgba(0.05, 0.05, 0.08, 0.7)
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    Repeater {
                        model: [qsTr("文件"), qsTr("查询"), qsTr("Schema"), qsTr("对比"), qsTr("工具"), qsTr("历史"), qsTr("插件")]
                        delegate: Button {
                            text: modelData
                            Layout.fillWidth: true
                            onClicked: stackedView.currentIndex = index
                        }
                    }
                }
            }

            Rectangle {
                id: workspace
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Qt.rgba(0.15, 0.15, 0.2, 0.6)
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    TabBar {
                        id: tabBar
                        Layout.fillWidth: true
                        currentIndex: 0
                        TabButton { text: qsTr("编辑器") }
                        TabButton { text: qsTr("树视图") }
                        TabButton { text: qsTr("对比") }
                    }

                    StackLayout {
                        id: stackedView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentIndex: tabBar.currentIndex

                        // 编辑器
                        Rectangle {
                            color: Qt.rgba(0.18, 0.18, 0.24, 0.6)
                            border.color: Qt.rgba(0.2, 0.2, 0.2, 0.6)
                            TextArea {
                                id: editor
                                anchors.fill: parent
                                wrapMode: TextArea.NoWrap
                                placeholderText: qsTr("在此粘贴或打开 JSON 文件...")
                                font.family: "Fira Code"
                            }
                        }

                        // 树视图
                        Rectangle {
                            color: Qt.rgba(0.18, 0.18, 0.24, 0.6)
                            ListView {
                                id: treeView
                                anchors.fill: parent
                                model: treeModel
                                delegate: ItemDelegate {
                                    width: parent.width
                                    text: model.display
                                }
                            }
                        }

                        // 对比视图
                        Rectangle {
                            color: Qt.rgba(0.18, 0.18, 0.24, 0.6)
                            RowLayout {
                                anchors.fill: parent
                                spacing: 8
                                TextArea { Layout.fillWidth: true; Layout.fillHeight: true; text: qsTr("源 A") }
                                TextArea { Layout.fillWidth: true; Layout.fillHeight: true; text: qsTr("源 B") }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: sidePanel
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                color: Qt.rgba(0.08, 0.08, 0.1, 0.6)
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    Label { text: qsTr("属性面板") }
                    TextArea {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        readOnly: true
                        text: qsTr("节点信息将在此显示")
                    }
                }
            }
        }
    }

    ListModel {
        id: treeModel
        ListElement { display: "示例路径: value" }
    }
}
