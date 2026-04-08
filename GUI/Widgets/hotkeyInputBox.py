# Core/keybind_input.py
# Shared keybind input widget + native Alt-key suppression filter.
#
# On Windows, pressing Alt sends WM_SYSCOMMAND SC_KEYMENU which activates the
# window's menu/title-bar area and robs focus BEFORE Qt can handle the key event.
# grabKeyboard() and ShortcutOverride events don't intercept this because it
# happens at the native Win32 message level.  The only reliable fix is a
# QAbstractNativeEventFilter that drops SC_KEYMENU messages while a keybind
# input is actively capturing.
#
# _AltSuppressFilter is intentionally defined AFTER KeybindCapture so it can
# use isinstance(focused, KeybindCapture) — which is reliable regardless of
# PyQt6 wrapper identity.  _ensure_filter() is resolved at call-time (runtime),
# not at class-definition time, so the forward reference is fine.

import ctypes
import re
from PyQt6.QtWidgets import QLineEdit, QMessageBox, QApplication
from PyQt6.QtCore import Qt, QAbstractNativeEventFilter
from PyQt6.QtGui import QKeySequence

# VK codes for every modifier key on Windows.
# Used as a fallback because PyQt6 changed Qt.Key from IntEnum to plain Enum,
# so `event.key() in (Qt.Key.Key_Alt, ...)` can return False even when the
# values match.  nativeVirtualKey() returns a plain int, which is unambiguous.
_MODIFIER_VKS = frozenset({
    0x10,   # VK_SHIFT
    0x11,   # VK_CONTROL
    0x12,   # VK_MENU  (Alt)
    0x5B,   # VK_LWIN
    0x5C,   # VK_RWIN
    0xA0,   # VK_LSHIFT
    0xA1,   # VK_RSHIFT
    0xA2,   # VK_LCONTROL
    0xA3,   # VK_RCONTROL
    0xA4,   # VK_LMENU  (Left Alt)
    0xA5,   # VK_RMENU  (Right Alt / AltGr)
})

# Hardcoded Qt key int values for modifier keys — works even when PyQt6
# returns a raw int from event.key() instead of a Qt.Key enum member.
_MODIFIER_QT_INTS = frozenset({
    0x01000020,  # Qt.Key.Key_Shift
    0x01000021,  # Qt.Key.Key_Control
    0x01000022,  # Qt.Key.Key_Meta
    0x01000023,  # Qt.Key.Key_Alt
    0x01001103,  # Qt.Key.Key_AltGr (Qt 6.x — may not exist in all builds)
})

# Safe reference to Key_AltGr — not present in every Qt6 build.
_KEY_ALTGR = getattr(Qt.Key, "Key_AltGr", None)

# Names that QKeySequence produces for modifier-only presses — semantic guard.
_MODIFIER_NAMES = frozenset({"Alt", "Ctrl", "Shift", "Meta", "Win"})

_WM_SYSKEYDOWN = 0x0104   # Alt+key DOWN (also bare Alt press)
_WM_SYSCOMMAND = 0x0112   # System command
_SC_KEYMENU    = 0xF100   # Alt activates menu bar
_VK_MENU       = 0x12     # Virtual-key code for Alt

