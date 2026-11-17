import ".."
import QtQuick

// Observes DesktopData hardware.details and throughput.network only while active.
QtObject {
    id: consumer
    property bool active: false
    property bool observed: false

    function sync() {
        if (active && !observed) {
            observed = true;
            DesktopData.observe("hardware.details", consumer);
            DesktopData.observe("throughput.network", consumer);
        } else if (!active && observed) {
            observed = false;
            DesktopData.releaseOwner(consumer);
        }
    }

    onActiveChanged: sync()
    Component.onCompleted: sync()
    Component.onDestruction: {
        if (observed) {
            observed = false;
            DesktopData.releaseOwner(consumer);
        }
    }

    readonly property var hardware: {
        if (!active) return null;
        const details = DesktopData.topics["hardware.details"];
        const traffic = DesktopData.topics["throughput.network"];
        const summary = (DesktopData.topics["network.summary"] || {}).data || ({});
        const detailsData = details && details.data ? details.data : ({});
        const trafficData = traffic && traffic.data ? traffic.data : ({});
        let connection = "";
        if (summary.wired) connection = "Wired";
        else {
            for (const device of summary.devices || []) {
                const connected = (device.networks || []).find(network => network.connected);
                if (connected && connected.name) { connection = connected.name; break; }
            }
        }
        return {
            status: details ? details.status : "loading",
            error: details ? (details.error || "") : "",
            identity: detailsData.identity || ({}),
            sections: Array.isArray(detailsData.sections) ? detailsData.sections : [],
            network: {
                status: traffic ? traffic.status : "loading",
                download: trafficData.download !== undefined ? trafficData.download : null,
                upload: trafficData.upload !== undefined ? trafficData.upload : null,
                interfaces: Array.isArray(trafficData.interfaces) ? trafficData.interfaces : [],
                connection: connection
            }
        };
    }
}
