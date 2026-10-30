# Desktop Bar

Settings and workspace colours follow file/directory watches, including atomic
writes and theme symlink replacement. Monitor/configuration events refresh primary
output and gaps, with a 60 s recovery check. The dock also uses window events and
60 s recovery. Idle Lock toggles report their state over IPC (30 s recovery).
Battery stays at 30 s. WiFi glyphs and Focus share one 10 s status query without
IP/route telemetry; network details refresh only while WiFi or Control Center is
open. Hardware and recording details refresh immediately on opening, then every
2 s while open. Hardware identity and unsupported GPU detection are cached for
the broker session; utilization, frequency, temperatures and disk usage remain live.
One OBS status source refreshes every 2 s while an OBS window/process exists;
open recording details supply that snapshot instead. A startup probe discovers
an existing tray instance; subsequent OBS window events activate observation.
Remote details share the broker’s `remote.status` topic and refresh on opening and every 10 s while observed; closed panels
only read policy availability at startup and policy changes. Weather shares one default forecast across screens with a 15 min cache and schedule.
AI usage refreshes on opening and every 5 min only while a usage menu is open.

Live artwork decodes at the output's pixel dimensions. Aurora runs at 20 Hz on
an empty workspace and 5 Hz behind ordinary windows, retaining fullscreen and
Focus pauses. A one-shot Wayland EGL renderer probe detects llvmpipe/softpipe
and explicit software rendering. Software or unavailable EGL keeps Hyprpaper's
selected still image and skips the live scene. At startup and wallpaper preference
changes, bounded Hyprpaper IPC checks compare each output with its selected image,
with one follow-up check after 3 s. Outputs with missing, failed or stale replies
get the same still image from the bar on the background layer, cropped to fill
and decoded at screen size, including ultrawide variants. This fallback follows
Walker and carousel choices and remains visible in Focus mode and during
transitions; it does not animate the reveal. No polling or machine preference is added.

Login starts Hyprpaper, waits up to 2 s for its IPC endpoint, then starts the bar.
Optional session preparation, Elephant, crash help, cursor sync, nightlight, OSD
and clipboard watchers follow after 4 s. Authentication agents and idle locking
keep their existing startup path. Walker starts/waits for the same Elephant
service when invoked early; its KillMode remains process. Plugin login hooks
start after 12 s and the first automatic update check after 45 s.

