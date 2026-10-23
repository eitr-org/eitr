import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class ChatLayoutTests(unittest.TestCase):
    def test_chat_in_both_themes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            renders = Path(os.environ.get('EITR_REVIEW_RENDERS') or temporary)
            renders.mkdir(parents=True, exist_ok=True)
            for theme in ('light', 'dark'):
                capture = renders / ('chat-' + theme + '.png')
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 460; implicitHeight: 680
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.AssistantChat {
                id: chat
                anchors.fill: parent; anchors.margins: 20
                foreground: "FOREGROUND"; background: "BACKGROUND"
                helperCommand: ["python3", "-c", "import json,sys; request=json.loads(sys.stdin.readline()); print(json.dumps({'answer': 'Example answer'}))"]
                assistant: ({identifier: "fake", name: "Example assistant", provider: "Example provider", local: false})
                turns: [{role: "user", text: "What can I ask about Eitr?"},
                    {role: "assistant", text: "**Anything:** desktop settings, hardware, or another topic.\\n\\nI can explain options without changing your system."},
                    {role: "user", text: "How do I start a new conversation?"},
                    {role: "assistant", text: "Choose **New chat**. Escape returns to the normal pages and forgets this conversation."}]
            }
            function namedItem(item, name) {
                if (item.objectName === name) return item;
                for (const child of item.children) {
                    const found = namedItem(child, name);
                    if (found) return found;
                }
                return null;
            }
            Timer {
                id: replyCheck
                interval: 100; repeat: true
                property int attempts: 0
                onTriggered: {
                    attempts++;
                    if (attempts > 30) throw new Error("Fake reply timed out: " + chat.error);
                    if (!chat.thinking && chat.turns.length === 2) {
                        if (chat.turns[1].text !== "Example answer") throw new Error("Wrong reply");
                        chat.reset();
                        if (chat.turns.length || chat.draft || Object.keys(chat.response).length) throw new Error("Conversation retained");
                        console.log("CHAT_LAYOUT_OK"); Qt.quit();
                    }
                }
            }
            Timer {
                interval: 600; running: true
                onTriggered: {
                    if (chat.width !== 420 || chat.height !== 640 || chat.thinking) throw new Error("Invalid chat geometry/state");
                    const newChat = sample.namedItem(chat, "newChatButton");
                    if (!newChat || newChat.width < 70 || newChat.x + newChat.width > chat.width)
                        throw new Error("New chat button is clipped");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        chat.reset();
                        if (chat.turns.length || chat.error) throw new Error("Chat was not forgotten");
                        chat.draft = "Example question";
                        chat.send();
                        replyCheck.start();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', '#f5f0e7' if theme == 'light' else '#18212b')
                    .replace('FOREGROUND', '#252936' if theme == 'light' else '#e9eef1')
                    .replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment, text=True,
                                        capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('CHAT_LAYOUT_OK', result.stdout + result.stderr)
                self.assertNotIn('ReferenceError', result.stdout + result.stderr)
                self.assertNotIn('TypeError', result.stdout + result.stderr)
                self.assertGreater(capture.stat().st_size, 1000)