# ── Shared base class ──────────────────────────────────────────────────────────
# Defined first so _AltSuppressFilter (below) can reference it via isinstance.
class KeybindCapture(QLineEdit):
    """
    A read-only QLineEdit that captures key combinations (including Alt+x).
    Subclass and implement nothing — it just works.

    The parent widget (or any ancestor) may expose a `check_conflict(action_name, keybind)`
    method that returns a conflict description string or None.
    """

    def __init__(self, default_key: str = "", default_vk: int = 0, action_name: str = ""):
        super().__init__()
        self.setText(default_key)
        self.vk = default_vk
        self.action_name = action_name
        self.setReadOnly(True)
        _ensure_filter()  # register the native filter once (resolved at runtime)

    # ── Focus handling ─────────────────────────────────────────────────────────

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.grabKeyboard()

    def focusOutEvent(self, event):
        self.releaseKeyboard()
        super().focusOutEvent(event)

    def _release(self):
        self.releaseKeyboard()
        self.clearFocus()

    # ── Qt shortcut override (belt-and-suspenders) ─────────────────────────────

    def event(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().event(event)

    # ── Key capture ───────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key       = event.key()
        modifiers = event.modifiers()

        # ── Modifier-only guard (four independent layers) ─────────────────────
        # L1: Qt enum — works when PyQt6 returns Qt.Key enum objects.
        _mod_enum = [Qt.Key.Key_Shift, Qt.Key.Key_Control,
                     Qt.Key.Key_Alt, Qt.Key.Key_Meta]
        if _KEY_ALTGR is not None:
            _mod_enum.append(_KEY_ALTGR)
        if key in _mod_enum:
            return
        # L2: hardcoded int — works when PyQt6 returns a plain int from key().
        try:
            if int(key) in _MODIFIER_QT_INTS:
                return
        except Exception:
            pass
        # L3: native VK code — covers synthetic events (nativeVirtualKey is
        #     always a plain int, never an enum).
        if event.nativeVirtualKey() in _MODIFIER_VKS:
            return

        # Clear / cancel
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Escape):
            self.setText("")
            self.vk = 0
            self._release()
            return

        self.vk = event.nativeVirtualKey()
        # Build key-sequence string; use int() explicitly so bitwise-or works
        # regardless of whether PyQt6 wraps these as Enum or IntEnum.
        try:
            new_text = QKeySequence(int(modifiers) | int(key)).toString()
        except Exception:
            try:
                new_text = QKeySequence(modifiers.value | int(key)).toString()
            except Exception:
                return

        # L4: semantic guard — if QKeySequence still produced only a modifier
        #     name ("Alt", "Ctrl" …) no real key was combined yet.
        if not new_text or new_text in _MODIFIER_NAMES:
            return
            
        import re
        if re.fullmatch(r'(?:Ctrl\+?|Alt\+?|AltGr\+?|Shift\+?|Meta\+?|Win\+?)*', new_text):
            return
            
        # Catch localized modifier strings (e.g. "Maj+", "Strg+") or incomplete combinations.
        try:
            k_val = int(key)
        except Exception:
            try:
                k_val = int(key.value)
            except Exception:
                k_val = 0
                
        # 43 = Key_Plus, 61 = Key_Equal
        if new_text.endswith("+") and k_val not in (43, 61):
            return

        # Walk up the widget tree to find a parent that implements check_conflict
        parent = self.parent()
        while parent and not hasattr(parent, "check_conflict"):
            parent = parent.parent()

        if parent:
            conflict = parent.check_conflict(self.action_name, new_text)
            if conflict:
                self._release()
                QMessageBox.warning(
                    self.window(),
                    "Hotkey Conflict",
                    f"The hotkey '{new_text}' is already in use by '{conflict}'.\n"
                    f"Please choose a different hotkey."
                )
                return

        self.setText(new_text)
        self._release()


# ── Native event filter ────────────────────────────────────────────────────────
# Defined AFTER KeybindCapture so isinstance() works without forward references.
class _AltSuppressFilter(QAbstractNativeEventFilter):
    """
    Suppresses WM_SYSCOMMAND SC_KEYMENU whenever a KeybindCapture widget has
    keyboard focus.  Checks QApplication.focusWidget() at event-dispatch time
    rather than relying on focusIn/focusOut to toggle a flag — this avoids
    races with multi-input layouts, scroll areas, and modal dialogs.
    isinstance() is used instead of identity/set membership because PyQt6 may
    return different Python wrapper objects for the same underlying C++ widget.
    """

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            focused = QApplication.focusWidget()
            if focused is not None and isinstance(focused, KeybindCapture):
                try:
                    addr = int(message)
                    if not addr:
                        return False, 0
                    
                    from ctypes import wintypes
                    msg = wintypes.MSG.from_address(addr)
                    # Block bare Alt DOWN — this is what makes DefWindowProc
                    # enter "menu mode".  Qt still detects Alt as a held
                    # modifier via GetKeyState(), so Alt+X combos still work.
                    if msg.message == _WM_SYSKEYDOWN and msg.wParam == _VK_MENU:
                        return True, 0
                    # Belt-and-suspenders: kill SC_KEYMENU if it slips through.
                    if msg.message == _WM_SYSCOMMAND and (msg.wParam & 0xFFF0) == _SC_KEYMENU:
                        return True, 0
                except Exception:
                    pass
        return False, 0


_filter_instance: _AltSuppressFilter | None = None


def _ensure_filter() -> _AltSuppressFilter:
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = _AltSuppressFilter()
        QApplication.instance().installNativeEventFilter(_filter_instance)
    return _filter_instance
