.pragma library

var fontFamily = "JetBrainsMono Nerd Font";
var captionSize = 12;
var secondarySize = 12;
var bodySize = 13;
var controlSize = 13;
var headingSize = 16;
var padding = 18;
var cornerRadius = 6;
var controlRadius = 4;
// Geometry inset for the fluid bar joins. Content padding follows outer gaps.
var surfaceInset = 14;
var contentGapMultiplier = 2;
// Opacity for secondary text (captions, details, hints). 0.72 keeps dimmed
// foreground text above a 4.5:1 contrast ratio on light theme backgrounds too.
var secondaryTextOpacity = 0.72;

// Headline figures (a panel's one big number) and tabular digits for any value
// that updates in place, so changing numbers do not shift their neighbours.
var figureSize = 22;
var tabularFigures = ({"tnum": 1});
// Foreground alpha for subtle panel dividers.
var dividerAlpha = 0.12;

// WCAG relative luminance of a QML color.
function luminance(color) {
    function channel(value) { return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4); }
    return 0.2126 * channel(color.r) + 0.7152 * channel(color.g) + 0.0722 * channel(color.b);
}

// Whichever of two inks reads better on a filled surface (an accent-filled tile).
function readableInk(surface, first, second) {
    function contrast(a, b) { const high = Math.max(a, b), low = Math.min(a, b); return (high + 0.05) / (low + 0.05); }
    const base = luminance(surface);
    return contrast(base, luminance(first)) >= contrast(base, luminance(second)) ? first : second;
}

function selectionAlpha(selected, hovered) {
    return selected ? 0.18 : hovered ? 0.1 : 0.04;
}

function selectionBorderWidth(selected) {
    return selected ? 0 : 1;
}

var selectionBorderAlpha = 0.15;
var selectionRowHeight = 36;
var selectionRowGap = 6;
var selectionInset = 10;
var selectionTextInset = 36;
var selectionIconSize = 18;
var selectionDetailGap = 2;
var selectionActionInset = 4;
var selectionActionGap = 6;
var selectionActionWidth = 24;
var selectionActionHeight = 24;
// Smallest clickable area for any control, whatever its drawn size.
var minimumHitTarget = 28;
