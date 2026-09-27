import unittest
from unittest.mock import patch

import token_strip as hud


MAIN = 101
SECOND_MAIN = 102
MINIMIZED_MAIN = 103
MENU = 201
UNOWNED_POPUP = 202
OWNED_POPUP = 203
SMALL_POPUP = 204


class FakeUser32:
    def __init__(self):
        self.owners = {MENU: MAIN, OWNED_POPUP: MAIN}

    def IsWindowVisible(self, hwnd):
        return True

    def GetWindow(self, hwnd, relationship):
        assert relationship == hud.GW_OWNER
        return self.owners.get(hwnd, 0)

    def GetForegroundWindow(self):
        return MENU

    def EnumWindows(self, callback, unused):
        for hwnd in (MENU, UNOWNED_POPUP, OWNED_POPUP, SMALL_POPUP,
                     MAIN, SECOND_MAIN, MINIMIZED_MAIN):
            callback(hwnd, 0)


class WindowDetectionTests(unittest.TestCase):
    def test_only_main_windows_are_candidates(self):
        dimensions = {
            MENU: (48, 25),
            UNOWNED_POPUP: (500, 400),
            OWNED_POPUP: (500, 400),
            SMALL_POPUP: (48, 25),
            MAIN: (1200, 800),
            SECOND_MAIN: (850, 650),
            MINIMIZED_MAIN: (850, 650),
        }
        fake_user32 = FakeUser32()
        with (patch.object(hud, "u32", fake_user32),
              patch.object(hud, "_process_name", return_value="ChatGPT.exe"),
              patch.object(hud, "_get_window_long", side_effect=lambda hwnd, _index:
                           hud.WS_EX_NOACTIVATE if hwnd == UNOWNED_POPUP else 0),
              patch.object(hud, "rect", side_effect=lambda hwnd:
                           (0, 0, *dimensions[hwnd])),
              patch.object(hud, "is_minimized_or_cloaked",
                           side_effect=lambda hwnd: hwnd == MINIMIZED_MAIN)):
            self.assertEqual(hud.enum_windows(), [MAIN, SECOND_MAIN])

    def test_foreground_menu_maps_to_its_main_window(self):
        with patch.object(hud, "u32", FakeUser32()):
            self.assertEqual(
                hud.select_codex_window(MENU, SECOND_MAIN, [MAIN, SECOND_MAIN]), MAIN
            )

    def test_unrelated_foreground_preserves_last_main_window(self):
        with patch.object(hud, "u32", FakeUser32()):
            self.assertEqual(
                hud.select_codex_window(999, SECOND_MAIN, [MAIN, SECOND_MAIN]),
                SECOND_MAIN,
            )

    def test_closed_main_is_replaced_by_new_main(self):
        with patch.object(hud, "u32", FakeUser32()):
            self.assertIsNone(hud.select_codex_window(0, MAIN, []))
            self.assertEqual(hud.select_codex_window(0, MAIN, [SECOND_MAIN]), SECOND_MAIN)

    def test_poll_keeps_hud_on_main_while_menu_is_foreground(self):
        selected = []
        app = hud.TokenStrip.__new__(hud.TokenStrip)
        app.last_active_codex = SECOND_MAIN
        app.pinned_thread = None
        app.root = type("Root", (), {"after": lambda self, _ms, callback: callback()})()
        app._accept_poll = lambda _catalog, hwnd, *_: selected.append(hwnd)
        with (patch.object(hud, "u32", FakeUser32()),
              patch.object(hud, "get_catalog", return_value=[]),
              patch.object(hud, "enum_windows", return_value=[MAIN, SECOND_MAIN]),
              patch.object(hud, "uia_page_title", return_value=""),
              patch.object(hud, "discover_thread_for_title", return_value=None)):
            app._background_poll()
        self.assertEqual(selected, [MAIN])


if __name__ == "__main__":
    unittest.main()
