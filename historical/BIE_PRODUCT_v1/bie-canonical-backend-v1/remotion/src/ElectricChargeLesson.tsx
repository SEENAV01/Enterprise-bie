import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/*
  LESSON 01 — ELECTRIC CHARGE

  Production philosophy:
  - No fixed "60 second" constraint.
  - Each scene exists for a learning purpose.
  - Visual continuity between scenes.
  - Source-grounded facts.
  - Conceptual enrichment is presented visually, not falsely attributed
    to the source.

  Source facts used:
  - Positive / negative charge
  - Electric field
  - q
  - Coulomb (C)
  - q = ne
  - e = 1.6 × 10^-19 C

  Lesson ends by naturally introducing Electric Field.
*/

const COLORS = {
  bg: "#050812",
  panel: "#0B1220",
  white: "#F8FAFC",
  muted: "#94A3B8",
  cyan: "#38BDF8",
  positive: "#FB7185",
  negative: "#60A5FA",
  green: "#34D399",
  yellow: "#FBBF24",
};

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const ease = (x: number) =>
  x * x * (3 - 2 * x);

const progress = (
  frame: number,
  start: number,
  end: number
) =>
  interpolate(frame, [start, end], [0, 1], clamp);

const Charge = ({
  x,
  y,
  type,
  scale = 1,
  glow = true,
}: {
  x: number;
  y: number;
  type: "+" | "-";
  scale?: number;
  glow?: boolean;
}) => {
  const color =
    type === "+"
      ? COLORS.positive
      : COLORS.negative;

  return (
    <g
      transform={`translate(${x} ${y}) scale(${scale})`}
    >
      {glow && (
        <circle
          r="100"
          fill={color}
          opacity="0.08"
        />
      )}

      <circle
        r="55"
        fill="#0B1220"
        stroke={color}
        strokeWidth="3"
      />

      <circle
        r="44"
        fill={color}
        opacity="0.11"
      />

      <text
        textAnchor="middle"
        y="18"
        fill={COLORS.white}
        fontSize="62"
        fontWeight="700"
        fontFamily="Inter, system-ui, sans-serif"
      >
        {type}
      </text>
    </g>
  );
};

const Title = ({
  eyebrow,
  title,
  opacity = 1,
}: {
  eyebrow: string;
  title: string;
  opacity?: number;
}) => (
  <div
    style={{
      position: "absolute",
      top: 90,
      left: 120,
      opacity,
      fontFamily: "Inter, system-ui, sans-serif",
    }}
  >
    <div
      style={{
        color: COLORS.cyan,
        fontSize: 17,
        fontWeight: 800,
        letterSpacing: 5,
      }}
    >
      {eyebrow}
    </div>

    <div
      style={{
        marginTop: 15,
        color: COLORS.white,
        fontSize: 54,
        fontWeight: 850,
        letterSpacing: -2,
      }}
    >
      {title}
    </div>
  </div>
);

const FadeText = ({
  children,
  opacity,
  style = {},
}: {
  children: React.ReactNode;
  opacity: number;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      opacity,
      color: COLORS.white,
      fontFamily: "Inter, system-ui, sans-serif",
      ...style,
    }}
  >
    {children}
  </div>
);

/* -------------------------------------------------------------
   SCENE 01 — MYSTERY
------------------------------------------------------------- */

