import QtQuick
import QtQuick.Shapes
import "NorseGlyphs.js" as Glyphs

// The clock in Norse glyphs (NorseGlyphs.js), drawn as vector strokes so they stay
// sharp at any size and take any colour. `glyphHeight` sets the size in pixels.
Item {
    id: clock
    property string text: ""
    property color color: "white"
    property real glyphHeight: 46
    readonly property real unit: glyphHeight / Glyphs.box.height
    implicitWidth: Glyphs.width(text) * unit
    implicitHeight: glyphHeight

    // One SVG path for every stroke, another for the colon's filled diamonds.
    readonly property var paths: {
        let strokes = "", fills = "", x = 0;
        const point = (offset, value) => ((offset + value[0]) * unit) + " " + (value[1] * unit);
        for (const character of text) {
            if (character === ":") {
                for (const dot of Glyphs.colon)
                    fills += "M " + dot.map(value => point(x, value)).join(" L ") + " Z ";
            } else if (Glyphs.strokes[character]) {
                for (const line of Glyphs.strokes[character])
                    strokes += "M " + line.map(value => point(x, value)).join(" L ") + " ";
            }
            x += Glyphs.advance[character] !== undefined ? Glyphs.advance[character] : Glyphs.defaultAdvance;
        }
        return {strokes: strokes, fills: fills};
    }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: clock.color
            fillColor: "transparent"
            strokeWidth: Glyphs.box.stroke * clock.unit
            joinStyle: ShapePath.MiterJoin
            miterLimit: 2
            capStyle: ShapePath.FlatCap
            PathSvg { path: clock.paths.strokes }
        }
        ShapePath {
            strokeColor: "transparent"
            fillColor: clock.color
            PathSvg { path: clock.paths.fills }
        }
    }
}
