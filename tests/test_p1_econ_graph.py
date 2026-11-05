"""The economics graph builder (bie/brain/video/econ_graph.py): the drawing's numbers come from the economics."""
import unittest

from bie.brain import saanche
from bie.brain.video.econ_graph import EconGraph


def market():
    g = EconGraph(x_label="मात्रा", y_label="कीमत")
    D = g.linear("D", intercept=9, slope=-0.8)
    S = g.linear("S", intercept=1, slope=0.8)
    return g, D, S


class EconGraphTest(unittest.TestCase):
    def test_the_equilibrium_is_where_the_curves_cross(self):
        g, D, S = market()
        E = g.cross(D, S, "E")
        self.assertAlmostEqual(E.x, 5.0, places=3)
        self.assertAlmostEqual(E.y, 5.0, places=3)
        self.assertEqual(g.dots[-1].name, "E")
        g2 = EconGraph(xmin=0.5, ymax=30)                               # TC = 20 + Q²: AC = 20/Q + Q, MC = 2Q
        ac = g2.curve("AC", lambda q: 20 / q + q)
        mc = g2.curve("MC", lambda q: 2 * q)
        low = g2.cross(ac, mc, "min", dot=False)
        self.assertAlmostEqual(low.x, 20 ** 0.5, places=3)            # MC cuts AC at its lowest point
        self.assertAlmostEqual(low.y, 2 * 20 ** 0.5, places=3)

    def test_a_ceiling_makes_a_shortage_of_the_right_size(self):
        g, D, S = market()
        self.assertAlmostEqual(g.at_price(S, 3), 2.5, places=3)
        self.assertAlmostEqual(g.at_price(D, 3), 7.5, places=3)

    def test_a_shift_moves_the_whole_curve(self):
        g, D, S = market()
        D2 = g.shift(D, dx=2, name="D2")
        for q in (1, 4, 7):
            self.assertAlmostEqual(g.value(D2, q + 2), g.value(D, q))
        self.assertTrue(D2.dashed)
        E2 = g.cross(D2, S, "E2")
        self.assertGreater(E2.x, 5)
        self.assertGreater(E2.y, 5)                                    # more demand: higher price and quantity

    def test_areas_follow_the_curves(self):
        g, D, S = market()
        E = g.cross(D, S, "E")
        n = g.surplus_consumer(D, E, "उपभोक्ता बचत")
        pts, label, _ = g.areas[n - 1]
        for x, y in pts[:-2]:
            self.assertAlmostEqual(y, g.value(D, x), places=6)          # the top edge lies on demand
        self.assertEqual(pts[-2], (E.x, E.y))
        m = g.surplus_producer(S, E, "उत्पादक बचत")
        self.assertEqual(m, 2)
        t = g.rect(0, 4, 4, 6, "कर राजस्व")
        self.assertEqual(len(g.areas[t - 1][0]), 4)

    def test_the_parameters_fit_the_manifest_and_reveal_in_steps(self):
        g, D, S = market()
        E = g.cross(D, S, "E")
        g.surplus_consumer(D, E, "बचत")
        D2 = g.shift(D, dx=2, name="D2")
        g.arrow_between(D, D2, at_y=6, label="माँग बढ़ी")
        g.hline(3, "अधिकतम मूल्य")
        g.gap(g.at_price(S, 3), g.at_price(D, 3), 3, "कमी")
        g.tick_x(E.x, "Q1")
        g.tick_y(E.y, "P1")
        E2 = g.cross(D2, S, "E2", dot=False)
        g.dot(E2.x, E2.y, "E2", glide_from=E)
        first = g.params(show=[D], areas=[], dots=[], extras=False, draw_in=1.5)
        later = g.params(show=[D, S, D2], grow=[D2, "a1"], draw_in=1.5)
        for p in (first, later):
            self.assertEqual(saanche.problems("graph", p), [], p)
        self.assertEqual(first["show"], "1")
        self.assertNotIn("hlines", first)
        self.assertEqual(later["grow"], "3,a1")
        self.assertIn("<5,5:E2", later["dots"])
        self.assertIn("2.5,7.5@3:कमी", later["gaps"])
        self.assertEqual(g.item()["draw"], "graph")

    def test_a_curve_moves_on_the_word(self):
        g, D, S = market()
        D2 = g.shift(D, dx=2, name="D2")
        k = g.tangent(D, 5)
        self.assertAlmostEqual(k, -0.8, places=4)                      # the tangent of a line is the line's slope
        g.path_points([(5, 5, "a"), (6, 6, "b")])
        p = g.params(slide={D2: (-2, 0)}, morph_from={S: D}, along=[(D, 0.5, "P={y}", 0.1)], path_upto=1, glide=1.5)
        self.assertEqual(saanche.problems("graph", p), [])
        self.assertEqual(p["slide"], "3:-2,0")
        self.assertTrue(p["morph"].startswith("2:0,9 "))
        self.assertEqual(p["along"], "1@0.5<1@0.1:P={y}")
        self.assertEqual(p["path"], "5,5:a;6,6:b")
        self.assertEqual(p["pathUpto"], 1)

    def test_limits_are_named(self):
        g = EconGraph()
        for k in range(6):
            g.linear(f"L{k}", intercept=k, slope=0.1)
        with self.assertRaises(ValueError):
            g.linear("L7", intercept=1, slope=1)
        g2 = EconGraph()
        a = g2.linear("a", intercept=1, slope=0)
        b = g2.linear("b", intercept=2, slope=0)
        with self.assertRaises(ValueError):
            g2.cross(a, b)
        with self.assertRaises(ValueError):
            g2.through("v", (1, 1), (1, 5))


if __name__ == "__main__":
    unittest.main()
