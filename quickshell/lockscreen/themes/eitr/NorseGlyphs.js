.pragma library

// Norse clock glyphs in the Eitr wordmark's style: centre-line polylines in a
// 60x100 box, stroked 13 wide with mitred (limit 2) joins and flat ends; no curves.
// The colon is two filled diamonds. Approved by the owner on 2026-10-29.
var box = {width: 60, height: 100, stroke: 13};
var advance = {":": 40, " ": 46};
var defaultAdvance = 72;

var strokes = {
    "0": [[[7, 22], [30, 7], [53, 22], [53, 78], [30, 93], [7, 78], [7, 22], [30, 7]]],
    "1": [[[14, 24], [36, 7], [36, 93]]],
    "2": [[[7, 22], [30, 7], [53, 22], [53, 40], [9, 87], [53, 87]]],
    "3": [[[7, 18], [30, 7], [53, 24], [28, 50], [53, 76], [30, 93], [7, 82]]],
    "4": [[[40, 93], [40, 7], [7, 66], [53, 66]]],
    "5": [[[53, 13], [7, 13], [7, 46], [30, 38], [53, 54], [53, 78], [30, 93], [7, 82]]],
    "6": [[[53, 18], [30, 7], [7, 22], [7, 78], [30, 93], [53, 78], [53, 60], [30, 46], [7, 58]]],
    "7": [[[7, 13], [53, 13], [24, 93]]],
    "8": [[[30, 12], [50, 29], [30, 50], [10, 29], [30, 12], [50, 29]],
          [[30, 50], [53, 71], [30, 88], [7, 71], [30, 50], [53, 71]]],
    "9": [[[7, 82], [30, 93], [53, 78], [53, 22], [30, 7], [7, 22], [7, 40], [30, 54], [53, 42]]],
    "A": [[[7, 93], [30, 7], [53, 93]], [[15, 66], [45, 66]]],
    "P": [[[7, 93], [7, 7], [53, 27], [7, 50]]],
    "M": [[[7, 93], [7, 7], [30, 40], [53, 7], [53, 93]]]
};

var colon = [[[20, 28], [26, 34], [20, 40], [14, 34]], [[20, 62], [26, 68], [20, 74], [14, 68]]];

function width(text) {
    var total = 0;
    for (var index = 0; index < text.length; index++)
        total += advance[text[index]] !== undefined ? advance[text[index]] : defaultAdvance;
    return total - (text.length ? defaultAdvance - box.width : 0);
}
