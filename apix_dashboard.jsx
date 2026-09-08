import React, { useState, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell,
} from "recharts";

// ---- Data (aggregated from the prototype pipeline's output CSVs) ----
const DAILY = [
  { d: "Jul 24", v: 110.03 }, { d: "Jul 25", v: 102.19 }, { d: "Jul 26", v: 113.88 },
  { d: "Jul 27", v: 96.21 }, { d: "Jul 28", v: 90.92 }, { d: "Jul 29", v: 91.0 },
  { d: "Jul 30", v: 95.77 }, { d: "Jul 31", v: 110.44 }, { d: "Aug 01", v: 101.87 },
  { d: "Aug 02", v: 114.71 }, { d: "Aug 03", v: 94.42 }, { d: "Aug 04", v: 92.31 },
  { d: "Aug 05", v: 90.93 }, { d: "Aug 06", v: 94.49 }, { d: "Aug 07", v: 110.04 },
  { d: "Aug 08", v: 99.56 }, { d: "Aug 09", v: 112.96 }, { d: "Aug 10", v: 95.79 },
  { d: "Aug 11", v: 91.06 }, { d: "Aug 12", v: 92.42 }, { d: "Aug 13", v: 97.19 },
  { d: "Aug 14", v: 109.5 }, { d: "Aug 15", v: 101.36 }, { d: "Aug 16", v: 114.93 },
  { d: "Aug 17", v: 96.85 }, { d: "Aug 18", v: 91.28 }, { d: "Aug 19", v: 90.59 },
  { d: "Aug 20", v: 94.89 }, { d: "Aug 21", v: 108.86 }, { d: "Aug 22", v: 102.08 },
  { d: "Aug 23", v: 114.39 }, { d: "Aug 24", v: 95.0 }, { d: "Aug 25", v: 90.68 },
  { d: "Aug 26", v: 90.72 }, { d: "Aug 27", v: 95.08 }, { d: "Aug 28", v: 109.74 },
  { d: "Aug 29", v: 99.87 }, { d: "Aug 30", v: 113.54 }, { d: "Aug 31", v: 95.84 },
  { d: "Sep 01", v: 90.05 }, { d: "Sep 02", v: 90.45 }, { d: "Sep 03", v: 95.59 },
  { d: "Sep 04", v: 111.45 }, { d: "Sep 05", v: 100.74 }, { d: "Sep 06", v: 113.4 },
];

const WEEKLY = [
  { d: "Jul 26", v: 108.7 }, { d: "Aug 02", v: 100.13 }, { d: "Aug 09", v: 99.24 },
  { d: "Aug 16", v: 100.32 }, { d: "Aug 23", v: 99.85 }, { d: "Aug 30", v: 99.23 },
  { d: "Sep 06", v: 99.64 },
];

const MONTHLY = [
  { d: "Jul 2026", v: 101.3 }, { d: "Aug 2026", v: 100.09 }, { d: "Sep 2026", v: 100.28 },
];

const HEATMAP = [
  { route: "BLR–HYD", v: 99.8 }, { route: "BOM–BLR", v: 99.9 },
  { route: "DEL–BLR", v: 100.1 }, { route: "DEL–BOM", v: 98.9 },
  { route: "DEL–CCU", v: 102.3 }, { route: "MAA–DEL", v: 97.1 },
];

const ELASTICITY = [
  { window: "T+1", fare: 10455 }, { window: "T+7", fare: 8275 },
  { window: "T+15", fare: 6599 }, { window: "T+30", fare: 5510 },
  { window: "T+45", fare: 4685 },
];

// ---- Design tokens ----
const INK = "#1B2A41";
const PAPER = "#FCFCFA";
const GOLD = "#B08D2B";
const BRICK = "#A64B3D";
const TEAL = "#3F7566";
const SLATE = "#6B7A8F";
const HAIRLINE = "#DCD9D0";

