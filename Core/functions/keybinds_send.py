# Core/keys.py
import ctypes
import time
from ctypes import wintypes

# === CONSTANTES MODULE ===
KEYEVENTF_KEYUP = 0x0002

# === STRUCTURES MODULE ===
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    )

class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = (
            ('ki', KEYBDINPUT),
            ('mi', ctypes.c_byte * 28),
            ('hi', ctypes.c_byte * 32)
        )
    _anonymous_ = ('i',)
    _fields_ = (
        ('type', wintypes.DWORD),
        ('i', _I)
    )

# === CLASSE VK ===
class VK:
    SPACE = 0x20
    RETURN = 0x0D
    SHIFT = 0x10
    CONTROL = 0x11
    MENU = 0x12
    LWIN = 0x5B
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A
    NUM_0 = 0x30
    NUM_1 = 0x31
    NUM_2 = 0x32
    NUM_3 = 0x33
    NUM_4 = 0x34
    NUM_5 = 0x35
    NUM_6 = 0x36
    NUM_7 = 0x37
    NUM_8 = 0x38
    NUM_9 = 0x39
    LSHIFT = 0xA0
    RSHIFT = 0xA1
    LCONTROL = 0xA2
    RCONTROL = 0xA3
    LMENU = 0xA4
    RMENU = 0xA5

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

KEY_MAP = {
    'space': VK.SPACE,
    'enter': VK.RETURN,
    'shift': VK.SHIFT,
    'ctrl': VK.CONTROL,
    'alt': VK.MENU,
    'win': VK.LWIN,
}

# === FONCTIONS HELPER ===
def _send_key(vk_code, is_down):
    user32 = ctypes.windll.user32
    scan = user32.MapVirtualKeyW(vk_code, 0)
    flags = 0 if is_down else KEYEVENTF_KEYUP
    ki = KEYBDINPUT(vk_code, scan, flags, 0, None)
    inp = INPUT(type=1, i=INPUT._I(ki=ki))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

# === FONCTIONS PRINCIPAUX ===
def parse_shortcut(shortcut_str):
    modifiers = 0
    vk = 0
    parts = [p.strip().lower() for p in shortcut_str.split('+')]
    
    for part in parts:
        if part == 'ctrl':
            modifiers |= MOD_CONTROL
        elif part == 'shift':
            modifiers |= MOD_SHIFT
        elif part == 'alt':
            modifiers |= MOD_ALT
        elif part == 'win':
            modifiers |= MOD_WIN
        elif part in KEY_MAP:
            vk = KEY_MAP[part]
        elif part.startswith('f') and part[1:].isdigit():
            vk = getattr(VK, part.upper(), 0)
        elif len(part) == 1:
            vk = ord(part.upper())
    
    return modifiers, vk

def send_shortcut(shortcut_str):
    if not shortcut_str:
        return
    
    _, vk = parse_shortcut(shortcut_str)
    if vk == 0:
        return
    
    _send_key(vk, True)
    time.sleep(0.02)
    _send_key(vk, False)
    time.sleep(0.02)

def send_shortcut_multi(keys_str):
    if not keys_str:
        return
    
    parts = [p.strip().lower() for p in keys_str.split('+')]
    
    vks = []
    for part in parts:
        if part in KEY_MAP:
            vks.append(KEY_MAP[part])
        elif part.startswith('f') and part[1:].isdigit():
            vk_f = getattr(VK, part.upper(), 0)
            if vk_f:
                vks.append(vk_f)
        elif len(part) == 1:
            vks.append(ord(part.upper()))
    
    for vk in vks:
        _send_key(vk, True)
        time.sleep(0.02)
    
    time.sleep(0.05)
    
    for vk in reversed(vks):
        _send_key(vk, False)
        time.sleep(0.02)

def force_release_modifiers():
    for vk in [VK.SHIFT, VK.CONTROL, VK.MENU, VK.LWIN,
               VK.LSHIFT, VK.RSHIFT, VK.LCONTROL, VK.RCONTROL, VK.LMENU, VK.RMENU]:
        _send_key(vk, False)
