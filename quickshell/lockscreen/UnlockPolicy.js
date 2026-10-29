.pragma library

function eligible(authenticated, locked, secure, reduced, snapshotReady, expired) {
    return authenticated && !locked && !secure && !reduced && snapshotReady && !expired;
}