function heatColor(v) {
  // interpolate teal (below 100) -> paper (at 100) -> brick (above 100)
  const clamped = Math.max(96, Math.min(104, v));
  if (clamped <= 100) {
    const t = (clamped - 96) / 4;
    return mix(TEAL, "#EDEAE0", t);
  }
  const t = (clamped - 100) / 4;
  return mix("#EDEAE0", BRICK, t);
}
function mix(hexA, hexB, t) {
  const a = hexA.match(/\w\w/g).map((h) => parseInt(h, 16));
  const b = hexB.match(/\w\w/g).map((h) => parseInt(h, 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

const FREQ = { Daily: DAILY, Weekly: WEEKLY, Monthly: MONTHLY };

export default function APIxDashboard() {
  const [freq, setFreq] = useState("Daily");
  const data = FREQ[freq];
  const latest = DAILY[DAILY.length - 1].v;
  const change = latest - 100;
  const rising = change >= 0;

  const elasticityMax = useMemo(() => Math.max(...ELASTICITY.map((e) => e.fare)), []);

  return (
    <div style={{
      background: PAPER, color: INK, fontFamily: "Georgia, 'Iowan Old Style', serif",
      padding: "28px 24px 20px", maxWidth: 720, margin: "0 auto",
    }}>
      {/* Masthead */}
      <div style={{ borderBottom: `2px solid ${INK}`, paddingBottom: 12, marginBottom: 20 }}>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: 0.2 }}>
          Airfare Price Index
        </div>
        <div style={{
          fontFamily: "system-ui, -apple-system, sans-serif", fontSize: 12.5,
          color: SLATE, marginTop: 3,
        }}>
          Prototype augmentation to the Consumer Price Index — simulated data, internal-round demo
        </div>
      </div>

      {/* Hero number */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginBottom: 6 }}>
        <div style={{
          fontSize: 52, fontWeight: 700, lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
        }}>
          {latest.toFixed(1)}
        </div>
        <div style={{
          fontFamily: "system-ui, -apple-system, sans-serif", fontSize: 15,
          color: rising ? BRICK : TEAL, fontWeight: 600,
        }}>
          {rising ? "▲" : "▼"} {Math.abs(change).toFixed(1)} vs base period
        </div>
      </div>
      <div style={{
        fontFamily: "system-ui, -apple-system, sans-serif", fontSize: 12.5,
        color: SLATE, marginBottom: 22,
      }}>
        As of Sep 6, 2026 · base period (first 7 days) = 100
      </div>

      {/* Frequency toggle + trend chart */}
      <div style={{
        display: "flex", gap: 6, marginBottom: 10,
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}>
        {Object.keys(FREQ).map((f) => (
          <button
            key={f}
            onClick={() => setFreq(f)}
            style={{
              padding: "5px 12px", fontSize: 13, cursor: "pointer",
              background: freq === f ? INK : "transparent",
              color: freq === f ? PAPER : INK,
              border: `1px solid ${INK}`, borderRadius: 0,
            }}
          >
            {f}
          </button>
        ))}
      </div>

      <div style={{ width: "100%", height: 220, marginBottom: 26 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke={HAIRLINE} vertical={false} />
            <XAxis
              dataKey="d" tick={{ fontSize: 10.5, fill: SLATE, fontFamily: "system-ui" }}
              axisLine={{ stroke: HAIRLINE }} tickLine={false}
              interval={freq === "Daily" ? 6 : 0}
            />
            <YAxis
              domain={[85, 120]} tick={{ fontSize: 10.5, fill: SLATE, fontFamily: "system-ui" }}
              axisLine={false} tickLine={false}
            />
            <ReferenceLine y={100} stroke={SLATE} strokeDasharray="3 3" />
            <Tooltip
              contentStyle={{
                background: INK, border: "none", fontFamily: "system-ui", fontSize: 12,
              }}
              labelStyle={{ color: PAPER }} itemStyle={{ color: GOLD }}
              formatter={(v) => [v.toFixed(2), "APIx"]}
            />
            <Line type="monotone" dataKey="v" stroke={GOLD} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Two-column: heatmap + elasticity */}
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 260px" }}>
          <SectionLabel>Route-wise sub-index (7-day avg)</SectionLabel>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 10 }}>
            {HEATMAP.map((h) => (
              <div key={h.route} style={{
                background: heatColor(h.v), padding: "10px 12px",
                border: `1px solid ${HAIRLINE}`,
              }}>
                <div style={{
                  fontFamily: "system-ui, sans-serif", fontSize: 11, color: INK, opacity: 0.75,
                }}>
                  {h.route}
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
                  {h.v.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: "1 1 260px" }}>
          <SectionLabel>Lead-time elasticity (avg fare)</SectionLabel>
          <div style={{ width: "100%", height: 180, marginTop: 6 }}>
            <ResponsiveContainer>
              <BarChart data={ELASTICITY} margin={{ top: 10, right: 4, left: -18, bottom: 0 }}>
                <CartesianGrid stroke={HAIRLINE} vertical={false} />
                <XAxis
                  dataKey="window" tick={{ fontSize: 10.5, fill: SLATE, fontFamily: "system-ui" }}
                  axisLine={{ stroke: HAIRLINE }} tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10.5, fill: SLATE, fontFamily: "system-ui" }}
                  axisLine={false} tickLine={false}
                />
                <Tooltip
                  contentStyle={{ background: INK, border: "none", fontFamily: "system-ui", fontSize: 12 }}
                  labelStyle={{ color: PAPER }} itemStyle={{ color: GOLD }}
                  formatter={(v) => [`₹${v.toLocaleString("en-IN")}`, "Avg fare"]}
                />
                <Bar dataKey="fare" radius={0}>
                  {ELASTICITY.map((e, i) => (
                    <Cell key={i} fill={e.fare === elasticityMax ? BRICK : GOLD} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${HAIRLINE}`, marginTop: 26, paddingTop: 10,
        fontFamily: "system-ui, -apple-system, sans-serif", fontSize: 11, color: SLATE,
        lineHeight: 1.5,
      }}>
        Method: weighted price relative across a 6-route basket (Laspeyres-style), base period = first 7 days = 100.
        Weights are illustrative — to be replaced with DGCA passenger-traffic shares.
      </div>
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <div style={{
      fontFamily: "system-ui, -apple-system, sans-serif", fontSize: 12.5,
      color: INK, fontWeight: 600,
    }}>
      {children}
    </div>
  );
}
