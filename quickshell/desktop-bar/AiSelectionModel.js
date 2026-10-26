.pragma library

function restore(settings) {
    return settings && settings.version === 1 && Array.isArray(settings.openedProviders)
        ? settings.openedProviders : [];
}

function toggle(available, opened, name) {
    var current = Array.isArray(opened) ? opened.slice() : [];
    if (available.indexOf(name) === -1) return current;
    return current.indexOf(name) === -1
        ? current.concat([name])
        : current.filter(function(providerName) { return providerName !== name; });
}

function shownProviders(providers) {
    return (providers || []).map(function(provider) {
        return Object.assign({}, provider, {accounts: (provider.accounts || []).filter(function(account) {
            return !account.error && Array.isArray(account.windows) && account.windows.length > 0;
        })});
    }).filter(function(provider) { return provider.accounts.length > 0; });
}

function sharedPlan(accounts) {
    if (!accounts.length) return "";
    var plan = accounts[0].plan || "";
    return accounts.every(function(account) { return (account.plan || "") === plan; }) ? plan : "";
}
