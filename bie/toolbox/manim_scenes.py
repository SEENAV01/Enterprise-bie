"""Manim scenes BIE renders offline (Task 046a). Parameters come from a JSON file named by BIE_MANIM_PARAMS, so a
scene is data-driven like a web block. Text uses Manim's Text (Pango), so no LaTeX installation is needed.

    BIE_MANIM_PARAMS=params.json python -m manim render -r 1280,720 --fps 30 --format mp4 bie/toolbox/manim_scenes.py FunctionDraw
"""
from __future__ import annotations

import json
import os

import numpy as np
from manim import (BLUE_B, DOWN, LEFT, ORANGE, UL, UP, WHITE, Axes, Create, Dot, FadeIn, MoveAlongPath, Scene, Text, ValueTracker,
                   always_redraw, config, linear)

BG = "#06121c"
ACCENT = "#38d3c3"
WARM = "#ffb35c"


def params() -> dict:
    path = os.environ.get("BIE_MANIM_PARAMS")
    return json.loads(open(path, encoding="utf-8").read()) if path else {}


class FunctionDraw(Scene):
    """Axes, then a function drawn from left to right with a dot riding the tip; numbers come from BIE (SymPy samples)."""

    def construct(self):
        p = params()
        config.background_color = BG
        self.camera.background_color = BG
        xs = np.array(p.get("x") or np.linspace(-2 * np.pi, 2 * np.pi, 200))
        ys = np.array(p.get("y") or np.sin(xs))
        ax = Axes(x_range=[float(xs.min()), float(xs.max()), p.get("x_step", 1.0)], y_range=[float(ys.min()) - 0.5, float(ys.max()) + 0.5, p.get("y_step", 1.0)],
                  x_length=11, y_length=5.2, axis_config={"color": BLUE_B, "include_numbers": False}, tips=False).shift(DOWN * 0.4)
        title = Text(p.get("title", "y = sin x"), font_size=40, color=WHITE).to_corner(UL)
        points = [ax.c2p(x, y) for x, y in zip(xs, ys)]
        curve = ax.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=ACCENT, stroke_width=6)["line_graph"]
        dot = Dot(points[0], color=WARM, radius=0.11)
        self.add(ax)                                       # the axes are there from the first frame; the curve is what draws
        self.play(FadeIn(title), run_time=0.8)
        self.play(Create(curve), MoveAlongPath(dot, curve), run_time=p.get("draw_seconds", 2.6), rate_func=linear)
        note = Text(p.get("note", "Manim (offline render)"), font_size=26, color=WARM).next_to(ax, UP, buff=0.1).align_to(ax, LEFT)
        self.play(FadeIn(note), run_time=0.4)
        self.wait(0.3)