The shared Audio/Mic panel includes a live PipeWire input-level meter. Monitoring runs
only while that panel is open; no audio is written to disk. The meter follows the
shared panel theme and shows zero when the selected microphone is muted.
Devices show readable names (`AudioNames.js` turns "GA104 High Definition Audio
Controller Digital Stereo (HDMI) [34GL750]" into "34GL750") with a type glyph. The
current device is a compact picker that unfolds the list; a device's pencil button
renames it, saved by PipeWire node name in the machine-local `eitr/audio-names.json`.

The desktop bar and its native popups follow the current theme. Shared selectable
rows are 36 px tall with 24 px inset action buttons and 4 px edge insets. WiFi
shows connection status beside the network name. Icon buttons have hover-only
backgrounds and spin their glyph while loading. Shared switches use a compact
36 px track.

Tailscale and Streaming panels put the main state in a header switch (connected,
sharing) that runs Walker's Connect/Disconnect or Start/Stop Sharing rows; before
that is possible the header shows the first step instead (Set Up, Sign In). Details
follow, then Tailscale's devices with direct or relayed paths, or Streaming's Start
at login switch and its everyday actions (Pair a Device, Connect to another PC).
Setup and diagnostic rows sit in the "…" menu, and a footer opens Walker's Remote
Access menu. Every control runs the same Walker row through menu-action.py. Streaming uses the Moonlight controller glyph.

Configuration reload errors use a native, padded popup with the bar's live
Theme Color or Blur appearance. Error details are selectable and scroll within
the screen; dismiss with the close button or Escape while focused. Successful
reloads stay quiet. The previous working configuration remains active after a
failed reload. A failure before any configuration loads still uses Quickshell's
built-in fallback, since the custom popup cannot run yet.

## EITR Handbook

Learn > EITR Handbook and SUPER+F1 toggle a centered, non-tiled overlay.
Secure Boot is a chapter inside the Handbook; Security contains actions, not a
terminal documentation viewer. The reader has instant chapter/full-text search,
selectable Markdown, local screenshots, Previous/Next and Alt+Left/Right chapter
navigation. Ctrl+F focuses search; Up/Down and Enter pick a match. Page Up/Down
and Ctrl+Home/End scroll the chapter. Code blocks sit on a foreground-tinted
background. Escape, the close button or SUPER+F1
dismiss it with the shared 320 ms effect; a click beside it does nothing. Its font, corners and
Blur/Theme Color surface follow desktop preferences. Document links can navigate
chapters or open HTTP(S) references on an explicit click, never run commands.

`handbook/chapters.json` selects Markdown sources, including canonical distro
recovery/network/Secure Boot guides. Run `scripts/handbook-build.py` from the
repository after changing them; `--check` detects a stale bundled catalog.
The Shortcuts chapter combines keyboard and mouse references generated from
Learn's `shortcuts.sh` and `mouse-gestures.sh`, not another maintained table.
Rendering Markdown is a build step using `python-markdown`; the installed reader
uses bundled HTML/Markdown and needs no Python Markdown dependency at runtime.
Screenshots must contain only sanitized EITR UI, with no personal screen content.
The bundle is installed with the desktop defaults and needs no network or pager.
Long chapters render as separate selectable rich-text blocks so scrolling does
not lose earlier text. Opening the reader closes bar panels before taking focus.
The screenshot fixture has no input region and uses example colors/data only.
Stop it with `quickshell ipc -p handbook-preview.qml call -- preview stop` from
this directory: it closes the surface before quitting, avoiding Qt's cursor
teardown abort observed when forcibly exiting a visible preview on Qt 6.12.

## Control Center

The chat rail button opens an in-memory conversation with the default assistant.
Enter sends, Shift+Enter adds a line, and Escape returns to the pages. Leaving
chat or closing the panel clears it and cancels the headless request. The helper
sends an allowlisted system summary only on the first turn and never saves chats.

Native panel headings share a small theme-accent rune seal (PanelHeading), and
horizontal section dividers carry a subtle carved diamond (PanelDivider). The
seal replaces a heading's old leading glyph, and a status line under a title is
the heading's subtitle; the Handbook keeps its Eitr logo instead of a seal.
Compact recording controls use only the seal; Calendar retains its date typography.
Weather carries a small seal before the city instead of a heading row, Hardware's
sections show a CPU, GPU, RAM or Storage icon before their titles, and the
workspace style menu has no heading. Decorations follow the
current theme and stay static, with no background animation.

SUPER+, toggles the native control center. Its icon rail selects General,
Plugins, Style, Tools and System; sections fold from their titles (remembered for the
session). Buttons that match a Walker menu row run that row's own command through
`scripts/menu-action.py`, so the two never drift apart. Closing resets it to General. It uses the same DockPanel,
PanelSurface, 320 ms unfolding/folding, padding, and live Blur/Theme Color as the
bar panels. It attaches to the current bar edge (top, bottom, left, or right),
with scrolling when content exceeds the screen. Escape and outside clicks close
it; switching to an existing detail panel closes it before opening that panel.
In full-bar mode it leaves Hyprland's live outer window gap at the opposite
screen edge; vertical bars leave both top and bottom outer gaps.

General includes WiFi/Bluetooth power toggles using the bar's WiFi indicator,
Airplane mode, Idle Lock, Do Not Disturb and Game Mode.
Controls are grouped into Connectivity, Focus & Privacy, Sound, Display, Media,
and Power. Idle Lock, Do Not Disturb and Game Mode share Focus & Privacy. Night Light controls
remain under Settings > Display & Night Light. Media is hidden without a player.
Audio controls share the current PipeWire devices; brightness and power profiles reuse Display's
backend. Airplane mode blocks WiFi/Bluetooth through rfkill and remembers which
radios were originally enabled in a private runtime file. Turning it off restores
only those radios, not Bluetooth that was already disabled. Hardware blocks and
external blocks are never silently overridden. Opening the panel never changes
radio state or starts scanning/audio capture.

Notifications remain exclusively in the dedicated notification panel.
Style groups its settings into Theme & Wallpaper (open initially), Corners, Bar,
Workspaces, Lockscreen, Cursor and Terminal folds. Each open fold encloses its
header and padded options in one subtle surface. Bar groups Layout, Position,
Appearance, Show on, Clock, Media style and Behavior; Behavior holds Auto-hide,
Dock and Reduce motion. Theme & Wallpaper opens the carousels and font picker;
Workspaces includes marker previews. Settings contains
inline keyboard and display/night-light configuration. Keyboard rows include
removal controls, disabled when only one layout remains. General ends
with icon-only Lock, Logout, Suspend, Reboot, and Shutdown actions with tooltips.
Capture launches the existing screenshot, OCR, QR, color-picker, and OBS tools;
selection/capture commands wait for the panel to finish closing first.

DesktopFonts reads the machine-local `~/.config/eitr/font.json` and updates bar
and panel text when it changes. Nerd Font icons retain their dedicated fallback.

Media shows cover art, title/artist, previous/play/next, and elapsed/total time.
Seeking is enabled only when the player supports it. Clicking the bar's animated
indicator (or Media icon on vertical bars) opens a single-background media popup;
the card background is retained only inside the control center. Player selection retains the bar's
existing meeting exclusions and playing-player preference. Media style
(`mediaStyle: bars/line` in `bar-settings.json`) selects eight bars or a smooth
16-point line before the playback controls. Both use a fixed 26 px indicator and
one shared spectrum consumer at 30 fps, including on vertical edges. A gentle
playback animation is used if no audio frame arrives. Reduce motion preserves
live levels without easing and disables decorative fallback motion. The shared
provider's runtime config is independent of the interactive visualizer configuration.

The battery icon and Power section appear only with a present system battery,
never for wireless mice/headsets. Battery displays charge/state, an estimated
remaining/charging time when telemetry is available, and health in its popup.
Saver/Balanced/Performance use the existing laptop-only power-profiles-daemon;
unsupported profiles are disabled. The distro already installs/enables that
daemon on laptops; no desktop power service is added.

OBS controls share compact icon backgrounds and show loading until actions and
the resulting status refresh finish. Starting capture first prepares OBS in
the background, then closes the panel before recording or streaming starts.
The recording dot (just left of the clock while OBS records or streams, where dictation
also shows its level bars) opens RecordingMenu: elapsed
time and size from the shared broker capture details, Pause/Resume, Chapter and Stop, a LIVE
row with Stop for streams, OBS microphone and camera toggles and the scene list.
Stopping a recording sends an Open folder / Copy path notification. During
SUPER+D dictation the dot becomes a red waveform fed by the default microphone's
PipeWire peak (metered only while listening), then pulses while Whisper transcribes.
OBS ships its WebSocket off; the first control turns it on while OBS is closed
(authentication stays required, and a password is generated if OBS has none),
or asks to close OBS once when it is open, since OBS rewrites that file on exit.
The OBS WebSocket password is handed to `obs-cmd` through its
`OBS_WEBSOCKET_URL` environment variable, never on the command line.
Recording options persist in `obs-recording.json`; audio and microphone
switches affect OBS inputs, not system volume. Webcam requires a configured
OBS camera source. The active scene must include visible full-screen monitor
capture. OBS's saved Wayland capture permission still determines the monitor;
changing the primary display may require selecting it again in OBS.

Double-left-click empty bar space to switch between the current transparent
background and opaque theme color. Double-right-click empty space to switch
through Full, Centered, Tabs and Islands layouts. Centered mode shows only the clock
until hovered, then unfolds both icon groups in their existing order. Centered meets the screen edge with square edge ends and the same softly rounded 45° slopes as Tabs on both sides. These slopes rotate with the bar on all four edges and ignore the corner preference; its detached panels still follow that preference. Each side
packs toward the clock with the same 4 px gap between every item and group.
The surface has equal end padding (12 px horizontally, 8 px vertically), so it can be
asymmetric. The clock
stays screen-centered on all four edges; vertical bars unfold up/down. Leaving
starts a 350 ms collapse delay. A pin between media and the clock keeps it open;
pinning persists across reloads/logins. Open panels and drags also keep it expanded.
Panels in this mode use separate rounded surfaces next to the bar, centered along
its axis, with the same 320 ms opening/closing effect. The gap follows Hyprland's
live inner window spacing (opposing insets added together). Gaps outside the
centered strip pass clicks through. Old split preferences migrate to centered.

Islands gives the logo, Overview/workspaces, AI Usage/Hardware/Idle Lock, clock, weather and status controls separate content-sized pills, preserving their order and Full’s icon spacing. Media and capture indicators get pills only while active. The clock stays exactly screen-centred; weather has its own pill beside it. Pills follow Square/Rounded/Extra Rounded, the bar colour/transparency and blur. Pills sit half of Hyprland’s live outer gap from the screen edge, with the full gap between neighbouring pills, on all four edges. The reserved window space includes the pill depth and that half gap; auto-hide reserves none. Gaps and rounded corners pass clicks through. Empty space on each pill supports the usual double-click and drag gestures. Panels use Tabs’ detached rounded surfaces at Full’s positions, with the live inter-window gap and 320 ms reveal. The status group retains Full’s manual show/hide toggle.

Tabs uses a continuous 7 px strip and three content-sized tabs for the left, centre and right groups. Each inner tab end has 4 px of padding measured from its outermost item, including when media is hidden; the centre tab is symmetric around the clock when media and weather are hidden. Weather is hidden until the centre tab is hovered, then slides out after the fixed clock in 320 ms; it retracts after a short hover delay and stays visible while its panel is open. Only the trailing side grows, along the bar axis on every edge, with 4 px after the last visible item. Tabs retain the full bar depth (30 px horizontally), fixed trapezoid joins with straight 45° slopes outside the tab padding. The clock stays exactly screen-centred, including with media visible. Panels float beside the bar on detached rounded surfaces, aligned left, centre or right like Full and inset from screen edges by the outer gap, with the live Hyprland inter-window gap and the same 320 ms reveal as Centered. Gaps pass clicks through; the full tab depth is reserved for windows. Double-right-click cycles Full → Centered → Tabs → Islands → Full. The slopes have subtly softened bends and do not follow the corner preference; screen-edge ends stay square and filled. Tabs always shows all right-side controls without a show/hide arrow.

Drag empty bar space toward top, bottom, left, or right to change its edge; a
preview highlights the destination. The choices persist in `bar-settings.json`.
Walker exposes the same settings under Settings > Style > Desktop Bar > Appearance,
Displays, Layout, and Position. Appearance offers Blur and Theme Color. Displays
shows the bar on the main display only (default) or on every display; then the
focused display's bar answers IPC and shortcuts, each bar highlights its own
display's workspace, and only the main bar shows notification popups.
Learn > Mouse Gestures also lists these gestures and
the desktop wallpaper/theme double clicks. Left/right bars keep the 30 px depth of
top/bottom bars with upright compact controls: the centered clock stacks the hour
over the minutes (with AM/PM for 12-hour time) above a calendar glyph (the date is
in its tooltip), the weather
shows only its icon (the temperature is in its tooltip), and popups open inward.
The `clock` setting in `bar-settings.json` (`12h`, the default, or `24h`), under
Settings > Style > Desktop Bar > Clock and Control Center > Style > Bar, picks the time format
for every edge.
AI Usage, Hardware and Idle Lock sit together after the workspaces; right-hand controls
retain their manual show/hide toggle in Full, Centered and Islands. Tabs keeps them visible without a toggle. Both side groups share 24 px icon slots
and 4 px spacing, with centered alignment on every bar edge. Active workspace
glyphs use the accent color without a filled background in every style; the
style menus show the same markers.
Horizontal bars inset the left icon group by 12 px and the right group by
13 px; the clock remains exactly screen-centered.
The Idle Lock icon follows AI Usage and is a plain switch: a click turns
automatic idle locking on or off, with no panel; its tooltip shows the state.
When on, `hypridle` locks after 15 minutes, turns screens off after 30 and
suspends after 60. Locking now stays in the Control Center, Main > Power and
SUPER+M. Walker's Quick Actions > Idle Lock and the Control Center tile are the same toggle.

The Eitr logo comes first and toggles Control Center beside the bar, using the
same left-side panel placement as Hardware. Centered bars keep panels centered
beside the bar. The Overview icon follows the logo and precedes the workspace
markers on every bar edge. It opens a screen-centered overview of occupied
workspaces only, across monitors, numbered 1–10. Window captures stay in memory and refresh once per second while open;
they are never saved to disk. The workspace layout updates without switching
through desktops. Unsupported captures fall back to application labels. Click
a tile or press 1–9/0 to switch; arrows select a tile and Enter switches to it.
Tiles preserve the workspace monitor's aspect ratio and show its number in the
top-left corner. The current workspace has an accent border around its number;
keyboard selection uses a neutral foreground outline, independent of that marker.
There are no window-count headings. Escape or clicking outside the
tiles dismisses it. Walker's global search for Workspace Overview opens the same view.
SUPER+Tab toggles Overview and is listed in Learn > Shortcuts. The overlay has
no navigation-tip footer; the shortcuts remain available in Learn and this guide.
The overlay always uses the theme-tinted Blur background, even with a Theme
Color bar. Workspace previews enter in order with a 55 ms stagger and a 260 ms
fade/scale/slide; even ten previews finish in about 755 ms. The blurred background
appears before previews. All dismissal paths instantly remove the entire overlay:
workspace selection, Escape, and outside click.
Capture uses Quickshell's
[ScreencopyView](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/ScreencopyView/)
and the compositor's window-export protocol, without additional screenshot tools.

The bar starts with workspaces 1–5. Visiting a higher workspace expands the
sequence through that number, capped at 10: visiting 7 shows 1, 2, 3, 4, 5, 6, 7.
Extra markers disappear when leaving an empty higher workspace: the sequence
ends at the current workspace or highest occupied workspace, with 1–5 always
present. The compositor's existing SUPER+1–9/0 bindings and
monitor assignments remain unchanged. Named/special workspaces are not included
in the numbered overview; external compositor commands can still create them.

Right-click a workspace to choose Dots, Glyph, Numbers or Runes (the default), or use Walker's
Settings > Style > Workspaces menu. Both selectors share the same saved preference.
The menu includes examples; the checkmark identifies the current selection.
The choice is saved in `workspace-style.json`. Selected workspace colors follow
the current theme's accent.

Calendar, Weather, and AI Usage use native Quickshell popups and dismiss on an
outside click or Escape, not pointer movement or focus loss. Calendar and Weather
stay centered on horizontal bars; AI Usage opens beside its left-hand icon.
Panels open above bottom bars and inward from vertical bars. All panels
temporarily use the foreground Overlay layer while visible, including during
closing, so application popups cannot cover their surfaces or steal clicks.
While a notification popup is visible, panels use Top instead: notification
popups stay on Overlay, above panels, so their close buttons receive clicks.
Panel focus grabs allow both the bar and visible notification window; they must
not redirect notification clicks to controls underneath. Grabs require a visible,
opened panel with a live anchor. Losing a plugin anchor during registry reload
closes its panel; reviewed plugin terminals release panel/menu grabs and widget
editing before launch. Approval changes also end widget editing for Walker flows.
The bar returns to its normal Top layer once all panels are closed. Start-group panels
sit flush against the left screen edge (top for vertical bars); end-group panels
sit flush against the right edge (bottom for vertical bars), without a curved
gap at the screen boundary. Calendar and Weather remain screen-centered along
the bar's axis in all four positions.
Panels render inside the bar's Wayland surface, joining it with inward-curved
corners and continuous blur. They unfold over 320 ms from the selected edge
and fold back on outside click, Escape, or icon toggle.
Switching controls finishes the current panel's closing animation before opening
the next panel; rapid clicks select the latest requested panel without overlap.
Content-driven width and height changes use the same 320 ms cubic animation:
AI provider changes, OBS editing, keyboard additions, schedule editing, and
other dynamic panels grow or shrink while staying attached to the bar. Hidden
panels update immediately so resizing does not compete with opening/closing.
Their surface follows the bar's current appearance, including live changes
between the solid theme color and transparency with blur.
Calendar retains its fixed six-row
grid, bottom navigation, year progress, and Left/Right/Up/Down/bracket/T keys.
AI Usage retains the existing backend/cache, refresh-on-open and five-minute
updates while open. Accounts with readable usage appear grouped by assistant;
accounts with errors or no usage windows and assistants without readable accounts
are hidden. Claude Code, Codex and Grok readers use each account’s own configuration.
The provider button includes a shared plan when available. Multiple accounts show
labels above their bars, including individual plans when those differ.
Click a section heading to fold or unfold it; all sections start closed at login.
Long lists scroll within the screen. No readable providers shows an empty message.
Opened sections are saved atomically for the session in
`$XDG_RUNTIME_DIR/eitr-ai-usage-open.json` (version 1, `openedProviders`), surviving
bar reloads but cleared at logout or reboot. The old config preference is ignored
and left untouched. Temporary outages do not discard opened-section choices.
Cached usage appears independently of background requests, so opening never waits
for network access. Unreadable cached accounts are hidden too.
The derived cache is private (0600) and reconciles added/deleted account IDs
before displaying cached results.
Grok is not installed by this feature or added to distro defaults. Its optional
reader follows the official Grok Build auth/billing schema for one personal
first-party OAuth login; API-key/enterprise quotas are not supported. The Grok reader is mock-tested, not verified against a live
Grok account. Provider detection never launches sign-in flows or conversations.
The panel shows only the account limits; limit percentages show usage consumed.
Claude's scoped weekly limits, including Fable when returned by the account,
appear alongside Session and Weekly limits.
The popup grows to fit its content up to the available screen height.
Weather retains the 15-minute refresh,
debounced city search, country-based units, and smaller alternate temperature.
City overrides last only until the popup closes; the bar's default is unchanged.
Escape cancels city search first, then closes Weather. Buttons support Tab/Enter.

The first-login welcome is the Handbook's Getting Started chapter. Above its
text the reader shows setup buttons that only open existing workflows: the theme
and wallpaper carousel (`appearance-picker.sh`), the Display, Keyboard, WiFi and
Bluetooth panels (`show-panel.sh`), and the Shortcuts chapter. A button closes
the Handbook, then its workflow opens. The reader itself runs nothing: it
signals `shell.qml`, which opens the workflow and saves the welcome state. Walker > Learn > Welcome reopens it (`handbook.sh open getting-started`).
The Handbook closes only from its close button, Escape or SUPER + F1; a click
beside it does nothing.
It opens automatically about two seconds after the bar starts, at most once per
Quickshell session, when `scripts/welcome-state.py status` reports it pending.
State lives in `${XDG_STATE_HOME:-~/.local/state}/eitr/`, never in this repository.
A user is eligible only when the Eitr installer's `installed-paths` record exists
there, so existing desktops restored from this backup are not interrupted.
Closing the automatic welcome writes `welcome-dismissed`; the chapter's "Show this
welcome at the next login" switch writes `welcome-pending` (or, turned off,
`welcome-dismissed`) right away. No daemon or service is involved.

