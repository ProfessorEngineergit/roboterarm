"""On-Device-ML-Studio — beliebige Objekte erkennen, vollständig offline.

Aufbau wie „richtige" Bildklassifikation, aber leichtgewichtig für die CPU des
RK3399-T (keine NPU):

  Bild ──► Merkmals-Extraktor ──► Klassifikator ──► Label (+ Konfidenz)

* Extraktoren (austauschbar):
    - MobileNetExtractor  (tflite-Embeddings, falls ROBOTERARM_MOBILENET gesetzt)
    - KombiExtractor      (Farbhistogramm + Thumbnail; Default, rein numpy)
* Klassifikatoren (austauschbar): KNN, NaechsterCentroid, LogReg.
* Datensatz: beliebig viele Klassen, Persistenz, Train/Test-Split.
* Auswertung: Genauigkeit + Confusion-Matrix (für den Oberstufen-Track).
"""
from __future__ import annotations

import json
import os
import random
from collections import Counter

import numpy as np


# ============================ Merkmals-Extraktoren ============================

class Extractor:
    name = "basis"

    def __call__(self, frame):
        raise NotImplementedError


class ThumbnailExtractor(Extractor):
    name = "thumbnail"

    def __init__(self, n: int = 12):
        self.n = n

    def __call__(self, frame):
        h, w = frame.shape[:2]
        ys = np.linspace(0, h - 1, self.n).astype(int)
        xs = np.linspace(0, w - 1, self.n).astype(int)
        return (frame[np.ix_(ys, xs)].astype(np.float32) / 255.0).reshape(-1)


class FarbHistogramExtractor(Extractor):
    name = "farbhist"

    def __init__(self, bins: int = 8):
        self.bins = bins

    def __call__(self, frame):
        from .vision import _bgr_to_hsv
        h, s, _v = _bgr_to_hsv(frame)
        hi = np.clip((h / 180.0 * self.bins).astype(int), 0, self.bins - 1)
        si = np.clip((s / 256.0 * self.bins).astype(int), 0, self.bins - 1)
        hist = np.zeros((self.bins, self.bins), np.float32)
        np.add.at(hist, (hi.ravel(), si.ravel()), 1.0)
        hist /= hist.sum() + 1e-6
        return hist.reshape(-1)


class KombiExtractor(Extractor):
    """Default: Farbverteilung (was) + grobes Thumbnail (wo) — gute Allround-Merkmale."""
    name = "kombi"

    def __init__(self):
        self.a = FarbHistogramExtractor(8)
        self.b = ThumbnailExtractor(10)

    def __call__(self, frame):
        return np.concatenate([self.a(frame), self.b(frame)])


class MobileNetExtractor(Extractor):
    name = "mobilenet"

    def __init__(self, pfad: str):
        try:
            from tflite_runtime.interpreter import Interpreter
        except Exception:
            from tensorflow.lite import Interpreter  # type: ignore
        self.interp = Interpreter(model_path=pfad)
        self.interp.allocate_tensors()
        self.inp = self.interp.get_input_details()[0]
        self.out = self.interp.get_output_details()[0]
        _, self.hh, self.ww, _ = self.inp["shape"]

    def __call__(self, frame):
        ys = np.linspace(0, frame.shape[0] - 1, self.hh).astype(int)
        xs = np.linspace(0, frame.shape[1] - 1, self.ww).astype(int)
        bild = frame[np.ix_(ys, xs)][:, :, ::-1]                  # BGR->RGB
        x = (bild.astype(np.float32) / 127.5 - 1.0)[None, ...]
        self.interp.set_tensor(self.inp["index"], x)
        self.interp.invoke()
        return self.interp.get_tensor(self.out["index"]).reshape(-1).astype(np.float32)


def standard_extractor() -> Extractor:
    pfad = os.environ.get("ROBOTERARM_MOBILENET")
    if pfad and os.path.exists(pfad):
        try:
            return MobileNetExtractor(pfad)
        except Exception:
            pass
    return KombiExtractor()


# ============================== Klassifikatoren ==============================

class Klassifikator:
    def fit(self, X, y):
        raise NotImplementedError

    def predict_proba(self, f) -> dict:
        raise NotImplementedError

    def predict(self, f):
        p = self.predict_proba(f)
        if not p:
            return (None, 0.0)
        lab = max(p, key=p.get)
        return (lab, p[lab])

    def klon(self):
        return self.__class__()


