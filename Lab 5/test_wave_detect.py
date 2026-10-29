"""
Checks the wave rule on made-up keypoints, no camera or Pi needed:

    python -m unittest test_wave_detect
"""
import math
import unittest

from wave_detect import WaveDetector, count_swings

SHOULDERS_Y, SHOULDER_L_X, SHOULDER_R_X = 200, 260, 380      # a person 120 px wide at the shoulders


def pose(wrist_x, wrist_y, conf=0.9):
    xy, c = [[0.0, 0.0] for _ in range(17)], [0.0] * 17
    xy[5], xy[6] = [SHOULDER_L_X, SHOULDERS_Y], [SHOULDER_R_X, SHOULDERS_Y]
    xy[10] = [wrist_x, wrist_y]
    c[5] = c[6] = 0.9
    c[10] = conf
    return xy, c


def run(frames, fps=10):
    d = WaveDetector()
    return any(d.feed(i / fps, xy, c) for i, (xy, c) in enumerate(frames))


class Waves(unittest.TestCase):
    def test_swings(self):
        self.assertEqual(count_swings([0, 1, 0, 1]), 2)
        self.assertEqual(count_swings([0, 0.1, 0, 0.1, 0]), 0)      # jitter is not a wave
        self.assertEqual(count_swings([0, 0.5, 1.0, 1.5]), 0)       # one slow sweep is not a wave

    def test_wave_above_the_shoulders(self):
        frames = [pose(380 + 60 * math.sin(i * 0.8), 120) for i in range(30)]
        self.assertTrue(run(frames))

    def test_same_motion_below_the_shoulders_is_not_a_wave(self):
        frames = [pose(380 + 60 * math.sin(i * 0.8), 300) for i in range(30)]
        self.assertFalse(run(frames))

    def test_raised_hand_held_still_is_not_a_wave(self):
        self.assertFalse(run([pose(400, 120) for _ in range(30)]))

    def test_unsure_wrist_is_ignored(self):
        frames = [pose(380 + 60 * math.sin(i * 0.8), 120, conf=0.2) for i in range(30)]
        self.assertFalse(run(frames))

    def test_too_slow_to_fit_the_window(self):
        frames = [pose(380 + 60 * math.sin(i * 0.05), 120) for i in range(60)]   # one swing per ~6 s
        self.assertFalse(run(frames))


if __name__ == "__main__":
    unittest.main()