The same chapter holds "Offer to report problems when something breaks". It
shares the default-on crash-notification preference with Control Center and
Main > Toggle (`~/.config/eitr/crash-help.json`). The user service
`eitr-crash-help.service` watches new coredump journal records for this UID,
rate-limits each program, and offers AI help, report preparation, ignore and mute.
The bar does not run a second crash watcher. Only an explicit action opens an
assistant or the report workflow; nothing is sent automatically.

The theme carousel supports instant type-to-search within the chosen Dark/Light
category. Search text appears above the previews only while nonempty. Arrows and
Tab navigate matches; Enter applies. Backspace edits the search before returning
to categories, and Escape clears a search before closing. Wallpaper browsing is
unchanged.

Bar tooltips follow the current theme's background and foreground colors.

A compact media strip sits left of the clock without moving the clock's center.
It uses native MPRIS players (excluding the duplicate playerctld proxy), prefers
a playing player, and retains a paused player's title.
Meeting apps and recognized meeting-page URLs/titles are excluded, including
Google Meet, Zoom, Teams, and Webex. Previous, play/pause, and
next controls respect the player's capabilities. The animated indicator shows
the song title on hover and opens the compact media card when clicked.
The indicator follows live system audio through the shared spectrum provider
only while visible and playing. The strip hides without an eligible
player or when there is insufficient space beside the hardware indicators.