class KNN(Klassifikator):
    def __init__(self, k: int = 3):
        self.k = k

    def fit(self, X, y):
        self.X = np.asarray(X, np.float32)
        self.y = list(y)
        return self

    def predict_proba(self, f):
        if len(self.y) == 0:
            return {}
        d = np.linalg.norm(self.X - np.asarray(f, np.float32), axis=1)
        idx = np.argsort(d)[: min(self.k, len(d))]
        c = Counter(self.y[i] for i in idx)
        tot = sum(c.values())
        return {k: v / tot for k, v in c.items()}

    def klon(self):
        return KNN(self.k)


class NaechsterCentroid(Klassifikator):
    def fit(self, X, y):
        X = np.asarray(X, np.float32)
        self.klassen_ = sorted(set(y))
        self.cent = {c: X[[i for i, l in enumerate(y) if l == c]].mean(0) for c in self.klassen_}
        return self

    def predict_proba(self, f):
        f = np.asarray(f, np.float32)
        d = {c: float(np.linalg.norm(f - self.cent[c])) for c in self.klassen_}
        mn = min(d.values())
        w = {c: np.exp(-(d[c] - mn)) for c in d}
        tot = sum(w.values())
        return {c: float(w[c] / tot) for c in w}


class LogReg(Klassifikator):
    def __init__(self, lr: float = 0.5, schritte: int = 300, l2: float = 1e-3):
        self.lr, self.schritte, self.l2 = lr, schritte, l2

    def fit(self, X, y):
        X = np.asarray(X, np.float32)
        self.klassen_ = sorted(set(y))
        idx = {c: i for i, c in enumerate(self.klassen_)}
        Y = np.zeros((len(y), len(self.klassen_)), np.float32)
        for i, l in enumerate(y):
            Y[i, idx[l]] = 1.0
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-6
        Xn = (X - self.mu) / self.sd
        n, d = Xn.shape
        self.W = np.zeros((d, len(self.klassen_)), np.float32)
        self.b = np.zeros(len(self.klassen_), np.float32)
        for _ in range(self.schritte):
            z = Xn @ self.W + self.b
            z -= z.max(1, keepdims=True)
            P = np.exp(z)
            P /= P.sum(1, keepdims=True)
            g = P - Y
            self.W -= self.lr * (Xn.T @ g / n + self.l2 * self.W)
            self.b -= self.lr * g.mean(0)
        return self

    def predict_proba(self, f):
        fn = (np.asarray(f, np.float32) - self.mu) / self.sd
        z = fn @ self.W + self.b
        z -= z.max()
        p = np.exp(z)
        p /= p.sum()
        return {c: float(p[i]) for i, c in enumerate(self.klassen_)}

    def klon(self):
        return LogReg(self.lr, self.schritte, self.l2)


KLASSIFIKATOREN = {"knn": KNN, "centroid": NaechsterCentroid, "logreg": LogReg}


# ================================= Datensatz =================================

class Datensatz:
    def __init__(self):
        self.merkmale: list = []
        self.labels: list[str] = []

    def hinzu(self, label: str, merkmal):
        self.merkmale.append(np.asarray(merkmal, np.float32))
        self.labels.append(label)

    def klassen(self):
        return sorted(set(self.labels))

    def zaehle(self) -> dict:
        return dict(Counter(self.labels))

    def __len__(self):
        return len(self.labels)

    def split(self, anteil: float = 0.3, seed: int = 0):
        idx = list(range(len(self.labels)))
        random.Random(seed).shuffle(idx)
        n_test = int(len(idx) * anteil) if len(idx) > 1 else 0
        test = set(idx[:n_test])
        return [i for i in idx if i not in test], [i for i in idx if i in test]

    def speichere(self, ordner: str):
        os.makedirs(ordner, exist_ok=True)
        np.savez(os.path.join(ordner, "merkmale.npz"),
                 X=np.asarray(self.merkmale, np.float32) if self.merkmale else np.zeros((0, 0)))
        with open(os.path.join(ordner, "labels.json"), "w", encoding="utf-8") as f:
            json.dump(self.labels, f, ensure_ascii=False)

    @classmethod
    def lade(cls, ordner: str):
        d = cls()
        with open(os.path.join(ordner, "labels.json"), encoding="utf-8") as f:
            d.labels = json.load(f)
        X = np.load(os.path.join(ordner, "merkmale.npz"))["X"]
        d.merkmale = [np.asarray(r, np.float32) for r in X]
        return d


