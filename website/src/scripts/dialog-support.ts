// Dialogs open and close declaratively: buttons carry `commandfor` and `command`
// ("show-modal", "close"), and `closedby="any"` lets a click outside close a dialog.
// This module fills both in only where the browser lacks them.

// Invoker Commands are Baseline only since December 2025: older browsers get the polyfill.
if (!('commandForElement' in HTMLButtonElement.prototype)) {
  import('invokers-polyfill');
}

// Safari has no `closedby`: Esc still closes the dialog there, and this adds click outside.
// The pointer position is tested rather than event.target, which is also the dialog for its
// own padding; press and release must both be outside, so a text selection that ends on the
// backdrop does not close it.
if (!('closedBy' in HTMLDialogElement.prototype)) {
  const outside = (event: PointerEvent, dialog: HTMLDialogElement) => {
    const bounds = dialog.getBoundingClientRect();
    return event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
  };
  for (const dialog of document.querySelectorAll<HTMLDialogElement>('dialog[closedby="any"]')) {
    let pressedOutside = false;
    dialog.addEventListener('pointerdown', event => { pressedOutside = outside(event, dialog); });
    dialog.addEventListener('pointerup', event => { if (pressedOutside && outside(event, dialog)) dialog.close(); });
  }
}