WiFi and Bluetooth open themed native popups on the right. Outside clicks,
Escape, or hiding the status icons dismiss them; pointer movement does not.
Inactive workspace tooltips list their open applications by display name, with
duplicates omitted. Current and empty workspaces show no tooltip.
Walker System entries use show-panel.sh to open these same bar popups, including
audio, microphone, keyboard, display, calendar, weather, hardware, and AI usage.
Its allowlist accepts exactly the `panels show` kinds; a test keeps them in sync. Hidden
status icons remain hidden; their popups anchor beside the notification icon.
Walker's Settings > Devices & Input > Keyboard menu is the only place to add or
remove layouts: Add Layout lists the installed XKB languages and variants, and
Delete removes the selected layout. Added layouts persist in
hypr/keyboard-layouts.lua and retain Alt+Shift switching.
Up to four layouts can be configured; duplicate and unknown layouts are rejected.
WiFi defaults to iwd and supports NetworkManager through Settings > Connectivity > Network Backend.
Selection applies after reboot; the panel uses the running backend's D-Bus API for adapter power,
scanning, connection, and disconnection. The compact panel separates remembered
networks from other networks and shows ping, the current WiFi band, IP address
and gateway. Ping probes use two packets to 1.1.1.1 on opening and every 15
seconds while visible.
Band selection remains managed by iwd; no unsupported band controls are shown.
Passwords are passed through stdin,
not command-line arguments. Enterprise PEAP/MSCHAPv2 and TTLS/PAP credentials,
CA certificate and server-domain validation are configured in the panel;
other methods still need advanced provisioning. See `distro/NETWORKING.md`.
Bluetooth uses Quickshell's BlueZ service
for power, discovery, pairing, connecting, and forgetting devices (with confirmation).
Bluetooth groups connected, known, and scanned devices separately; row actions
stay beside the device, with power and Scan in the panel header. The adapter's
machine name is not displayed. The existing Blueman agent handles any pairing-code confirmation dialogs.
Discovery started by the popup stops after 20 seconds or when it closes.
These popups do not change network services or require new packages.

Quickshell owns the desktop notification server. The bell and SUPER+N open its
grouped notification center using the same DockPanel and PanelSurface as the
other controls. Cards use the notification image as their 28 px header icon,
falling back to the app icon (then a bell) if it is absent or cannot load.
Screenshot tools (including Satty) show a body preview instead, keeping the app
icon in the header. Other non-chat apps use body previews for non-square images;
chat/browser images remain header avatars. Previews preserve native size up to
160×120 px in the center or 128×96 px in popups. Image roles are inferred because
apps do not consistently label avatars versus attachments.
Local notification images are decoded immediately and held in memory for the
notification's lifetime, including during DND, so sender cleanup cannot break
later previews. This does not save clipboard-only screenshots to disk.
Images are never duplicated, and the app name is not repeated. Each
app group shows its count and starts with its newest notification over a visual
stack of up to three cards (one front card and two backing layers). The arrow
or clicking the collapsed front card expands the stack without opening the app.
Once expanded, clicking a card invokes its default action normally. The arrow
reveals the full group and collapses it back to the stack; the three-card limit
does not change card styling: expanded cards share the translucent foreground
fill, while the collapsed front masks the overlapping layers behind it. This
background-only transition keeps text and controls readable in blur mode and
does not discard notification history. Single
notifications remain fully readable. Expansion choices persist while the shell
is running, including when new notifications arrive.
Right-clicking the bell toggles Do Not Disturb; the center also
offers Do Not Disturb and Clear All buttons. Popups and the center follow the
bar's live theme-color or transparent/blur appearance. Notifications include
the local arrival date and time beneath their title, in both popups and history;
timestamps stay in memory and are hidden when unavailable. They also include
image/app icons, action buttons, and inline replies when supplied by
the application. Clicking anywhere on a card invokes the application's default
action, such as opening the corresponding chat message, and closes the center
or hides the popup. Apps without a default action still expose any supplied
action buttons; the shell does not guess an action. Dismiss and reply controls
remain independent. Terminal notifications remain filtered out.
Hiding the desktop bar leaves the notification service and popups running;
opening the center while the bar is hidden shows its attached surface temporarily.

Popups group by application, showing only the newest card over up to two backing
layers. New messages update that front card without replaying an entrance fade.
At most four applications appear at once. Hover pauses expiry for the stack;
dismissing or activating the front card hides its whole popup stack, while older
messages remain in notification history. Transient messages can join popup
stacks but remain excluded from history.

Popup timeout hides ordinary notifications while retaining them in history;
transient notifications expire without entering history. Critical notifications
and explicit no-timeout notifications remain until dismissed. Hovering pauses
popup expiry. Do Not Disturb suppresses popups while retaining history.
History stays in memory and survives Quickshell configuration reloads, but not
process restarts; notification contents are never written to a log. Only Do Not
Disturb is persisted in machine-local `notification-settings.json`. The center
retains up to 100 notifications, with periodic pruning. `notifications` IPC
provides `toggle`, `dnd`, `clear`, `clearApp`, and `status`.

Click the Hardware icon to open the shared CPU/GPU/RAM/Storage popup. It refreshes every
two seconds while any hardware panel is visible and closes on an outside click or Escape. CPU load,
cores, frequency and temperature, GPU usage, VRAM and power, and RAM/swap totals
are read locally. Storage identifies only the drive backing `/`, including
encrypted device stacks, and shows installation used/free space. Other drives
are omitted, and Btrfs subvolume mounts are not counted repeatedly.
GPU telemetry uses `nvidia-smi`; temperatures use `sensors`.
Missing optional telemetry is shown as unavailable. No terminal is launched.

Display opens a themed native panel with brightness, Night Light, and active
monitor names, resolutions, and refresh rates. Clicking a display opens its
settings inside its card; their Main display switch makes it the bar's primary
screen (the choice persists in `~/.config/hypr/primary-display`), and the main
display is the fixed reference the others are arranged around.
If that display is unplugged, the bar uses an available screen until it returns.
Until a choice is saved, the bar uses the first connected output listed in the
machine-local `~/.config/hypr/preferred-outputs`, else the largest active
screen. A monitor's settings edit its mode, scale, position (beside another
monitor, aligned start/center/end; remembered so it follows that monitor; the
main display has none) and mirroring, each a collapsed row that opens its
choices. Changes apply and save at once, except a new resolution, refresh rate or HDR toggle,
which reverts after 15 s unless kept (the Keep bar is pinned below the scrolling
panel). Every monitor is pinned to an explicit position, monitors that move
together are parked aside first so no step overlaps, overlapping layouts are
refused, and settings are saved to
`~/.config/hypr/displays.json`. DDC brightness is read after the panel unfolds
and not polled, because each read takes about half a second. **Edit
layout by hand** opens `~/.config/hypr/local.lua`, seeded from
`hypr/local.lua.template` when missing.
HDR-capable monitors expose an HDR switch and a 1.0–2.0× SDR content brightness slider.
Capability comes from CTA EDID PQ/HLG metadata. Generated `displays.lua` enables
Proton Wayland/HDR and DXVK HDR only with connected HDR hardware; the local loader
refreshes it before loading. New sessions and a restarted Steam inherit these defaults.
`cm_auto_hdr = 2` switches fullscreen HDR games to `hdredid` with desktop HDR off;
browsers use HDR only when desktop HDR is on for their monitor. The browser
`no_auto_hdr` window rule preserves colour management while preventing fullscreen
browser surfaces from switching an SDR desktop into HDR. The desktop switch also uses `hdredid`, so Hyprland applies the EDID's peak and black
levels. Turning HDR off writes `cm = "srgb"` and 8-bit explicitly, because
Hyprland keeps the previous preset when the fields are missing.
The Night Light editor saves valid time changes automatically; its Auto switch
enables or disables the schedule, while the main switch remains a manual override.
Brightness uses the laptop backlight when present and the first DDC monitor
otherwise. The SwayOSD overlay for volume and
brightness is generated from the current theme when styles change.
For an Arch installation image, include `brightnessctl` for direct laptop
backlight control and `ddcutil` for external monitors. The control chooses a
usable native backlight before DDC; chassis type is not used to select it.
On laptops, a Power Profile row below brightness switches power-profiles-daemon
between Power Saver, Balanced, and Performance through `scripts/power-profile.py`
(`powerprofilesctl` in argv form). Profiles the hardware lacks are disabled. The
row is hidden without a system battery (`/sys/class/power_supply/BAT*`) or the
daemon, so desktops never see it; no extra bar icon is added.

