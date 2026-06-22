// Kamera-Clip für den Roboterarm — alternatives "Kinder-Teil" zum Selberdrucken.
// Hält die InnoMaker-16-MP-USB-Kamera an der drehenden Säule/Schulter (Auge dreht mit der Basis).
// Parametrisch: Maße an die eigene Kamera anpassen und mit OpenSCAD als STL exportieren.
//
//   openscad -o kamera_clip.stl kamera_clip.scad
//
// Druck: PLA, 0.2 mm, 20 % Infill, ohne Stützen (flach aufs Bett legen).

// ---- Parameter (mm) ----
// InnoMaker 16 MP (IMX298): quadratische Platine 32 x 32 mm, 4x M2-Löcher.
// Werte ggf. am realen Modul nachmessen (Linsenhöhe je nach Fokus-Mechanik).
kamera_breite   = 32;   // Breite der Kameraplatine/-fassung
kamera_dicke    = 10;   // Dicke (Platine + Linsenmodul)
wand            = 2.4;  // Wandstärke
lippe           = 2.0;  // Haltelippe vorn
platte_dicke    = 3.0;  // Montageplatte
platte_laenge   = 30;
schraubloch     = 3.4;  // M3 Durchgang
lochabstand     = 20;

$fn = 48;

module montageplatte() {
    difference() {
        cube([platte_laenge, kamera_breite + 2*wand, platte_dicke]);
        for (dx = [-1, 1])
            translate([platte_laenge/2 + dx*lochabstand/2,
                       (kamera_breite + 2*wand)/2, -1])
                cylinder(h = platte_dicke + 2, d = schraubloch);
    }
}

module halter() {
    // U-förmige Fassung für die Kamera
    aussen_b = kamera_breite + 2*wand;
    aussen_t = kamera_dicke + 2*wand;
    difference() {
        cube([aussen_t, aussen_b, kamera_dicke + wand + lippe]);
        translate([wand, wand, wand])
            cube([kamera_dicke, kamera_breite, kamera_dicke + lippe + 1]);
        // Fenster für die Linse
        translate([-1, aussen_b/2 - 6, wand + 3])
            cube([aussen_t + 2, 12, kamera_dicke]);
    }
}

union() {
    montageplatte();
    translate([platte_laenge - wand, 0, platte_dicke])
        halter();
}
