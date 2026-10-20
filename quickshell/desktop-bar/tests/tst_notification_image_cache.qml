import QtQuick
import QtTest

TestCase {
    id: test
    name: "NotificationImageCache"
    when: windowShown
    width: 100; height: 100
    visible: true
    Image {
        id: retained
        visible: false
        source: Qt.resolvedUrl("thumbnail.png")
        asynchronous: false
        cache: true
    }
    Component {
        id: laterImage
        Image { width: 28; height: 28; asynchronous: true }
    }
    function test_preview_survives_sender_file_cleanup() {
        compare(retained.status, Image.Ready);
        // The Python harness deletes the sender file after this marker.
        console.log("THUMBNAIL_LOADED");
        wait(500);
        var preview = createTemporaryObject(laterImage, test, {source: retained.source});
        tryCompare(preview, "status", Image.Ready);
        compare(preview.implicitWidth, retained.implicitWidth);
        verify(grabImage(preview).width > 0);
    }
}