const Scene01 = ({ frame }: { frame: number }) => {
  const p = ease(progress(frame, 0, 70));

  const separation = ease(
    progress(frame, 80, 250)
  );

  const leftX =
    960 - interpolate(
      separation,
      [0, 1],
      [105, 340]
    );

  const rightX =
    960 + interpolate(
      separation,
      [0, 1],
      [105, 340]
    );

  const question =
    progress(frame, 240, 310);

  return (
    <>
      <Title
        eyebrow="PHYSICS • ELECTRICITY"
        title="Something is happening."
        opacity={p}
      />

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        <Charge
          x={leftX}
          y={545}
          type="+"
          scale={1.2}
        />

        <Charge
          x={rightX}
          y={545}
          type="+"
          scale={1.2}
        />

        {/* subtle force arrows */}
        {frame > 140 && (
          <>
            <line
              x1={leftX - 75}
              y1={545}
              x2={leftX - 180}
              y2={545}
              stroke={COLORS.cyan}
              strokeWidth="5"
              strokeLinecap="round"
              opacity={0.7}
            />

            <line
              x1={rightX + 75}
              y1={545}
              x2={rightX + 180}
              y2={545}
              stroke={COLORS.cyan}
              strokeWidth="5"
              strokeLinecap="round"
              opacity={0.7}
            />
          </>
        )}
      </svg>

      <FadeText
        opacity={question}
        style={{
          position: "absolute",
          bottom: 125,
          width: "100%",
          textAlign: "center",
          fontSize: 27,
          fontWeight: 700,
          letterSpacing: 2,
        }}
      >
        WHY ARE THE OBJECTS MOVING?
      </FadeText>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 02 — PREDICTION
------------------------------------------------------------- */

const Scene02 = ({ frame }: { frame: number }) => {
  const local = frame - 320;

  const inP = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 18,
      stiffness: 90,
    },
  });

  const answer = progress(local, 160, 220);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          textAlign: "center",
          transform: `scale(${interpolate(
            inP,
            [0, 1],
            [0.88, 1]
          )})`,
          opacity: inP,
        }}
      >
        <div
          style={{
            color: COLORS.cyan,
            fontSize: 18,
            fontWeight: 800,
            letterSpacing: 5,
          }}
        >
          MAKE A PREDICTION
        </div>

        <div
          style={{
            marginTop: 25,
            color: COLORS.white,
            fontSize: 60,
            fontWeight: 850,
          }}
        >
          What happens when
          <br />
          charges interact?
        </div>

        <div
          style={{
            display: "flex",
            gap: 25,
            justifyContent: "center",
            marginTop: 60,
          }}
        >
          {["ATTRACT", "REPEL"].map(
            (answerText, i) => (
              <div
                key={answerText}
                style={{
                  padding: "20px 60px",
                  border:
                    i === 1
                      ? `2px solid ${COLORS.positive}`
                      : "2px solid #334155",
                  borderRadius: 16,
                  color: COLORS.white,
                  fontSize: 23,
                  fontWeight: 750,
                }}
              >
                {answerText}
              </div>
            )
          )}
        </div>

        <div
          style={{
            marginTop: 45,
            opacity: answer,
            color: COLORS.positive,
            fontSize: 31,
            fontWeight: 850,
            letterSpacing: 3,
          }}
        >
          LIKE CHARGES → REPEL
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------
   SCENE 03 — REVEAL
------------------------------------------------------------- */