# ================================== Modell ===================================

class Modell:
    def __init__(self, extractor: Extractor | None = None, klassifikator: Klassifikator | None = None):
        self.extractor = extractor or standard_extractor()
        self.klf = klassifikator or KNN()
        self.datensatz = Datensatz()
        self.labels: list[str] = []
        self._fit = False

    # ---- Datensatz ----
    def aufnehmen(self, label: str, frame):
        self.datensatz.hinzu(label, self.extractor(frame))
        self._fit = False

    @property
    def klassen(self):
        return self.datensatz.klassen()

    # ---- Training / Inferenz ----
    def trainiere(self):
        if not len(self.datensatz):
            return {"fehler": "keine Daten"}
        self.klf.fit(self.datensatz.merkmale, self.datensatz.labels)
        self._fit = True
        self.labels = self.datensatz.klassen()
        return {"beispiele": len(self.datensatz), "klassen": self.labels,
                "verteilung": self.datensatz.zaehle(),
                "klassifikator": type(self.klf).__name__,
                "merkmale": type(self.extractor).__name__}

    def _sicher_fit(self) -> bool:
        if not self._fit and len(self.datensatz):
            self.trainiere()
        return self._fit

    def vorhersage(self, frame):
        if not self._sicher_fit():
            return None
        return self.klf.predict(self.extractor(frame))[0]

    def vorhersage_detail(self, frame) -> dict:
        if not self._sicher_fit():
            return {"label": None, "confidence": 0.0, "proba": {}}
        f = self.extractor(frame)
        lab, conf = self.klf.predict(f)
        return {"label": lab, "confidence": round(float(conf), 3),
                "proba": {k: round(v, 3) for k, v in self.klf.predict_proba(f).items()}}

    def sieht(self, label: str, frame) -> bool:
        return self.vorhersage(frame) == label

    def bewerte(self, anteil: float = 0.3, seed: int = 0) -> dict:
        if len(self.datensatz) < 2 or len(self.datensatz.klassen()) < 2:
            return {"fehler": "zu wenig Daten (mind. 2 Klassen)"}
        tr, te = self.datensatz.split(anteil, seed)
        if not te:
            return {"fehler": "Testmenge leer"}
        X, y = self.datensatz.merkmale, self.datensatz.labels
        klf = self.klf.klon().fit([X[i] for i in tr], [y[i] for i in tr])
        klassen = self.datensatz.klassen()
        conf = {a: {b: 0 for b in klassen} for a in klassen}
        richtig = 0
        for i in te:
            p = klf.predict(X[i])[0]
            conf[y[i]][p] = conf[y[i]].get(p, 0) + 1
            richtig += int(p == y[i])
        return {"genauigkeit": round(richtig / len(te), 3), "confusion": conf,
                "klassen": klassen, "n_test": len(te), "n_train": len(tr)}

    # ---- Persistenz ----
    def speichere(self, ordner: str = "modell"):
        self.datensatz.speichere(ordner)
        with open(os.path.join(ordner, "modell.json"), "w", encoding="utf-8") as f:
            json.dump({"klassifikator": type(self.klf).__name__,
                       "k": getattr(self.klf, "k", None)}, f, ensure_ascii=False)
        return ordner

    @classmethod
    def lade(cls, ordner: str = "modell"):
        m = cls()
        m.datensatz = Datensatz.lade(ordner)
        try:
            with open(os.path.join(ordner, "modell.json"), encoding="utf-8") as f:
                meta = json.load(f)
            klass = {"KNN": KNN, "NaechsterCentroid": NaechsterCentroid, "LogReg": LogReg}.get(
                meta.get("klassifikator"), KNN)
            m.klf = klass(meta["k"]) if klass is KNN and meta.get("k") else klass()
        except Exception:
            pass
        if len(m.datensatz):
            m.trainiere()
        return m
