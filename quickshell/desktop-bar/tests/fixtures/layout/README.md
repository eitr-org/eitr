# Layout render fixtures

`layout_render.py` supplies runtime copies, isolated environments, capture paths,
and bounded Quickshell execution. The `.qml.in` files hold the inert visual
fixtures and their geometric assertions; the Python tests supply production
sections and scenario values.

- Notch: 306 cases. Four edges, two palettes, three panel alignments, three
  corner styles and five/ten workspaces, each with media absent/present (288);
  centered panels on four edges with leading/trailing alignment and media
  absent/present (16); hovered weather on top/left (2). Oversized panels are
  included in the trailing, square, ten-workspace cases.
- Bar sections: 64 states. Four edges, four layouts, status open/closed and
  two screen sizes. Every state checks clock centering and panel targets.
- Islands: 12 edge/corner combinations. Each runs six stages covering player
  and capture visibility, content sizes, transparency, reduced motion, gaps,
  auto-hide, input regions and final capture.

The three fixtures contain 14, 5 and 17 QML geometry error checks respectively.
The section suite also compiles the extracted production views through `qmldir`.
