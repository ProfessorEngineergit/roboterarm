"""Smoke-Test für den Dienst (lädt das Modul in Simulation, ohne Server zu starten)."""
import importlib.util
import os
import sys
import unittest

os.environ.setdefault("ROBOTERARM_BACKEND", "sim")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def lade_service():
    spec = importlib.util.spec_from_file_location(
        "robot_service", os.path.join(ROOT, "service", "robot_service.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = lade_service()

    def test_status(self):
        s = self.svc.status()
        self.assertIn("winkel", s)
        self.assertIn("backend", s)

    def test_frame_bild(self):
        roh, typ = self.svc.frame_bild(self.svc.arm.kamera.frame())
        self.assertIn(typ, ("image/bmp", "image/jpeg"))
        self.assertGreater(len(roh), 100)

    def test_runner_idle(self):
        self.assertFalse(self.svc.runner.laeuft())


if __name__ == "__main__":
    unittest.main()
