.pragma library

var fontFamily = "JetBrainsMono Nerd Font";
var captionSize = 11;
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
// Foreground alpha for subtle panel dividers.
var dividerAlpha = 0.12;

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
