.pragma library

// The effect's surface may be shown beneath the lock once PAM succeeded...
function eligible(authenticated, reduced, snapshotReady, expired) {
    return authenticated && !reduced && snapshotReady && !expired;
}

// ...and animates only once both lock states report the screen released.
function released(locked, secure) {
    return !locked && !secure;
}