Volume and Mic open themed native PipeWire popups with live volume/gain sliders,
mute controls, and default output/input device selection. Volume also lists
playback applications with individual sliders and mute controls. Sliders adjust
up to 100% without changing existing higher values until moved. Moving the mouse
away does not dismiss either popup; outside clicks, Escape, or hiding the status
icons do. Long lists scroll within the available screen height. No settings
application is launched, and opening Mic does not start audio capture.

The keyboard icon sits between OBS and Updates. It appears only with two or more layouts
and shows the active one's short code ("US", "BR"; the variant, such as "INT", when two
share a base), with "Keyboard · <layout name>" on hover. Its panel and
the Control Center switch layouts and link to Walker to add or remove them. They follow
Alt+Shift through Hyprland's activelayout event and reload after config reloads. Weather keeps the city's local temperature unit
as the main reading, with a smaller equivalent in the other unit alongside it.

Install Quickshell:

```sh
sudo pacman -S quickshell
```

Run the preview:

```sh
eitr-shell desktop-bar --daemonize
```

Toggle the bar:

```sh
eitr-run walker/scripts/actions/toggle/desktop-bar.sh
```

Stop the bar:

```sh
eitr-shell desktop-bar kill
```

## Panel Style

Control Center > Style > Corners and Walker > Settings > Style > Corners select Square,
Rounded (1.5× the base radii, halfway to Extra Rounded) or Extra Rounded. The machine-local preference is
`~/.config/eitr/style.json`. The styles, their radius scale and Hyprland window
rounding are defined once in `corner-styles.json`, which `desktop-style.py`,
DesktopStyle, the Walker style generator and `hyprland.lua` read; add or tune a
style there, with its one-line description in `elephant/menus/corners.lua`.
Choosing a style from Walker calls `quickshell ipc … style reload`, so
DesktopStyle updates Eitr bar/panel/card/control corners live without polling;
the bar's theme refresh supplies the critical-notification color. Third-party applications retain their own internal widget
styles; circular indicators and slider thumbs remain circular. Cards get a subtle
inward-fading glow without a hard outline or exterior shadow: the theme accent for
normal urgency, color1 for critical, and none for subdued low-priority cards, in
popups and history.

Attached panel backgrounds retain the fluid bar join. Their inner content uses
twice the live Hyprland outer gaps on all four sides; per-panel content containers do
not add a second outer margin. Bottom bars mirror the same content inset without
detaching the panel from the bar.

`PanelStyle.js` defines the shared font family, utility heading (16 px),
body/control text (13 px), secondary text and captions (12 px), padding, corner radii
(`controlRadius` for rows, inputs, and buttons), the divider alpha
(`dividerAlpha`), and `surfaceInset`: the 14 px geometry inset of the fluid
bar joins. Content padding follows the live outer gaps; content-sized panels
add `verticalContentInset` around their content instead of duplicate margins.
Bar glyphs and the appearance picker use the same font family.
Calendar dates, weather temperatures, and glyphs retain purpose-specific sizes.
Compact selectors retain their smaller padding; full panels use 18 px.
Notification CSS uses the same font family, with larger text for message content.

## Panel guideline

Every panel follows the same rules, so a new one feels like the others:

- **One number first.** A panel that reports values leads with the one that
  matters, as a large figure (`figureSize`); details unfold on click
  (Hardware shows each component's usage and opens its rows).
- **Readable names.** Show what people recognise, not driver strings, and let
  them rename what they own (audio devices).
- **State by colour.** An on/off tile fills with the theme accent when on
  (`ControlCenterTile` `toggle`); its ink is whichever of foreground or
  background reads better on the accent (`readableInk`). No "On"/"Off" subtitles.
  One-shot actions are compact buttons, not tiles.
- **One primary header control.** Rarer actions go in the `PanelMoreButton`
  "…" menu with their names; session-ending power actions sit behind one
  labelled Power button, with Lock kept one click away.
- **A footer to go further.** When a panel has a fuller place (Walker settings,
  a monitor app), it ends with a `PanelFooterLink` row such as "Network Settings…".
- **Three text sizes.** 16 px headings, 13 px body, 12 px secondary text and
  captions. Dimmed text uses `secondaryTextOpacity` (0.72), which stays above a
  4.5:1 contrast ratio on light themes too. Numbers that change in place use
  `tabularFigures`.
- **Comfortable targets.** Drawn controls may be compact, but every button
  takes clicks over at least `minimumHitTarget` (28 px), and keyboard focus
  shows the same fill as hover.
- **Refresh on open.** Panels load fresh data when they open and on their own
  timers; there are no refresh buttons. `PanelLoadingIndicator` spins in the
  header only while loading (or scanning) and disappears when done.
- **Nothing heavy during the unfold.** Starting helper processes blocks rendering
  for a moment, and rebuilding content re-lays out the panel, so either one during
  the 320 ms unfold makes it jump. Data passed to `updateContent`/`applySnapshot`
  while a panel unfolds waits until it has finished. Panels that start several
  helpers on opening (Control Center, Display) start them on `DockPanel.revealed`
  instead, and fetch once in the background after the bar starts so the first
  opening already has data.
- **Dividers between groups.** A subtle `PanelDivider` separates a panel's
  groups (devices, sections, options); Control Center sections carry a label.
- **Walker descriptions fit.** Row descriptions stay within 72 characters in
  every language; `walker/tests/test_menu_structure.py` enforces it.

## Visual plugins

Plugin runtime diagnostics appear in **Control Center > Plugins**: an error state, the first message and **View error details**, with one-click disabling retained. The session list is bounded and de-duplicated; file URLs identify plugin QML warnings and exceptions. Messages without plugin URLs cannot be attributed reliably. Plugins run inside the desktop with its permissions, without a sandbox; install only trusted plugins. The existing installation review shows the full-permissions warning, including for plugins outside the official collection. See `distro/PLUGINS.md` for diagnostic limits.

General ends with a labelled Plugins area for approved schema v2 tile components.
PluginArea queries approved placements; PluginComponent owns checked asynchronous
loading, the style/data API, shared tile rows and inline failure fallback.
Placements prefetch before opening and refresh on registry changes. Panel subviews
use an intrinsic height with scrolling above 360 px; Back and Escape return to tiles.
Three component failures disable a plugin's visual components persistently;
`eitr plugin enable-ui ID` and the Re-enable visuals action reset them. QML runs inside
the bar and is not a sandbox or crash boundary. See `distro/PLUGINS.md` for the
manifest, API contract, review behavior and runtime limitations.


PluginRegistry prefetches approved declarations and opt-in placements once, using
JsonState to avoid rebuilding unchanged entries. PluginArea, PluginDesktop and
PluginBarItems share it. The dedicated Plugins page groups management controls by plugin. PluginManagement uses shared 36 px rows
with inset 24 px actions, declared titles and plugin/monitor display names. It exposes monitor-specific widget actions,
bar placement and failure reset. PluginDesktop maps each placed widget to a
Bottom-layer window by default, or an opt-in click-through Top-layer window; PluginWidget
adds explicit edit handles. PluginGeometry snaps and clamps logical geometry to
Hyprland's monitor reserved area. Missing monitors retain their saved entries.
`eitr/plugin-placements.json` is an ignored machine-local preference, version 2 (version 1 migrates on read),
with widgets keyed by plugin/id/monitor and bar items by plugin/id. Edit mode is
session-only. PluginBarItems uses fixed 24 px slots and 4 px spacing supplied by
the shell's shared metrics, inside the right group on every edge. PluginPanel
uses ThemedPopup/DockPanel for attached or detached surfaces and dismissal.

SpectrumProvider owns one on-demand cava process for media and plugins;
SpectrumConsumer resamples and caps delivery. PluginComponent supervises declared
line streams through eitr_plugin_stream.py. Placement v2 stores aboveWindows;
Top-layer widgets pass clicks through outside edit mode and hide on fullscreen
monitors. See distro/PLUGINS.md for API limits and trust boundaries.


The Plugins page prefetches installed metadata through PluginRegistry and
JsonState alongside declarations and placements. It offers enable/disable,
reviewed Add/Update/Remove, icon/preview cards and per-plugin visual controls.
Widget options are shared by the page and right-click popup (PluginWidgetMenu).
PluginWidget uses monitor-local pointer coordinates; PluginDesktop keeps motion
unsnapped until release, raises edit surfaces, and saves fitted geometry through
the locked placement helper. Transparent widgets use a separate unblurred layer
namespace; their edit outline remains visible. Edit widgets toggles all widgets
interactive; Done and Escape end editing. Above-window widgets expose their
options in the Plugins page while click-through.

Plugin appearance belongs to its author. Widgets and panels default to no host surface; panel surfaces and theme helpers are opt-in. Tiles default to the Eitr row, with `look: "custom"` providing a full-slot canvas. See `distro/PLUGINS.md`.

Auto-hide is optional in Settings > Style > Desktop Bar and Control Center > Style. The
strip slides out in 320 ms, retaining a one-pixel edge input region. Panels,
pending popups, notification toasts, Overview and dragging hold it open; a 350 ms leave delay precedes
hiding. A hidden bar reserves no space. The preference is separate from the
Centered pin and applies independently to each displayed bar.

## Edge dock

Touch the screen edge opposite the bar to reveal the application dock. It unfolds from that edge, its straight sides meeting the edge, over windows without moving or resizing them and hides 350 ms after the pointer leaves, with the shared 320 ms motion (instant with Reduce motion). It appears on the main screen, or on every screen when Displays is set to all, and never reveals over a fullscreen window.

The dock shows pinned apps first, followed by other open applications in Hyprland’s window order. Each 36 px icon slot has a 6 px gap and uses the application’s desktop icon, with a glyph fallback; Eitr’s own task and menu terminals share one Eitr logo icon. Dots below an icon count its windows, up to three, and dim when none is on the current workspace of that screen. Hover for its name and window count. Click to focus its most recently used window (including switching workspace); click again to move to its next window. Middle-click closes the most recent window. Long lists scroll along the dock. The surface follows Blur/Theme Color and the corner preference.

**Dock** in **Settings > Style > Desktop Bar** and **Control Center > Style > Bar** turns it off or on. The `dock` setting in `bar-settings.json` defaults to `"yes"`. There is no dock shortcut.

Pinned apps stay at full opacity with no dots when closed; click one to launch it in its own application scope. Right-click an icon for Keep in Dock / Remove from Dock, New Window (when a desktop entry is available), and Close or Close All Windows. Escape or a click outside dismisses the menu. Apps without a desktop entry cannot be pinned.

Drag icons along the dock to reorder pins. Drag a running app into the pinned section to keep it there, or drag a pin past that section to remove it. Other icons make room with a short animation (instant with Reduce motion); unpinned apps retain Hyprland’s window order. A thin divider separates pins from other running apps only when both sections contain apps. Menus and drags keep the dock revealed.

Pins are desktop-entry IDs stored in order in the machine-local `quickshell/desktop-bar/dock-pins.json` under `$XDG_CONFIG_HOME` (normally `~/.config`), written atomically. Fresh installs have no pins. Window matching uses desktop-entry IDs, StartupWMClass and application classes.


## Motion and panel smoothness audit

Reduce motion is off by default. Settings > Style > Desktop Bar > Reduce motion and
Control Center > Style > Bar share `bar-settings.json` (`reduceMotion: yes/no`).
`DesktopStyle.motionDuration()` owns the policy: normal durations/easing are
unchanged, reduced durations are zero. DockPanel unfold/fold/resize, notification
group transitions, Handbook, Overview, carousel, bar expansion/auto-hide, markers,
button effects and meters use it. Infinite indicators stop under reduced motion;
loading state remains visible. Realm screenshot flashes and Fenrir are suppressed.
Data refresh, focus, notification-expiry and pointer-leave timers are unchanged.

Inventory: `shell.qml`'s `dockPanels`, `showKind()`/`panels` IPC, Control Center
page routing, `qmldir`, and auxiliary popup/overlay types. `brightness`/`display`
and `volume`/`mic` are aliases of the same panels. Walker uses these same IPC
kinds; it does not instantiate another copy.

Models stay warm through background status prefetch and `JsonState.changed` guards.
Opening starts fresh queries immediately. Panels with asynchronous data wait for
the first result and a layout turn, capped at 100 ms, before their single 320 ms
unfold. Retained/static panels begin on the next layout turn. `applySnapshot`
applies changed data immediately and signals readiness; `updateContent` does the
same for parsers updating scalar or native identity-guarded properties. There is
no after-reveal data queue or geometry latch. A size target received during the
unfold animates from the current size over the remaining reveal time, so both
finish together. Ordinary size changes after opening retain the 320 ms resize.
Native QObject lists compare identities rather than serializing service objects.

Every entry below **needs live check** on all four edges, Full/Centered/Tabs/Islands,
both palettes, cold/warm cache and slow providers. Offscreen checks cannot prove
compositor blur, D-Bus, GPU capture, DDC or real hardware performance.

| Panel / popup and routes | Opening work found | Fix / audited decision | Status |
| --- | --- | --- | --- |
| Control Center — General (`center`) | Multiple status processes and plugin activation | Warm prefetch; immediate open queries/results; guarded snapshots; plugins activate before reveal | needs live check |
| Control Center — Style | Cursor/lockscreen list queries; theme/font glyph layout | Prefetch style choices; apply query results before/during the shared reveal; fixed text roles | needs live check |
| Control Center — Tools | Static action rows; recording routes | Retained content; no open-time model query; actions still run only on click | needs live check |
| Control Center — System | Channel, keyboard, monitor and policy data | Immediate channel/policy queries; existing display/keyboard guards; retained page content | needs live check |
| Control Center — Plugins and details | Installed registry model, icon/preview decoding | Registry already prefetches and guards changes; fixed icon slots now decode asynchronously; source URL/folder shown | needs live check |
| Control Center — Quick chat | Assistant status; conversation delegates | Status query immediate and guarded; no request until Send; closing still clears memory | needs live check |
| AI Usage (`ai`) | Cache + fresh query replaced provider model on every open | Startup cache; immediate fresh query/results; guarded usage assignment | needs live check |
| Hardware (`hardware`) | Shared broker telemetry snapshot | Subscribe on open; immediate refresh; guarded section snapshot | needs live check |
| WiFi (`wifi`) | Status process replaced devices; ping could follow during reveal | Shared cached status; refresh on open and visible-only ping; guarded device snapshot; QR generated only after explicit Share | needs live check |
| Bluetooth (`bluetooth`) | Service-backed section arrays recreated when devices changed | Apply sections immediately and compare device identities; scan remains explicit and stops on close | needs live check |
| Display (`brightness`, `display`) and monitor editor | Status/monitor/settings/nightlight/power JSON; slow DDC read | Existing prefetch/JsonState retained; immediate query parsers and open DDC read; shared size retargeting | needs live check |
| Audio (`volume`, `mic`) and device picker | PipeWire node list, scroll positioning, microphone peak monitor | Apply node-list identity changes and initial scroll immediately; peak monitor activates after reveal; no recording is started | needs live check |
| Tailscale (`tailscale`) | Shared remote-status process and facts/actions model | Prefetch shared status; guard equality; panel snapshots and refresh apply before/during reveal | needs live check |
| Streaming (`streaming`) | Same remote-status process and facts/actions model | Same shared owner and immediate guarded panel snapshot; no connection action on open | needs live check |
| Keyboard (`keyboard`) | Layout process recreated all rows | Existing startup query retained; immediate open refresh/parse; guarded layout snapshot | needs live check |
| OBS (`obs`) | Status/options query replaced controls; periodic poll | Existing startup/poll retained; immediate parsers and open refresh; guarded status/options | needs live check |
| Recording / Streaming status (`recording`) | Details query rebuilt scenes and device controls | Warm background details; immediate open refresh/parse; guarded details; elapsed clock remains live | needs live check |
| Calendar (`calendar`) | Watched reminder/event files reparsed; subscription sync on open | Immediate parsing and guards on both lists; retain six fixed calendar weeks; sync runs outside GUI and watched results apply immediately | needs live check |
| Weather (`weather`) and city search | Weather JSON replaced forecast model; async city search | Warm background weather; immediate request and parsing; guard weather snapshot; city search remains explicit/debounced; shared size retargeting | needs live check |
| Notifications center (`notifications`) | Already-retained service groups and in-memory images | No open-time process; fixed panel height; shared reveal and group duration policy | needs live check |
| Notification toasts / grouped cards | Arrival-driven delegates and image loading | Existing decoded-image cache and async fixed image slots retained; group transitions use central motion policy | needs live check |
| Workspace style (`workspace`) | Static choices and font metrics | Retained delegates/TextMetrics; shared size retargeting during reveal; marker animations honor motion policy | needs live check |
| Media (`media`) | MPRIS seek timer and cover art | Existing async fixed-size cover retained; no process/model load on open | needs live check |
| Battery / Power (`battery`) | Power-profile refresh | Immediate refresh; existing shared power data and fixed control metrics | needs live check |
| Plugin panels (`PluginPanel`) and General subviews | Author QML/data loader activates on opening | Asynchronous PluginComponent retained; host activates before reveal and reports implicit-height readiness; arbitrary author code still requires profiling | needs live check |
| Overview (`overview`) | Synchronous grid Loader, toplevel refresh and capture on open | Retain grid with asynchronous construction; defer refresh and captures until entrances finish; async sized wallpaper; dismissal remains instant | needs live check |
| Theme / Wallpaper carousel | Re-query, model clear and image cache disabled | Reuse per-mode catalog; guard equal results; async bounded image placeholders; preserve uncached artwork across theme changes; motion policy covers navigation | needs live check |
| Handbook / first-login welcome | Reload/parse complete catalog on every open | Existing startup/watch loading retained; remove redundant open reload; guard and defer changed catalogs; figures already async | needs live check |
| Time picker (`timepicker`) | Fixed controls; writer only on confirmation | No open-time process or image load; already instant | needs live check |
| Header More actions, widget options, device/layout choices, power confirmation rows | Retained small action lists | No background load on open; shared button images async; existing instant popup behavior retained | needs live check |
| Bar/tool/workspace tooltips | Text-only popup and font metrics | Fixed font roles, bounded width; existing delay and instant display retained; no open-time process | needs live check |
| Reload-error popup | Lazy text-only error surface | Deliberately lazy to survive shell errors; no heavy model or image work, already instant | needs live check |

Offscreen regression: `PanelMotionTests` supplies a result before revealing and
a size-changing result during the unfold, then repeats equivalent snapshots every
20 ms. It requires one continuous motion, guarded equal-model assignments, final
size at reveal completion, and no second size animation afterwards. Reduced
motion applies both results immediately without animation. Assertions in frame
callbacks are retained and cause a nonzero exit, rather than merely logging QML
exceptions. The late-result fixture reaches final size in about 342 ms including
its 20 ms preparation, with one motion.

Run `EITR_PANEL_REVIEW_RENDERS=OUTPUT bash tools/check.sh python-tests` for the
shared regression captures. Run
`EITR_PANEL_REVIEW_RENDERS=OUTPUT python3 quickshell/desktop-bar/tests/render_panel_motion.py`
for isolated per-panel measurements and dark/light captures. This harness loads
actual panel components with mock services and no live helper scripts or D-Bus.
It samples every 16 ms and fails on a second motion or size change after reveal.
The review renders are outside the checkout in `../panels-shots/`.

Per-panel results below include preparation and the first sampled final frame;
the configured unfold duration is 320 ms. These are software-renderer fixture
measurements, not live provider/hardware latency claims.

| Panel / route | Time to final size, dark / light (ms) | Motions |
| --- | --- | --- |
| AiUsageMenu | 321 / 322 | 1 |
| SystemMonitorMenu | 330 / 329 | 1 |
| WifiMenu | 329 / 329 | 1 |
| BluetoothMenu | 321 / 321 | 1 |
| BrightnessMenu | 330 / 330 | 1 |
| AudioMenu | 321 / 321 | 1 |
| KeyboardLayoutMenu | 329 / 328 | 1 |
| ObsMenu | 328 / 329 | 1 |
| RecordingMenu | 330 / 331 | 1 |
| WeatherMenu | 322 / 322 | 1 |
| CalendarMenu | 322 / 322 | 1 |
| RemoteAccessMenu | 421 / 421 | 1 |
| BatteryMenu | 322 / 321 | 1 |
| WorkspaceStyleMenu | 320 / 321 | 1 |
| NotificationCenter | 321 / 321 | 1 |
| PluginPanel | 322 / 322 | 1 |
| ControlCenter-style | 335 / 332 | 1 |
| ControlCenter-plugins | 329 / 330 | 1 |
| ControlCenter-plugin-details | 331 / 330 | 1 |
| MediaMenu | 322 / 321 | 1 |
| AudioMenu-mic | 321 / 322 | 1 |
| RemoteAccessMenu-streaming | 422 / 422 | 1 |
| ControlCenter-general | 332 / 340 | 1 |
| ControlCenter-tools | 336 / 337 | 1 |
| ControlCenter-system | 348 / 329 | 1 |

## Focus preset

Settings > Style > Focus, Control Center > Style > Focus and `eitr focus on|off|status`
share a machine-local preference. Focus uses native Hyprland groups with up to
four panes per monitor and a thin Quickshell tab strip. Turning it off restores
the normal bar and effects, spreading windows two per workspace. See the
[Focus Handbook chapter](handbook/content/focus.md) for keys, monitor behavior and recovery.

### Desktop data ownership

One `NetworkService` in the shell supplies every screen, bar layout and Focus
strip. The registered `DesktopData` singleton owns one `scripts/bar-data.py` child
for the entire shell. The broker imports the existing WiFi CLI adapters once into a pool of at most three
threads and schedules the summary at startup and every
10 seconds. WiFi menus and Control Center hold detail observer tokens while
open; one shared reader refreshes on opening and every 2 seconds. Only visible
WiFi menus hold latency tokens, for one probe on opening/connection and every
15 seconds. Closing or destroying a consumer releases its tokens idempotently;
zero demand stops the corresponding reader and timer. Cached details appear
immediately, with fresh panel content applied through the popup reveal guard.
Refreshes coalesce to one running read and one pending refresh. Each topic keeps
its last good data, timestamp, and loading/ready/unavailable/stale/error status.
Network actions share a busy guard across screens. QR generation has its own
guard; credentials and QR results go only to the requesting panel and are not
part of shared snapshots. The existing iwd and NetworkManager readers and action
helpers remain the backend authority.

The version 1 transport uses bounded newline-delimited JSON on stdin/stdout;
Adapter logs never enter protocol stdout. Requests use `subscribe`/`unsubscribe`
with a topic and unique observer token, or `refresh` with a request ID. Topics are
`network.summary`, `network.details`, `network.latency`, `capture.summary`,
`capture.details`, `capture.options`, `power.battery`, `power.profile`,
`power.radios`, `display.topology`, `display.settings`, `display.brightness`,
`display.nightlight`, `hardware.details`, `remote.availability`, `remote.status`,
`weather.default`, `ai.usage` and `updates.status`. State snapshots carry
`v`, `op`, `topic`, `token`, `id`, `epoch`, per-topic `seq`, `status`, `data`, and
`ageMs` (null before a successful read). A `hello` establishes the epoch; reconnect
replays current tokens and sends full snapshots. Old epoch/sequence results are
ignored. Reads have deadlines and D-Bus calls time out within 5 seconds. A timed-out
read keeps its topic occupied until its thread returns. Scheduling sleeps until
the next due read or a demand change.

Broker exit retains good data as stale and retries with capped exponential delay
and jitter, stopping after six retries. `eitr-shell desktop-bar ipc call -- data retry`
allows explicit recovery; `eitr-shell desktop-bar ipc call -- data status` returns topic
ages, error codes, in-flight/pending counts, observers and restart count, without
network identities or raw data. Each status call requests diagnostics once and
returns the diagnostics received from the previous call; there is no status polling. Native desktop controls remain independent.
Network actions use request IDs and a bounded ordered broker queue and share serialization with power/radio writes. Busy state is shared across screens; results and error codes return only to the originating panel. Each helper receives credentials on stdin and is killed and reaped at its operation deadline (enterprise: 120 s). Timeout or broker death means outcome unknown: reconcile state and retry explicitly. Writes are never replayed. QR remains an ephemeral helper outside the broker.

### Capture data ownership

The singleton `ObsStatus` adapts `capture.summary`, `capture.details`, and
`capture.options` from the same `DesktopData` broker. Imported OBS reads run in
the bounded worker pool; they do not launch Python per refresh. Summary checks
run at startup, on window changes and explicit refresh, then every 2 seconds
only while an OBS window or process is known to exist. Recording panels share
one 2-second details reader while open; details also update the summary, so no
parallel summary check runs. Options refresh on open or after writes, without
periodic polling. Unavailable reads retain last-good data with controls disabled;
unknown status never becomes a confirmed stopped state.

Capture actions, including option writes and preparation, use request IDs and
one bounded ordered domain queue. Busy state is shared across screens; results
return to the requesting controller. The existing prepare/close/reveal delay
before starting capture is preserved. The OBS stop command keeps its 30-second
deadline, within a 45-second total budget for notification and idle cleanup.
Timeouts and broker death leave an unknown outcome, require state reconciliation,
and never replay writes. `obs-control.py` remains the standalone CLI for Walker,
screenshots and shortcuts, with the same output and translation behavior.
`eitr-shell desktop-bar ipc call -- data status` includes capture topic diagnostics
without recording paths, scene names or raw OBS data.

### Shared battery, power and radios

`PowerService` consumes `power.battery`, `power.profile` and `power.radios` from
DesktopData. Imported adapters share the bounded worker pool and per-call deadlines;
the standalone battery, power-profile and airplane CLIs retain their output.
The broker derives system-battery capability once with `eitr_battery`; peripheral
batteries do not enable laptop controls. Battery reads retain the 30-second cadence.
Profile reads run every 3 seconds while Brightness is open, otherwise every 5 seconds
while Battery or Control Center is open. Radio reads run every 5 seconds only while
Control Center is open. Multiple screens share these reads and release demand on
close/destruction. One shared read preserves the existing 8-second startup warmup. The shell alone presents the existing low-battery hook at 15%
and warnings at 10% and 5%, including after suspend gaps.
Profile and airplane writes have request IDs, ordered serialization with network
writes and originating-panel results. They keep the existing helpers and privilege
boundaries. Unknown outcomes require a successful refresh and explicit retry;
writes are never replayed. Data status includes all three power topics.


`DisplayService` shares `display.topology`, `display.settings`,
`display.brightness` and `display.nightlight` through the same broker. The display
domain loads on first demand inside the bounded worker pool; import and read
failures affect the requested topic without preventing other domains from starting. Hyprland
monitor/configuration events and the watched primary/preferred output files
refresh topology; shell geometry, desktop widgets and display controls use one
monitor snapshot, including reserved edges. The saved main display, preferred
connected output and largest-display fallback order is unchanged.
Brightness and night-light reads retain their three-second interval only while
observed; startup warms each once. DDC brightness is never periodically polled.
Slider writes keep the latest pending value and suspend read demand until the
write queue drains. Panel actions and display trials still use their existing
helpers; the independent trial rollback survives bar or broker exit. The
standalone display and hypridle brightness commands remain available.


Hardware read ownership
-----------------------

`hardware.details` owns the hardware sampler and session identity in the broker.
The Hardware popup, including Control Center's Hardware entry, subscribes on open
and releases on close or destruction. Opening refreshes immediately; multiple
screens share one 2-second sampler, with no periodic sampling after the last
observer closes. An already-admitted read may finish; a closed generation cannot
publish its result. Identity discovery is retained across opens, including failed or timed-out
GPU probes. The popup keeps its last good sections on failure and uses the existing
translated unavailable message. `system-details.py` remains an independent CLI with
its existing JSON and optional stdin identity contract.

All domain adapters load lazily on demand inside the bounded worker pool, under
the read deadline. Each domain can occupy at most two of the three pool
workers, so one slow domain cannot fill the pool with sibling topics. A failed or slow import marks only that topic unavailable;
it cannot prevent broker startup or another domain's reads. Capture's ordered
action controller belongs to the broker, separate from its lazy read adapter.
`eitr-shell desktop-bar ipc call -- data status` includes hardware demand,
freshness and read errors without scheduling periodic diagnostics.

### Weather and AI data ownership

`weather.default` shares the weather calculation and compatible disk cache with
`weather-status.sh` and `weather-popup.py`. All bar screens and default-location
panels consume it; the broker schedules one 15-minute reader. Opening a panel
checks the same 15-minute cache. City search and alternate forecasts use bounded
`query`/`reply` requests addressed to the requesting panel, cancelled on close or
replacement. They never replace the default forecast or its disk cache. Alternate
cities remain session-only. HTTP calls have five-second limits within a total
17-second budget; provider 429 responses establish cooldowns.

`ai.usage` refreshes on opening and every five minutes only while observed.
The shared adapter reconciles cached accounts before refreshing; at most two
account jobs use the three-thread broker pool, leaving room for other domains.
Closing the last menu prevents queued accounts from starting; active calls drain
under their existing command/HTTP timeouts. The AI adapter is then released, so
its provider implementation is not retained at idle. Account cooldown deadlines
survive adapter release without retaining provider payloads. `ai-popup.py` and
`ai-usage.py` retain their standalone interfaces and compatible cache; the popup's
session selection file is unchanged. Diagnostics expose only topic-level codes
and counters, never account identifiers or provider responses. Adapter imports
and reads run lazily in the bounded pool; an import failure affects only its domain.

### Update data ownership

The broker lazily imports `updates.py` in its bounded worker pool. It checks
45 seconds after startup, every six hours, and on the existing `updates refresh`
IPC after System Update or a manual check. Concurrent refreshes coalesce into one
follow-up check. Each external command retains its 120-second timeout; the read
budget is 365 seconds for the three sequential commands. Private checkupdates
package databases remain separate from the system database. Successful zero,
offline and unreadable results are distinct; failed checks never report up to date.
The shell retains presentation, count-based notification deduplication and task
terminal launching. The standalone CLI retains its output and updater actions
remain outside the broker. All domains initialize lazily inside the worker pool;
an import failure remains local to its domain. Screen/VM acceptance is pending.