const Scene03 = ({ frame }: { frame: number }) => {
  const local = frame - 540;

  const reveal = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 20,
      stiffness: 80,
    },
  });

  return (
    <>
      <Title
        eyebrow="THE REVEAL"
        title="Electric Charge"
        opacity={reveal}
      />

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        <circle
          cx="960"
          cy="540"
          r={230 * reveal}
          fill={COLORS.cyan}
          opacity={0.045}
        />

        <Charge
          x={960}
          y={540}
          type="+"
          scale={1.5 * reveal}
        />
      </svg>

      <FadeText
        opacity={reveal}
        style={{
          position: "absolute",
          bottom: 150,
          width: "100%",
          textAlign: "center",
          color: COLORS.muted,
          fontSize: 24,
        }}
      >
        A property of matter associated with
        electric phenomena.
      </FadeText>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 04 — TWO TYPES
------------------------------------------------------------- */

const Scene04 = ({ frame }: { frame: number }) => {
  const local = frame - 700;

  const p = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 18,
      stiffness: 90,
    },
  });

  return (
    <>
      <Title
        eyebrow="TWO FORMS"
        title="Positive and Negative"
        opacity={p}
      />

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        <Charge
          x={620}
          y={550}
          type="+"
          scale={1.45 * p}
        />

        <Charge
          x={1300}
          y={550}
          type="-"
          scale={1.45 * p}
        />
      </svg>

      <div
        style={{
          position: "absolute",
          top: 730,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          gap: 390,
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        <div
          style={{
            color: COLORS.positive,
            fontSize: 25,
            fontWeight: 800,
            letterSpacing: 3,
          }}
        >
          POSITIVE
        </div>

        <div
          style={{
            color: COLORS.negative,
            fontSize: 25,
            fontWeight: 800,
            letterSpacing: 3,
          }}
        >
          NEGATIVE
        </div>
      </div>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 05 — INTERACTION LAB
------------------------------------------------------------- */

const Scene05 = ({ frame }: { frame: number }) => {
  const local = frame - 900;

  const cycle = local % 320;

  const repel =
    cycle < 160;

  const t = ease(
    interpolate(
      repel ? cycle : cycle - 160,
      [15, 145],
      [0, 1],
      clamp
    )
  );

  const distance = repel
    ? interpolate(t, [0, 1], [190, 520])
    : interpolate(t, [0, 1], [520, 190]);

  const left = 960 - distance / 2;
  const right = 960 + distance / 2;

  return (
    <>
      <Title
        eyebrow="INTERACTION LAB"
        title={
          repel
            ? "Like charges move apart"
            : "Unlike charges move together"
        }
        opacity={1}
      />

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        <Charge
          x={left}
          y={540}
          type="+"
          scale={1.15}
        />

        <Charge
          x={right}
          y={540}
          type={repel ? "+" : "-"}
          scale={1.15}
        />

        <line
          x1={left}
          y1={540}
          x2={right}
          y2={540}
          stroke="#334155"
          strokeWidth="2"
          strokeDasharray="8 12"
        />
      </svg>

      <div
        style={{
          position: "absolute",
          bottom: 125,
          width: "100%",
          textAlign: "center",
          color: repel
            ? COLORS.positive
            : COLORS.cyan,
          fontSize: 30,
          fontWeight: 850,
          letterSpacing: 4,
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        {repel
          ? "REPEL"
          : "ATTRACT"}
      </div>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 06 — QUANTISATION
------------------------------------------------------------- */

const Scene06 = ({ frame }: { frame: number }) => {
  const local = frame - 1220;

  const count = Math.min(
    6,
    Math.floor(
      interpolate(local, [20, 160], [0, 6], clamp)
    )
  );

  const equation = progress(local, 175, 240);

  return (
    <>
      <Title
        eyebrow="HOW MUCH CHARGE?"
        title="Build it from elementary charge"
        opacity={1}
      />

      <div
        style={{
          position: "absolute",
          top: 410,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          gap: 22,
        }}
      >
        {Array.from({ length: count }).map(
          (_, i) => (
            <div
              key={i}
              style={{
                width: 72,
                height: 72,
                borderRadius: "50%",
                border: `3px solid ${COLORS.positive}`,
                background: `${COLORS.positive}12`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: COLORS.white,
                fontSize: 30,
                fontWeight: 800,
                boxShadow:
                  `0 0 35px ${COLORS.positive}20`,
              }}
            >
              e
            </div>
          )
        )}
      </div>

      <FadeText
        opacity={progress(local, 90, 145)}
        style={{
          position: "absolute",
          top: 535,
          width: "100%",
          textAlign: "center",
          color: COLORS.muted,
          fontSize: 22,
        }}
      >
        n = number of electrons
      </FadeText>

      <FadeText
        opacity={equation}
        style={{
          position: "absolute",
          top: 635,
          width: "100%",
          textAlign: "center",
          fontSize: 70,
          fontWeight: 850,
          letterSpacing: 4,
        }}
      >
        q = ne
      </FadeText>

      <FadeText
        opacity={equation}
        style={{
          position: "absolute",
          top: 750,
          width: "100%",
          textAlign: "center",
          color: COLORS.muted,
          fontSize: 24,
        }}
      >
        e = 1.6 × 10⁻¹⁹ C
      </FadeText>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 07 — COULOMB
------------------------------------------------------------- */

const Scene07 = ({ frame }: { frame: number }) => {
  const local = frame - 1530;

  const p = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 20,
      stiffness: 80,
    },
  });

  const line = progress(local, 65, 125);

  return (
    <>
      <Title
        eyebrow="MEASUREMENT"
        title="How do we measure charge?"
        opacity={p}
      />

      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 60,
            transform: `scale(${interpolate(
              p,
              [0, 1],
              [0.8, 1]
            )})`,
          }}
        >
          <div
            style={{
              color: COLORS.white,
              fontSize: 90,
              fontWeight: 850,
            }}
          >
            q
          </div>

          <div
            style={{
              width: 120,
              height: 3,
              background: COLORS.cyan,
              transformOrigin: "left",
              transform: `scaleX(${line})`,
            }}
          />

          <div
            style={{
              textAlign: "center",
            }}
          >
            <div
              style={{
                color: COLORS.cyan,
                fontSize: 45,
                fontWeight: 850,
              }}
            >
              COULOMB
            </div>

            <div
              style={{
                marginTop: 12,
                color: COLORS.muted,
                fontSize: 25,
              }}
            >
              C
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 08 — CHARGE MICROSCOPE
------------------------------------------------------------- */

const Scene08 = ({ frame }: { frame: number }) => {
  const local = frame - 1740;

  const zoom = interpolate(
    local,
    [0, 150],
    [1, 2.5],
    clamp
  );

  const info = progress(local, 130, 190);

  return (
    <>
      <Title
        eyebrow="ZOOM IN"
        title="One elementary charge"
        opacity={1}
      />

      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 530,
          transform: `translate(-50%, -50%) scale(${zoom})`,
          width: 130,
          height: 130,
          borderRadius: "50%",
          border: `4px solid ${COLORS.positive}`,
          background: `${COLORS.positive}12`,
          boxShadow:
            `0 0 80px ${COLORS.positive}35`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          color: COLORS.white,
          fontSize: 48,
          fontWeight: 800,
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        e
      </div>

      <FadeText
        opacity={info}
        style={{
          position: "absolute",
          bottom: 170,
          width: "100%",
          textAlign: "center",
          fontSize: 29,
          fontWeight: 700,
        }}
      >
        e = 1.6 × 10⁻¹⁹ C
      </FadeText>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 09 — PAYOFF
------------------------------------------------------------- */

const Scene09 = ({ frame }: { frame: number }) => {
  const local = frame - 1980;

  const p = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 20,
      stiffness: 70,
    },
  });

  return (
    <>
      <Title
        eyebrow="PUT IT TOGETHER"
        title="Now the mystery makes sense."
        opacity={p}
      />

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        <Charge
          x={700}
          y={530}
          type="+"
          scale={1.2}
        />

        <Charge
          x={1220}
          y={530}
          type="+"
          scale={1.2}
        />

        <line
          x1="760"
          y1="530"
          x2="1160"
          y2="530"
          stroke={COLORS.cyan}
          strokeWidth="4"
          strokeDasharray="10 12"
          opacity={p}
        />
      </svg>

      <div
        style={{
          position: "absolute",
          bottom: 140,
          width: "100%",
          textAlign: "center",
          fontFamily: "Inter, system-ui, sans-serif",
          color: COLORS.positive,
          fontSize: 34,
          fontWeight: 850,
          letterSpacing: 4,
        }}
      >
        CHARGE → INTERACTION
      </div>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 10 — CHARGE LAB
------------------------------------------------------------- */

const Scene10 = ({ frame }: { frame: number }) => {
  const local = frame - 2180;

  const cycle =
    Math.floor(Math.max(0, local) / 240) % 2;

  const challenge =
    cycle === 0
      ? "LIKE CHARGES"
      : "UNLIKE CHARGES";

  const answered =
    local % 240 > 125;

  return (
    <>
      <Title
        eyebrow="REVISION LAB"
        title="You decide what happens."
        opacity={1}
      />

      <div
        style={{
          position: "absolute",
          top: 330,
          width: "100%",
          textAlign: "center",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        <div
          style={{
            color: COLORS.muted,
            fontSize: 22,
            letterSpacing: 3,
          }}
        >
          {challenge}
        </div>

        <div
          style={{
            marginTop: 35,
            fontSize: 42,
            color: COLORS.white,
            fontWeight: 800,
          }}
        >
          What should happen?
        </div>

        <div
          style={{
            marginTop: 55,
            display: "flex",
            justifyContent: "center",
            gap: 25,
          }}
        >
          <div
            style={{
              padding: "20px 45px",
              border: `2px solid ${
                answered && cycle === 0
                  ? COLORS.green
                  : "#334155"
              }`,
              borderRadius: 15,
              color: COLORS.white,
              fontSize: 22,
              fontWeight: 750,
            }}
          >
            ATTRACT
          </div>

          <div
            style={{
              padding: "20px 45px",
              border: `2px solid ${
                answered && cycle === 1
                  ? COLORS.green
                  : "#334155"
              }`,
              borderRadius: 15,
              color: COLORS.white,
              fontSize: 22,
              fontWeight: 750,
            }}
          >
            REPEL
          </div>
        </div>

        {answered && (
          <div
            style={{
              marginTop: 45,
              color: COLORS.green,
              fontSize: 28,
              fontWeight: 850,
              letterSpacing: 3,
            }}
          >
            {cycle === 0
              ? "REPEL"
              : "ATTRACT"}
          </div>
        )}
      </div>
    </>
  );
};

/* -------------------------------------------------------------
   SCENE 11 — MEMORY LOCK
------------------------------------------------------------- */

const Scene11 = ({ frame }: { frame: number }) => {
  const local = frame - 2420;

  const p = spring({
    frame: Math.max(0, local),
    fps: 30,
    config: {
      damping: 22,
      stiffness: 75,
    },
  });

  return (
    <>
      <Title
        eyebrow="MEMORY LOCK"
        title="Electric Charge — one mental model"
        opacity={p}
      />

      <div
        style={{
          position: "absolute",
          left: 300,
          top: 320,
          width: 1320,
          fontFamily: "Inter, system-ui, sans-serif",
          opacity: p,
        }}
      >
        <div
          style={{
            textAlign: "center",
            color: COLORS.cyan,
            fontSize: 34,
            fontWeight: 850,
            marginBottom: 35,
          }}
        >
          ELECTRIC CHARGE
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 25,
          }}
        >
          <MemoryBox
            title="Positive"
            value="+"
            color={COLORS.positive}
          />

          <MemoryBox
            title="Negative"
            value="−"
            color={COLORS.negative}
          />

          <MemoryBox
            title="Symbol"
            value="q"
            color={COLORS.cyan}
          />

          <MemoryBox
            title="SI unit"
            value="Coulomb (C)"
            color={COLORS.yellow}
          />
        </div>

        <div
          style={{
            marginTop: 25,
            padding: 30,
            borderRadius: 20,
            border: "1px solid #334155",
            textAlign: "center",
            color: COLORS.white,
            fontSize: 42,
            fontWeight: 800,
          }}
        >
          q = ne
        </div>
      </div>
    </>
  );
};

const MemoryBox = ({
  title,
  value,
  color,
}: {
  title: string;
  value: string;
  color: string;
}) => (
  <div
    style={{
      padding: 25,
      borderRadius: 18,
      background: "#0B1220",
      border: `2px solid ${color}55`,
      textAlign: "center",
    }}
  >
    <div
      style={{
        color: COLORS.muted,
        fontSize: 16,
        letterSpacing: 2,
      }}
    >
      {title.toUpperCase()}
    </div>

    <div
      style={{
        marginTop: 10,
        color,
        fontSize: 30,
        fontWeight: 850,
      }}
    >
      {value}
    </div>
  </div>
);

/* -------------------------------------------------------------
   SCENE 12 — ELECTRIC FIELD BRIDGE
------------------------------------------------------------- */

const Scene12 = ({ frame }: { frame: number }) => {
  const local = frame - 2700;

  const reveal = progress(local, 0, 150);

  const fieldOpacity = progress(
    local,
    80,
    230
  );

  const titleOpacity = progress(
    local,
    210,
    280
  );

  const lines = Array.from({
    length: 12,
  });

  return (
    <>
      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
        }}
      >
        {/* central charge */}

        <Charge
          x={960}
          y={540}
          type="+"
          scale={1.25}
        />

        {/* conceptual field visualization */}

        {lines.map((_, i) => {
          const angle =
            (i / lines.length) *
            Math.PI *
            2;

          const x1 =
            960 + Math.cos(angle) * 90;

          const y1 =
            540 + Math.sin(angle) * 90;

          const x2 =
            960 + Math.cos(angle) * 330;

          const y2 =
            540 + Math.sin(angle) * 330;

          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={COLORS.cyan}
              strokeWidth="3"
              opacity={
                fieldOpacity * reveal
              }
            />
          );
        })}
      </svg>

      <FadeText
        opacity={titleOpacity}
        style={{
          position: "absolute",
          top: 170,
          width: "100%",
          textAlign: "center",
          fontSize: 68,
          fontWeight: 900,
          letterSpacing: -2,
        }}
      >
        Electric Field
      </FadeText>

      <FadeText
        opacity={titleOpacity}
        style={{
          position: "absolute",
          bottom: 130,
          width: "100%",
          textAlign: "center",
          color: COLORS.muted,
          fontSize: 24,
        }}
      >
        The region around an electric charge
        where its effect can be felt.
      </FadeText>
    </>
  );
};

/* -------------------------------------------------------------
   MAIN LESSON
------------------------------------------------------------- */

export const ElectricChargeLesson: React.FC = () => {
  const frame = useCurrentFrame();

  /*
    Deliberately generous scene durations.

    Total:
    2980 frames
    ≈ 99 seconds at 30fps.

    This is NOT a target duration.
    Content determines duration.
  */

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        overflow: "hidden",
        fontFamily:
          "Inter, system-ui, sans-serif",
      }}
    >
      {/* ambient atmosphere */}

      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 45%, rgba(56,189,248,0.045), transparent 48%)",
        }}
      />

      {/* subtle grid */}

      <svg
        width="1920"
        height="1080"
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.055,
        }}
      >
        <defs>
          <pattern
            id="lessonGrid"
            width="80"
            height="80"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 80 0 L 0 0 0 80"
              fill="none"
              stroke="#64748B"
              strokeWidth="1"
            />
          </pattern>
        </defs>

        <rect
          width="100%"
          height="100%"
          fill="url(#lessonGrid)"
        />
      </svg>

      {/* SCENE SWITCHER */}

      {frame < 320 && (
        <Scene01 frame={frame} />
      )}

      {frame >= 320 && frame < 540 && (
        <Scene02 frame={frame} />
      )}

      {frame >= 540 && frame < 700 && (
        <Scene03 frame={frame} />
      )}

      {frame >= 700 && frame < 900 && (
        <Scene04 frame={frame} />
      )}

      {frame >= 900 && frame < 1220 && (
        <Scene05 frame={frame} />
      )}

      {frame >= 1220 && frame < 1530 && (
        <Scene06 frame={frame} />
      )}

      {frame >= 1530 && frame < 1740 && (
        <Scene07 frame={frame} />
      )}

      {frame >= 1740 && frame < 1980 && (
        <Scene08 frame={frame} />
      )}

      {frame >= 1980 && frame < 2180 && (
        <Scene09 frame={frame} />
      )}

      {frame >= 2180 && frame < 2420 && (
        <Scene10 frame={frame} />
      )}

      {frame >= 2420 && frame < 2700 && (
        <Scene11 frame={frame} />
      )}

      {frame >= 2700 && (
        <Scene12 frame={frame} />
      )}

      {/* cinematic vignette */}

      <AbsoluteFill
        style={{
          pointerEvents: "none",
          boxShadow:
            "inset 0 0 180px rgba(0,0,0,0.72)",
        }}
      />
    </AbsoluteFill>
  );
};