import unittest
from unittest.mock import patch

import numpy as np

import rgbcontrol


class ZoneTests(unittest.TestCase):
    def test_samples_screen_from_left_to_right(self):
        image = np.zeros((2, 21, 3), dtype=np.uint8)
        image[:, :7] = (0, 0, 255)
        image[:, 7:] = (255, 0, 0)
        colors = rgbcontrol.generateZoneColors(image, 7)
        self.assertEqual(colors[:2], [[255, 0, 0]] * 2)
        self.assertEqual(colors[2], [85, 0, 170])
        self.assertEqual(colors[3:], [[0, 0, 255]] * 4)

    def test_single_zone_averages_whole_screen(self):
        image = np.array([[[0, 0, 255], [255, 0, 0]]], dtype=np.uint8)
        self.assertEqual(rgbcontrol.generateZoneColors(image, 1), [[127.5, 0, 127.5]])

    def test_sends_all_colors_and_fades_each_zone(self):
        with patch.object(rgbcontrol, 'wsSend') as send, patch.object(rgbcontrol, 'brightness', 0.5):
            rgbcontrol.sendrgb(None, [(255, 0, 0), (0, 0, 255)], False)
            send.assert_called_with(None, '#ff0000,#0000ff')
            rgbcontrol.switch_lights(None, [[200, 0, 0], [0, 0, 100]], 'on')
            send.assert_called_with(None, '#640000,#000032')
            rgbcontrol.switch_lights(None, [[200, 0, 0], [0, 0, 100]], 'off')
            send.assert_called_with(None, '#000000,#000000')


if __name__ == '__main__':
    unittest.main()
