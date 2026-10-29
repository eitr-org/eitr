.pragma library

function tabsForMonitor(clients, monitorId) {
    return clients.filter(client => client.mapped !== false && client.monitor === monitorId).map(client => ({
        address: client.address,
        title: client.title || client.class || "—",
        active: client.focusHistoryID === 0 && !client.hidden,
        pane: !client.hidden
    }));
}
