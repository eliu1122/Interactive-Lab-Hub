"""
Desk Curfew's only control: a wave at the camera. YOLO's pose model finds the shoulders
and wrists; a wave is a wrist held above the shoulders that swings side to side.

    python wave_detect.py          # wave at the webcam; prints WAVE each time it sees one

Needs the pose model, exported once like the Part A detector:

    python -c "from ultralytics import YOLO; YOLO('yolo26n-pose.pt').export(format='ncnn')"

The pose model and camera are only used before bed and in the morning. Overnight the
camera belongs to overnight.py, which does not look for waves.
"""
import collections
import time

L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST = 5, 6, 9, 10   # COCO keypoint numbers
MIN_CONF = 0.5      # ignore keypoints the model is unsure about
WINDOW = 3.0        # seconds of wrist movement to look at
STEP = 0.3          # a swing must travel this many shoulder-widths before it counts
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

    def feed(self, t, xy, conf):
        while self.history and t - self.history[0][0] > WINDOW:
            self.history.popleft()
        if xy is None:
            return False
        ok = lambda i: conf[i] >= MIN_CONF
        if not (ok(L_SHOULDER) and ok(R_SHOULDER)):
            return False
        width = abs(xy[L_SHOULDER][0] - xy[R_SHOULDER][0])
        top = min(xy[L_SHOULDER][1], xy[R_SHOULDER][1])           # image y grows downwards
        raised = [i for i in (L_WRIST, R_WRIST) if ok(i) and xy[i][1] < top]
        if width < 1 or not raised:
            return False
        wrist = min(raised, key=lambda i: xy[i][1])                 # the higher hand
        self.history.append((t, xy[wrist][0] / width))              # shoulder-widths: distance does not matter
        if count_swings([x for _, x in self.history]) >= MIN_SWINGS:
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

    def wait_for_wave(self, timeout=None):
        """Block until someone waves (True) or `timeout` seconds pass (False)."""
        detector = WaveDetector()
        t_end = None if timeout is None else time.time() + timeout
        while t_end is None or time.time() < t_end:
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
    cam = Camera()
    print("wave at the camera, Ctrl-C to stop", flush=True)
    try:
        while True:
            if cam.wait_for_wave():
                print(time.strftime("%H:%M:%S"), "WAVE", flush=True)
    except KeyboardInterrupt:
        pass
    cam.close()
