import QtQuick

QtObject {
    id: store
    property bool authenticated: false
    property bool reduced: true
    property var snapshots: ({})
    property int generation: 0
    function resetCapture() { if (!authenticated) { generation++; snapshots = ({}); } }
    function capture(sourceItem, screenName) {
        if (authenticated || reduced || !sourceItem || !screenName) return;
        const attempt = generation;
        try { sourceItem.grabToImage(function(result) {
            if (store.authenticated || store.generation !== attempt || !result || !result.url) return;
            const next = Object.assign({}, store.snapshots);
            next[screenName] = result;
            store.snapshots = next;
        }); } catch (error) { return; }
    }
}
