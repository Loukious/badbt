#!/usr/bin/python3
import os  # used to all external commands
import sys  # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
# import thread
import keymap
import bt_layouts


class BtkStringClient():
    # constants
    KEY_DOWN_TIME = 0.01
    KEY_DELAY = 0.01

    def __init__(self, lang='us'):
        # keyboard layout language
        self.lang = lang

        # the structure for a bt keyboard input report (size is 10 bytes)
        self.state = [
            0xA1,  # this is an input report
            0x01,  # Usage report = Keyboard
            # Bit array for Modifier keys
            [0,  # Right GUI - Windows Key
                 0,  # Right ALT
                 0,  # Right Shift
                 0,  # Right Control
                 0,  # Left GUI
                 0,  # Left ALT
                 0,  # Left Shift
                 0],  # Left Control
            0x00,  # Vendor reserved
            0x00,  # rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]
        self.scancodes = {
            "-": "KEY_MINUS",
            "=": "KEY_EQUAL",
            ";": "KEY_SEMICOLON",
            "'": "KEY_APOSTROPHE",
            "`": "KEY_GRAVE",
            "\\": "KEY_BACKSLASH",
            ",": "KEY_COMMA",
            ".": "KEY_DOT",
            "/": "KEY_SLASH",
            "_": "key_minus",
            "+": "key_equal",
            ":": "key_semicolon",
            "\"": "key_apostrophe",
            "~": "key_grave",
            "|": "key_backslash",
            "<": "key_comma",
            ">": "key_dot",
            "?": "key_slash",
            " ": "KEY_SPACE",
            "\n": "KEY_ENTER",
            "\h": "KEY_HOME"
        }

        # connect with the Bluetooth keyboard server
        print("setting up DBus Client")
        self.bus = dbus.SystemBus()
        self.btkservice = self.bus.get_object(
            'org.thanhle.btkbservice', '/org/thanhle/btkbservice')
        self.iface = dbus.Interface(self.btkservice, 'org.thanhle.btkbservice')

    def send_key_state(self):
        """sends a single frame of the current key state to the emulator server"""
        bin_str = ""
        element = self.state[2]
        for bit in element:
            bin_str += str(bit)
        self.iface.send_keys(int(bin_str, 2), self.state[4:10])

    def send_key_down(self, scancode, modifiers):
        """sends a key down event to the server"""
        self.state[2] = modifiers
        self.state[4] = scancode
        self.send_key_state()

    def send_key_up(self):
        """sends a key up event to the server"""
        self.state[4] = 0
        self.send_key_state()

    def send_string(self, string_to_send):
        layout = bt_layouts.get_layout(self.lang)
        for c in string_to_send:
            if c in layout:
                keystrokes = layout[c]
                for scancode, modifiers in keystrokes:
                    self.send_key_down(scancode, modifiers)
                    time.sleep(BtkStringClient.KEY_DOWN_TIME)
                    self.send_key_up()
                    time.sleep(BtkStringClient.KEY_DELAY)
            else:
                # Fallback: try US layout via legacy scancodes dict + keymap
                cu = c.upper()
                modifiers = [0, 0, 0, 0, 0, 0, 0, 0]
                if cu in self.scancodes:
                    scantablekey = self.scancodes[cu]
                    if scantablekey.islower():
                        modifiers = [0, 0, 0, 0, 0, 0, 1, 0]
                        scantablekey = scantablekey.upper()
                else:
                    if c.isupper():
                        modifiers = [0, 0, 0, 0, 0, 0, 1, 0]
                    scantablekey = "KEY_" + cu
                if scantablekey in keymap.keytable:
                    scancode = keymap.keytable[scantablekey]
                    self.send_key_down(scancode, modifiers)
                    time.sleep(BtkStringClient.KEY_DOWN_TIME)
                    self.send_key_up()
                    time.sleep(BtkStringClient.KEY_DELAY)
                else:
                    print(f"Warning: unsupported character '{c}' for layout '{self.lang}'")

if __name__ == "__main__":
    if(len(sys.argv) < 2):
        print("Usage: send_string <string to send> [mobile | mobilewww | windows | linux | mac] [win7 | win8 | win10 | win11] [-l language]")
        exit()

    # Parse -l language flag from argv
    lang = 'us'
    args = sys.argv[1:]
    if '-l' in args:
        idx = args.index('-l')
        if idx + 1 < len(args):
            lang = args[idx + 1].lower()
            args = args[:idx] + args[idx + 2:]

    string_to_send = args[0] if len(args) > 0 else ''
    prefix = args[1] if len(args) > 1 else ''
    uac = args[2] if len(args) > 2 else ''

    dc = BtkStringClient(lang=lang)
    print(f"Sending '{string_to_send}' (layout: {lang})")
# Send custom prefix
    if prefix == "mobile":
        scantablekey = "KEY_ENTER"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 1, 0, 0, 0 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(2)

    if prefix == "mobilewww":
        scantablekey = "KEY_WWW"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(5)
        scantablekey = "KEY_L"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 0, 0, 0, 1 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(2)

    if prefix == "windows":
        scantablekey = "KEY_LEFTMETA"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(3)
        dc.send_string("cmd")
        time.sleep(1)
        scantablekey = "KEY_ENTER"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 0, 0, 1, 1 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(2)

        if uac == "win7":
            scantablekey = "KEY_LEFT"
            scancode = keymap.keytable[scantablekey]
            modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            dc.send_key_down(scancode, modifiers)
            dc.send_key_up()
            time.sleep(2)
            dc.send_string("\n")

        if uac == "win8":
            scantablekey = "KEY_LEFT"
            scancode = keymap.keytable[scantablekey]
            modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            dc.send_key_down(scancode, modifiers)
            dc.send_key_up()
            time.sleep(2)
            dc.send_string("\n")

        if uac == "win10":
            scantablekey = "KEY_LEFT"
            scancode = keymap.keytable[scantablekey]
            modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            dc.send_key_down(scancode, modifiers)
            dc.send_key_up()
            time.sleep(2)
            dc.send_string("\n")

        if uac == "win11":
            scantablekey = "KEY_DOWN"
            scancode = keymap.keytable[scantablekey]
            modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            dc.send_key_down(scancode, modifiers)
            dc.send_key_up()
            time.sleep(1)
            dc.send_string("\n")
            scantablekey = "KEY_LEFT"
            scancode = keymap.keytable[scantablekey]
            modifiers = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            dc.send_key_down(scancode, modifiers)
            dc.send_key_up()
            time.sleep(2)
            dc.send_string("\n")

    if prefix == "mac":
        scantablekey = "KEY_SPACE"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 1, 0, 0, 0 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(1)
        dc.send_string("terminal\n")
        time.sleep(1)

    if prefix == "linux":
        scantablekey = "KEY_T"
        scancode = keymap.keytable[scantablekey]
        modifiers = [ 0, 0, 0, 0, 0, 1, 0, 1 ]
        dc.send_key_down(scancode, modifiers)
        dc.send_key_up()
        time.sleep(1)

# Send string + ENTER
    time.sleep(1)
    dc.send_string(string_to_send + "\n")
    print("Done.")
