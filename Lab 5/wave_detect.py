"""
Desk Curfew's only control: a wave at the camera. YOLO's pose model finds the shoulders
and wrists; a wave is a raised wrist (about shoulder height or higher) that swings side
to side. The thresholds below are deliberately loose; tighten them if it fires by accident.

    python wave_detect.py          # wave at the webcam; prints WAVE each time it sees one
    python wave_detect.py --debug  # also print what the pose model sees, twice a second

Needs the pose model, exported once like the Part A detector:

    python -c "from ultralytics import YOLO; YOLO('yolo26n-pose.pt').export(format='ncnn')"

The pose model and camera are only used before bed and in the morning. Overnight the
camera belongs to overnight.py, which does not look for waves.
"""
import argparse
import collections
import time

L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST = 5, 6, 9, 10   # COCO keypoint numbers
MIN_CONF = 0.3      # ignore keypoints the model is unsure about
WINDOW = 4.0        # seconds of wrist movement to look at
STEP = 0.2          # a swing must travel this many shoulder-widths before it counts
BELOW = 0.25        # the hand may be this many shoulder-widths below the shoulders and still count as raised
MIN_SWINGS = 2      # changes of direction: right-left-right is two


def count_swings(xs, step=STEP):
    """How many times the sequence changes direction by more than `step`."""
    if not xs:
        return 0
    lo = hi = xs[0]
    direction = swings = 0
    for x in xs[1:]:
        if direction <= 0 and x - lo > step:
            swings += direction < 0
            direction, hi = 1, x
        elif direction >= 0 and hi - x > step:
            swings += direction > 0
            direction, lo = -1, x
        hi, lo = max(hi, x), min(lo, x)
    return swings


class WaveDetector:
    """Feed it one person's keypoints per frame; feed() returns True when a wave is complete."""

    def __init__(self):
        self.history = collections.deque()       # (time, wrist x in shoulder-widths)
        self.status = "starting"                 # why the last frame did or did not count, for --debug

    def feed(self, t, xy, conf):
        while self.history and t - self.history[0][0] > WINDOW:
            self.history.popleft()
        if xy is None:
            self.status = "no person"
            return False
        ok = lambda i: conf[i] >= MIN_CONF
        if not (ok(L_SHOULDER) and ok(R_SHOULDER)):
            self.status = f"shoulders unsure ({conf[L_SHOULDER]:.2f}, {conf[R_SHOULDER]:.2f})"
            return False
        width = abs(xy[L_SHOULDER][0] - xy[R_SHOULDER][0])
        top = min(xy[L_SHOULDER][1], xy[R_SHOULDER][1]) + BELOW * width   # image y grows downwards
        raised = [i for i in (L_WRIST, R_WRIST) if ok(i) and xy[i][1] < top]
        if width < 1 or not raised:
            wrists = ", ".join(f"y {xy[i][1]:.0f} conf {conf[i]:.2f}" for i in (L_WRIST, R_WRIST))
            self.status = f"no hand raised (must be above y {top:.0f}; wrists {wrists})"
            return False
        wrist = min(raised, key=lambda i: xy[i][1])                 # the higher hand
        self.history.append((t, xy[wrist][0] / width))              # shoulder-widths: distance does not matter
        xs = [x for _, x in self.history]
        swings = count_swings(xs)
        self.status = (f"hand up: {swings}/{MIN_SWINGS} swings, side-to-side span "
                       f"{max(xs) - min(xs):.2f} shoulder-widths (needs > {STEP})")
        if swings >= MIN_SWINGS:
            self.history.clear()                                    # one wave, one event
            return True
        return False


class Camera:
    """The webcam plus the pose model, opened only while waiting for a wave."""

    def __init__(self, model_path="yolo26n-pose_ncnn_model"):
        import cv2
        from ultralytics import YOLO
        self.cv2 = cv2
        self.model = YOLO(model_path, task="pose")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.cap.isOpened():
            raise RuntimeError("no webcam found")

    def wait_for_wave(self, timeout=None, debug=False):
        """Block until someone waves (True) or `timeout` seconds pass (False)."""
        detector = WaveDetector()
        t_end = None if timeout is None else time.time() + timeout
        last_print, frames = time.time(), 0
        while t_end is None or time.time() < t_end:
            if debug and time.time() - last_print > 0.5:
                print(f"{frames / (time.time() - last_print):4.1f} fps | {detector.status}", flush=True)
                last_print, frames = time.time(), 0
            frames += 1
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.5)
                continue
            r = self.model.predict(frame, imgsz=320, conf=0.4, verbose=False)[0]
            if r.keypoints is None or len(r.boxes) == 0:
                detector.feed(time.time(), None, None)
                continue
            i = int(r.boxes.conf.argmax())                          # the most confident person
            xy = r.keypoints.xy[i].tolist()
            conf = r.keypoints.conf[i].tolist() if r.keypoints.conf is not None else [1.0] * len(xy)
            if detector.feed(time.time(), xy, conf):
                return True
        return False

    def close(self):
        self.cap.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="print what the pose model sees")
    args = parser.parse_args()
    cam = Camera()
    print("wave at the camera, Ctrl-C to stop", flush=True)
    try:
        while True:
            if cam.wait_for_wave(debug=args.debug):
                print(time.strftime("%H:%M:%S"), "WAVE", flush=True)
    except KeyboardInterrupt:
        pass
    cam.close()
