"""Test-Suite (Simulation) für die roboterarm-Bibliothek.

    PYTHONPATH=. python3 -m unittest discover -s tests
"""
import os
import tempfile

os.environ.setdefault("ROBOTERARM_BACKEND", "sim")
_tmp = tempfile.mkdtemp(prefix="roboterarm_test_")
os.environ["ROBOTERARM_CONFIG"] = os.path.join(_tmp, "config.json")
os.environ["ROBOTERARM_PROJEKTE"] = os.path.join(_tmp, "projekte")

import json
import unittest

import numpy as np

from roboterarm import Arm, Config, vision
from roboterarm.ml import KNN, NaechsterCentroid, LogReg

ROT = (40, 40, 220)
BLAU = (220, 60, 40)
GRUEN = (40, 200, 40)


def frame_mit(bgr, bereich=None, h=120, w=160):
    img = np.full((h, w, 3), 60, np.uint8)
    if bereich:
        y0, y1, x0, x1 = bereich
        img[y0:y1, x0:x1] = bgr
    else:
        img[:, :] = bgr
    return img


class TestBewegung(unittest.TestCase):
    def test_home_und_grenzen(self):
        arm = Arm()
        arm.home()
        self.assertEqual(arm.basis_winkel(), 90)
        arm.basis(999)
        self.assertLessEqual(arm.basis_winkel(), 180)
        arm.schulter(0)
        self.assertGreaterEqual(arm.winkel("schulter"), 20)

    def test_tempo_und_bewege(self):
        arm = Arm()
        arm.tempo(0)
        arm.bewege("ellbogen", 120)
        self.assertEqual(arm.winkel("ellbogen"), 120)


class TestVision(unittest.TestCase):
    def test_farbe_finden(self):
        f = frame_mit(ROT)
        t = vision.finde(f, "rot")
        self.assertIsNotNone(t)
        self.assertAlmostEqual(t["x"], 0, delta=0.2)
        self.assertIsNone(vision.finde(f, "blau"))

    def test_synonyme_und_custom(self):
        f = frame_mit(GRUEN)
        self.assertIsNotNone(vision.finde(f, "grün"))           # Synonym -> gruen
        self.assertIsNotNone(vision.finde(f, [(35, 60, 50), (85, 255, 255)]))  # eigener HSV

    def test_finde_alle(self):
        f = frame_mit(ROT, bereich=(40, 80, 10, 60))
        self.assertGreaterEqual(len(vision.finde_alle(f, "rot")), 1)


class TestML(unittest.TestCase):
    def test_klassifikatoren(self):
        X = [[0, 0], [0, 1], [1, 0], [8, 8], [8, 9], [9, 8]]
        y = ["a", "a", "a", "b", "b", "b"]
        for K in (KNN, NaechsterCentroid, LogReg):
            k = K().fit(X, y)
            self.assertEqual(k.predict([0, 0])[0], "a", K.__name__)
            self.assertEqual(k.predict([9, 9])[0], "b", K.__name__)

    def test_modell_und_bewertung(self):
        arm = Arm()
        arm.kamera.sim_szene(hat_ball=True, ball_welt=90)
        for _ in range(10):
            arm.modell.aufnehmen("Ball", arm.kamera.frame())
        arm.kamera.sim_szene(hat_ball=False)
        for _ in range(10):
            arm.modell.aufnehmen("leer", arm.kamera.frame())
        info = arm.modell.trainiere()
        self.assertEqual(sorted(info["klassen"]), ["Ball", "leer"])
        b = arm.modell.bewerte()
        self.assertGreaterEqual(b["genauigkeit"], 0.8)
        self.assertIn("confusion", b)


class TestGenerisch(unittest.TestCase):
    def test_sieht_farbe(self):
        arm = Arm()
        arm.kamera.sim_objekte([{"welt": 90, "farbe": "orange"}])
        self.assertTrue(arm.sieht("orange"))
        arm.kamera.sim_objekte([])
        self.assertFalse(arm.sieht("orange"))

    def test_sieht_ml(self):
        arm = Arm()
        arm.kamera.sim_objekte([{"welt": 90, "farbe": "rot", "radius": 24}])
        arm.lerne("Apfel", 8)
        arm.kamera.sim_objekte([])
        arm.lerne("nichts", 8)
        arm.kamera.sim_objekte([{"welt": 90, "farbe": "rot", "radius": 24}])
        self.assertTrue(arm.sieht("Apfel"))

    def test_suche_zentriere(self):
        arm = Arm()
        arm.home()
        arm.kamera.sim_objekte([{"welt": 140, "farbe": "orange"}])
        self.assertTrue(arm.suche("orange"))
        arm.zentriere_auf("orange")
        self.assertLessEqual(abs(arm.finde("orange")["x"]), 0.2)


class TestPosenAufnahme(unittest.TestCase):
    def test_pose(self):
        arm = Arm()
        arm.tempo(0)
        arm.basis(120)
        arm.schulter(70)
        arm.pose_speichern("test")
        arm.home()
        arm.pose_anfahren("test")
        self.assertEqual(arm.basis_winkel(), 120)

    def test_aufnahme_wiedergabe(self):
        arm = Arm()
        arm.tempo(0)
        arm.aufnahme_start()
        arm.basis(100)
        arm.greifer.zu()
        schritte = arm.aufnahme_stop()
        self.assertGreaterEqual(len(schritte), 2)
        arm.home()
        arm.wiedergabe(schritte)
        self.assertEqual(arm.basis_winkel(), 100)


class TestConfigIK(unittest.TestCase):
    def test_config_roundtrip(self):
        c = Config()
        c.farben = {"meinrot": [((0, 100, 100), (8, 255, 255))]}
        c2 = Config.from_dict(json.loads(json.dumps(c.to_dict())))
        self.assertIn("meinrot", c2.farben)
        self.assertEqual(c2.gelenke["basis"].kanal, 0)

    def test_ik(self):
        arm = Arm()
        z = arm.gehe_zu(120, 0, 60)
        self.assertEqual(set(z), {"basis", "schulter", "ellbogen"})


if __name__ == "__main__":
    unittest.main()
