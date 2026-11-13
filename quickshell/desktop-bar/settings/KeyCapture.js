.pragma library

function combination(event) {
    const names = {};
    names[Qt.Key_Return] = "RETURN"; names[Qt.Key_Enter] = "RETURN";
    names[Qt.Key_Space] = "SPACE"; names[Qt.Key_Tab] = "TAB";
    names[Qt.Key_Left] = "LEFT"; names[Qt.Key_Right] = "RIGHT";
    names[Qt.Key_Up] = "UP"; names[Qt.Key_Down] = "DOWN";
    names[Qt.Key_Print] = "PRINT"; names[Qt.Key_Delete] = "DELETE";
    names[Qt.Key_Home] = "HOME"; names[Qt.Key_End] = "END";
    names[Qt.Key_PageUp] = "PRIOR"; names[Qt.Key_PageDown] = "NEXT";
    names[Qt.Key_Insert] = "INSERT"; names[Qt.Key_Slash] = "SLASH";
    names[Qt.Key_Comma] = "COMMA"; names[Qt.Key_Period] = "PERIOD";
    names[Qt.Key_Semicolon] = "SEMICOLON"; names[Qt.Key_Equal] = "EQUAL";
    names[Qt.Key_Minus] = "MINUS"; names[Qt.Key_Backslash] = "BACKSLASH";
    names[Qt.Key_BracketLeft] = "BRACKETLEFT"; names[Qt.Key_BracketRight] = "BRACKETRIGHT";
    names[Qt.Key_Apostrophe] = "APOSTROPHE"; names[Qt.Key_QuoteLeft] = "GRAVE";
    names[Qt.Key_VolumeUp] = "XF86AUDIORAISEVOLUME"; names[Qt.Key_VolumeDown] = "XF86AUDIOLOWERVOLUME";
    names[Qt.Key_VolumeMute] = "XF86AUDIOMUTE"; names[Qt.Key_MediaPlay] = "XF86AUDIOPLAY";
    names[Qt.Key_MediaNext] = "XF86AUDIONEXT"; names[Qt.Key_MediaPrevious] = "XF86AUDIOPREV";
    names[Qt.Key_MediaPause] = "XF86AUDIOPAUSE"; names[Qt.Key_MediaTogglePlayPause] = "XF86AUDIOPLAY";
    names[Qt.Key_MicMute] = "XF86AUDIOMICMUTE"; names[Qt.Key_Calculator] = "XF86CALCULATOR";
    names[Qt.Key_MonBrightnessUp] = "XF86MONBRIGHTNESSUP"; names[Qt.Key_MonBrightnessDown] = "XF86MONBRIGHTNESSDOWN";
    names[Qt.Key_KeyboardBrightnessUp] = "XF86KBDBRIGHTNESSUP"; names[Qt.Key_KeyboardBrightnessDown] = "XF86KBDBRIGHTNESSDOWN";
    names[Qt.Key_Question] = "SLASH"; names[Qt.Key_Colon] = "SEMICOLON";
    names[Qt.Key_Plus] = "EQUAL"; names[Qt.Key_Underscore] = "MINUS";
    names[Qt.Key_Less] = "COMMA"; names[Qt.Key_Greater] = "PERIOD";
    names[Qt.Key_BraceLeft] = "BRACKETLEFT"; names[Qt.Key_BraceRight] = "BRACKETRIGHT";
    names[Qt.Key_Bar] = "BACKSLASH"; names[Qt.Key_QuoteDbl] = "APOSTROPHE";
    names[Qt.Key_AsciiTilde] = "GRAVE";
    let key = names[event.key] || "";
    if (event.key >= Qt.Key_A && event.key <= Qt.Key_Z || event.key >= Qt.Key_0 && event.key <= Qt.Key_9)
        key = String.fromCharCode(event.key);
    if (event.key >= Qt.Key_F1 && event.key <= Qt.Key_F35) key = "F" + (event.key - Qt.Key_F1 + 1);
    if (!key) return "";
    const parts = [];
    if (event.modifiers & Qt.MetaModifier) parts.push("SUPER");
    if (event.modifiers & Qt.ControlModifier) parts.push("CTRL");
    if (event.modifiers & Qt.AltModifier) parts.push("ALT");
    if (event.modifiers & Qt.ShiftModifier) parts.push("SHIFT");
    parts.push(key);
    return parts.join(" + ");
}
