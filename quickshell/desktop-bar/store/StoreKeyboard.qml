import ".."
import QtQuick

FocusScope {
    required property var catalog
    focus: catalog.opened
    Keys.priority: Keys.AfterItem
    Keys.onPressed: event => {
        if ((event.modifiers & Qt.ControlModifier) && event.key >= Qt.Key_1 && event.key <= Qt.Key_4 && !catalog.busy && !catalog.detail && !catalog.nativeReviewing && !catalog.reviewing && !catalog.removing && !catalog.addingAddress) {
            catalog.kind = catalog.kinds[event.key - Qt.Key_1].id; event.accepted = true; return;
        }
        if (event.key === Qt.Key_Escape) {
            if (catalog.nativeReviewing && catalog.confirmingReview) { event.accepted = true; return; }
            if (catalog.nativeReviewing) { DesktopData.releaseOwner(catalog); catalog.busy = false; catalog.discardReview(); } else if (catalog.addingAddress) { catalog.addingAddress = false; catalog.forceActiveFocus(); } else if (catalog.reviewing || catalog.removing) catalog.cancelSheet(); else if (catalog.managing) catalog.managing = null; else if (catalog.detail) catalog.closeDetail(); else if (catalog.query) catalog.query = ""; else catalog.closeRequested();
            event.accepted = true;
        } else if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && (catalog.nativeReviewing || catalog.reviewing || catalog.removing)) {
            if (catalog.nativeReviewing) catalog.nativeConfirm(); else catalog.confirm(); event.accepted = true;
        } else if (!catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail && !catalog.busy) {
            if (catalog.sidebarFocus) {
                if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) {
                    catalog.navigate(catalog.navigationIndex + (event.key === Qt.Key_Down ? 1 : -1));
                    event.accepted = true; return;
                }
                if (event.key === Qt.Key_Right || event.key === Qt.Key_Tab) {
                    catalog.sidebarFocus = false; catalog.cursor = catalog.navigable.length ? 0 : -1;
                    event.accepted = true; return;
                }
            } else if (event.key === Qt.Key_Left && (catalog.cursor < 0 || catalog.cursor % catalog.columns === 0)) {
                catalog.sidebarFocus = true; catalog.cursor = -1; event.accepted = true; return;
            }
            if ((event.key === Qt.Key_F && (event.modifiers & Qt.ControlModifier)) || (event.key === Qt.Key_Slash && !event.modifiers)) {
                catalog.searchField.forceActiveFocus(); catalog.searchField.selectAll(); event.accepted = true; return;
            }
            if (event.text && event.text !== " " && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)) && !/[\x00-\x1f\x7f]/.test(event.text)) {
                catalog.query += event.text; catalog.sidebarFocus = false; catalog.searchField.forceActiveFocus(); catalog.searchField.cursorPosition = catalog.searchField.text.length;
                event.accepted = true; return;
            }
            const count = catalog.navigable.length;
            let delta = 0;
            if (event.key === Qt.Key_Right) delta = 1;
            if (event.key === Qt.Key_Left) delta = -1;
            if (event.key === Qt.Key_Down) delta = catalog.columns;
            if (event.key === Qt.Key_Up) delta = -catalog.columns;
            if (delta && count) { catalog.cursor = Math.max(0, Math.min(count - 1, catalog.cursor < 0 ? 0 : catalog.cursor + delta)); event.accepted = true; }
            else if (event.key === Qt.Key_Space && catalog.getMore && catalog.cursor >= 0 && catalog.cursor < count) { catalog.toggle(catalog.navigable[catalog.cursor]); event.accepted = true; }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                if (catalog.cursor >= 0 && catalog.cursor < count) catalog.activate(catalog.navigable[catalog.cursor], catalog.isInstalled(catalog.navigable[catalog.cursor]));
                event.accepted = true;
            }
        }
    }
}
