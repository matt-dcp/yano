const {
  useState
} = React;
const {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
  ComposedChart,
  Area
} = Recharts;
const D = window.__DATA__;
if (!D) {
  document.getElementById("root").innerHTML = '<div style="padding:40px;text-align:center;color:#C44D4D;font-size:18px;">No data loaded. Run <code>python build.py</code> first.</div>';
  throw new Error("No data");
}
const COLORS = {
  gold: "#C6973F",
  goldLight: "#D4AD5E",
  goldDark: "#A67C2E",
  charcoal: "#2C2C2C",
  warmGray: "#4A4A4A",
  lightGray: "#F5F1EB",
  cream: "#FAF8F4",
  white: "#FFFFFF",
  green: "#4A8C5C",
  greenLight: "#E8F2EB",
  red: "#C44D4D",
  redLight: "#F8EDED",
  blue: "#4A6FA5",
  blueLight: "#EBF0F7"
};
const PIE_COLORS = ["#C6973F", "#4A6FA5", "#4A8C5C", "#8B6BAE", "#C47D4D", "#5AABA5", "#999"];
const fmt = n => "$" + Math.round(n).toLocaleString();
const fmtK = n => "$" + (n / 1000).toFixed(0) + "K";

// ── Shared Components ──
const KPICard = ({
  label,
  value,
  sub,
  accent
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    background: COLORS.white,
    borderRadius: 12,
    padding: "20px 24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
    borderLeft: `4px solid ${accent || COLORS.gold}`,
    minWidth: 0
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12,
    fontWeight: 600,
    color: COLORS.warmGray,
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 6
  }
}, label), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 28,
    fontWeight: 700,
    color: COLORS.charcoal,
    lineHeight: 1.1
  }
}, value), sub && /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12,
    color: COLORS.warmGray,
    marginTop: 4
  }
}, sub));
const SectionTitle = ({
  children
}) => /*#__PURE__*/React.createElement("h2", {
  style: {
    fontSize: 18,
    fontWeight: 700,
    color: COLORS.charcoal,
    borderBottom: `2px solid ${COLORS.gold}`,
    paddingBottom: 8,
    marginBottom: 20,
    marginTop: 0
  }
}, children);
const CompBar = ({
  label,
  value,
  max,
  format,
  color,
  benchmark,
  benchLabel
}) => {
  const pct = value / max * 100;
  const bmPct = benchmark ? benchmark / max * 100 : null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: 13,
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      color: COLORS.charcoal
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      color: color || COLORS.gold
    }
  }, format ? format(value) : value)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height: 10,
      background: COLORS.lightGray,
      borderRadius: 5,
      overflow: "visible"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      width: `${Math.min(pct, 100)}%`,
      background: color || COLORS.gold,
      borderRadius: 5,
      transition: "width 0.5s ease"
    }
  }), bmPct && /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: -3,
      left: `${Math.min(bmPct, 100)}%`,
      width: 2,
      height: 16,
      background: COLORS.charcoal,
      borderRadius: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: -16,
      left: -20,
      fontSize: 10,
      color: COLORS.warmGray,
      whiteSpace: "nowrap"
    }
  }, benchLabel))));
};
const CustomTooltip = ({
  active,
  payload,
  label
}) => {
  if (!active || !payload?.length) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      border: `1px solid ${COLORS.lightGray}`,
      borderRadius: 8,
      padding: "10px 14px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      marginBottom: 4
    }
  }, label), payload.map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      fontSize: 12,
      color: p.color,
      display: "flex",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", null, p.name, ":"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600
    }
  }, typeof p.value === "number" && Math.abs(p.value) > 100 ? fmt(Math.abs(p.value)) : p.value))));
};

// ── Main Dashboard ──
function CasaYanoDashboard() {
  const [tab, setTab] = useState("overview");
  const S = D.summary;
  const PF = D.proForma;

  // Add colors to source data
  const sourceData = D.sourceData.map((s, i) => ({
    ...s,
    color: PIE_COLORS[i % PIE_COLORS.length]
  }));
  // Add colors to expense categories
  const expCats = D.expenseCategories.map((c, i) => ({
    ...c,
    color: PIE_COLORS[i % PIE_COLORS.length]
  }));
  const tabs = [{
    id: "overview",
    label: "Overview"
  }, {
    id: "revenue",
    label: "Revenue"
  }, {
    id: "channels",
    label: "Channels"
  }, {
    id: "units",
    label: "Units"
  }, {
    id: "expenses",
    label: "Expenses"
  }, {
    id: "proforma",
    label: "Pro Forma 2026"
  }, {
    id: "benchmark",
    label: "vs SB Market"
  }];

  // NOI calcs
  const realizedNOI = S.totalToOwner - (S.totalExpenses > 0 ? S.totalExpenses : 0);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      background: COLORS.cream,
      minHeight: "100vh"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.charcoal,
      padding: "28px 32px 20px",
      color: COLORS.white
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      flexWrap: "wrap",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: 26,
      fontWeight: 700,
      letterSpacing: -0.5
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: COLORS.gold
    }
  }, "Casa Yano"), " Performance Dashboard"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "6px 0 0",
      fontSize: 13,
      color: "#aaa"
    }
  }, "Opened ", D.openingDate, " \xB7 ", D.numUnits, " Units \xB7 Santa Barbara, CA \xB7 Updated ", new Date(D.generatedAt).toLocaleDateString())), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "rgba(198,151,63,0.15)",
      border: `1px solid ${COLORS.gold}`,
      borderRadius: 8,
      padding: "8px 16px",
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: COLORS.goldLight,
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: 1
    }
  }, "Days Since Launch"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 28,
      fontWeight: 700,
      color: COLORS.gold
    }
  }, D.daysSinceLaunch))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 4,
      marginTop: 20,
      flexWrap: "wrap"
    }
  }, tabs.map(t => /*#__PURE__*/React.createElement("button", {
    key: t.id,
    onClick: () => setTab(t.id),
    style: {
      padding: "8px 18px",
      borderRadius: "8px 8px 0 0",
      border: "none",
      background: tab === t.id ? COLORS.cream : "transparent",
      color: tab === t.id ? COLORS.charcoal : "#999",
      fontWeight: tab === t.id ? 700 : 500,
      fontSize: 13,
      cursor: "pointer",
      transition: "all 0.2s"
    }
  }, t.label)))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "24px 32px",
      maxWidth: 1200,
      margin: "0 auto"
    }
  }, tab === "overview" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 16,
      marginBottom: 32
    }
  }, /*#__PURE__*/React.createElement(KPICard, {
    label: "Total Gross Revenue",
    value: fmtK(S.totalGross),
    sub: `${S.totalBookings} total bookings`,
    accent: COLORS.gold
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Owner Revenue",
    value: fmtK(S.totalToOwner),
    sub: `${S.ownerMargin}% margin`,
    accent: COLORS.green
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Blended ADR",
    value: fmt(S.blendedAdr),
    sub: `vs $${D.config.sbMedianAdr} SB median`,
    accent: COLORS.blue
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Avg Stay",
    value: `${S.avgStay} nights`,
    sub: `${S.avgLeadTime}-day avg lead time`,
    accent: COLORS.warmGray
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Total Expenses",
    value: fmtK(S.totalExpenses),
    sub: "Tracked to date",
    accent: COLORS.red
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Realized NOI",
    value: fmtK(realizedNOI),
    sub: "Owner rev minus tracked OpEx",
    accent: COLORS.gold
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "2fr 1fr",
      gap: 24,
      marginBottom: 32
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Monthly Revenue (To Owner)"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 260
  }, /*#__PURE__*/React.createElement(ComposedChart, {
    data: D.monthlyData
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "toOwner",
    name: "To Owner",
    fill: COLORS.gold,
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Line, {
    dataKey: "adr",
    name: "ADR",
    stroke: COLORS.blue,
    strokeWidth: 2,
    dot: {
      r: 3
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Booking Sources"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 260
  }, /*#__PURE__*/React.createElement(PieChart, null, /*#__PURE__*/React.createElement(Pie, {
    data: sourceData,
    dataKey: "bookings",
    nameKey: "name",
    cx: "50%",
    cy: "50%",
    outerRadius: 85,
    innerRadius: 45,
    paddingAngle: 2,
    strokeWidth: 0
  }, sourceData.map((entry, i) => /*#__PURE__*/React.createElement(Cell, {
    key: i,
    fill: entry.color
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    formatter: (v, n) => [v + " bookings", n]
  }), /*#__PURE__*/React.createElement(Legend, {
    iconType: "circle",
    iconSize: 8,
    formatter: v => /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: COLORS.warmGray
      }
    }, v)
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: `linear-gradient(135deg, ${COLORS.charcoal}, #3a3a3a)`,
      borderRadius: 12,
      padding: 24,
      color: COLORS.white
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: COLORS.gold,
      marginBottom: 12
    }
  }, "Launch Velocity"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 20
    }
  }, [{
    label: "Bookings/Day",
    value: (S.totalBookings / D.daysSinceLaunch).toFixed(1),
    note: `${S.totalBookings} in ${D.daysSinceLaunch} days`
  }, {
    label: "Gross Rev/Day",
    value: fmt(S.totalGross / D.daysSinceLaunch),
    note: "Run-rate pace"
  }, {
    label: "Annualized Gross",
    value: fmtK(S.totalGross / D.daysSinceLaunch * 365),
    note: "If current pace holds"
  }, {
    label: "Bookings/Unit/Week",
    value: (S.totalBookings / D.numUnits / (D.daysSinceLaunch / 7)).toFixed(1),
    note: "Across 6 units"
  }].map((item, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 24,
      fontWeight: 700,
      color: COLORS.gold
    }
  }, item.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: COLORS.white,
      marginTop: 2
    }
  }, item.label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "#888",
      marginTop: 2
    }
  }, item.note)))))), tab === "revenue" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KPICard, {
    label: "Total Gross",
    value: fmtK(S.totalGross),
    accent: COLORS.gold
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Total To Owner",
    value: fmtK(S.totalToOwner),
    accent: COLORS.green
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Blended ADR",
    value: fmt(S.blendedAdr),
    accent: COLORS.blue
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Total Nights Sold",
    value: S.totalNights.toLocaleString(),
    accent: COLORS.warmGray
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Revenue by Month"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: D.monthlyData
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "gross",
    name: "Gross",
    fill: COLORS.goldLight,
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "toOwner",
    name: "To Owner",
    fill: COLORS.gold,
    radius: [4, 4, 0, 0]
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "ADR Trend"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(LineChart, {
    data: D.monthlyData
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmt,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Line, {
    dataKey: "adr",
    name: "ADR",
    stroke: COLORS.gold,
    strokeWidth: 2.5,
    dot: {
      r: 4,
      fill: COLORS.gold
    }
  })))))), tab === "channels" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KPICard, {
    label: "OTA Bookings",
    value: `${S.otaBookingPct}%`,
    sub: `${S.totalBookings - S.directBookings} of ${S.totalBookings}`,
    accent: COLORS.red
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Direct Bookings",
    value: S.directBookings.toString(),
    sub: `${(100 - S.otaBookingPct).toFixed(1)}% of total`,
    accent: COLORS.green
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Avg OTA Commission",
    value: `${S.otaPct}%`,
    sub: "Blended rate",
    accent: COLORS.blue
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Repeat Guests",
    value: `${S.repeatGuestPct}%`,
    sub: "Multiple bookings",
    accent: COLORS.warmGray
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Bookings by Source"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(PieChart, null, /*#__PURE__*/React.createElement(Pie, {
    data: sourceData,
    dataKey: "bookings",
    nameKey: "name",
    cx: "50%",
    cy: "50%",
    outerRadius: 100,
    innerRadius: 50,
    paddingAngle: 2,
    strokeWidth: 0
  }, sourceData.map((entry, i) => /*#__PURE__*/React.createElement(Cell, {
    key: i,
    fill: entry.color
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    formatter: (v, n) => [v + " bookings", n]
  }), /*#__PURE__*/React.createElement(Legend, {
    iconType: "circle",
    iconSize: 8
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Revenue by Source"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: sourceData,
    layout: "vertical"
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    type: "number",
    tickFormatter: fmtK,
    fontSize: 11
  }), /*#__PURE__*/React.createElement(YAxis, {
    type: "category",
    dataKey: "name",
    width: 100,
    fontSize: 11
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "revenue",
    name: "Revenue",
    radius: [0, 4, 4, 0]
  }, sourceData.map((entry, i) => /*#__PURE__*/React.createElement(Cell, {
    key: i,
    fill: entry.color
  }))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Channel Performance"), /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 13
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      borderBottom: `2px solid ${COLORS.gold}`
    }
  }, ["Source", "Bookings", "% of Total", "Revenue", "Avg/Booking"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: {
      padding: "8px 12px",
      textAlign: "left",
      fontWeight: 700,
      fontSize: 12,
      textTransform: "uppercase",
      letterSpacing: 0.5
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, sourceData.map((s, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      borderBottom: `1px solid ${COLORS.lightGray}`
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px",
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      width: 10,
      height: 10,
      borderRadius: "50%",
      background: s.color,
      marginRight: 8,
      verticalAlign: "middle"
    }
  }), s.name), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px"
    }
  }, s.bookings), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px"
    }
  }, s.pct, "%"), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px",
      fontWeight: 600,
      color: COLORS.gold
    }
  }, fmt(s.revenue)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px"
    }
  }, s.bookings ? fmt(s.revenue / s.bookings) : "—"))))))), tab === "units" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
      gap: 16,
      marginBottom: 24
    }
  }, D.unitData.map((u, i) => {
    const best = D.unitData.reduce((a, b) => a.toOwner > b.toOwner ? a : b);
    const isBest = u.unit === best.unit;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        background: COLORS.white,
        borderRadius: 12,
        padding: 20,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        borderLeft: `4px solid ${isBest ? COLORS.gold : COLORS.lightGray}`
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 14,
        fontWeight: 700,
        color: COLORS.charcoal,
        marginBottom: 8
      }
    }, u.unit), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 22,
        fontWeight: 700,
        color: COLORS.gold
      }
    }, fmt(u.toOwner)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: COLORS.warmGray,
        marginTop: 4
      }
    }, u.bookings, " bookings \xB7 $", u.adr, " ADR \xB7 ", u.avgStay, "n avg"), isBest && /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 10,
        color: COLORS.gold,
        fontWeight: 700,
        marginTop: 6
      }
    }, "TOP PERFORMER"));
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Revenue by Unit"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: D.unitData
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "unit",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "toOwner",
    name: "To Owner",
    fill: COLORS.gold,
    radius: [4, 4, 0, 0]
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "ADR by Unit"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: D.unitData
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "unit",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmt,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "adr",
    name: "ADR",
    fill: COLORS.blue,
    radius: [4, 4, 0, 0]
  })))))), tab === "expenses" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KPICard, {
    label: "Total Expenses",
    value: fmtK(S.totalExpenses),
    accent: COLORS.red
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Cost per Turn",
    value: fmt(S.costPerTurn),
    sub: "Cleaning cost/booking",
    accent: COLORS.warmGray
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Expense Breakdown"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(PieChart, null, /*#__PURE__*/React.createElement(Pie, {
    data: expCats,
    dataKey: "amount",
    nameKey: "category",
    cx: "50%",
    cy: "50%",
    outerRadius: 100,
    innerRadius: 50,
    paddingAngle: 2,
    strokeWidth: 0
  }, expCats.map((entry, i) => /*#__PURE__*/React.createElement(Cell, {
    key: i,
    fill: entry.color
  }))), /*#__PURE__*/React.createElement(Tooltip, {
    formatter: (v, n) => [fmt(v), n]
  }), /*#__PURE__*/React.createElement(Legend, {
    iconType: "circle",
    iconSize: 8,
    formatter: v => /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: COLORS.warmGray
      }
    }, v)
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Monthly Expenses"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 300
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: D.expenseMonthly
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "cleaning",
    name: "Cleaning",
    stackId: "a",
    fill: PIE_COLORS[0]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "supplies",
    name: "Supplies",
    stackId: "a",
    fill: PIE_COLORS[1]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "capex",
    name: "CapEx",
    stackId: "a",
    fill: PIE_COLORS[2]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "marketing",
    name: "Marketing",
    stackId: "a",
    fill: PIE_COLORS[3]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "maint",
    name: "Maintenance",
    stackId: "a",
    fill: PIE_COLORS[5]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "other",
    name: "Other",
    stackId: "a",
    fill: PIE_COLORS[6],
    radius: [4, 4, 0, 0]
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Top Vendors"), /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 13
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      borderBottom: `2px solid ${COLORS.gold}`
    }
  }, ["Vendor", "Category", "Total Spend", "% of Total"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: {
      padding: "8px 12px",
      textAlign: "left",
      fontWeight: 700,
      fontSize: 12,
      textTransform: "uppercase",
      letterSpacing: 0.5
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, D.topVendors.map((v, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      borderBottom: `1px solid ${COLORS.lightGray}`
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px",
      fontWeight: 600
    }
  }, v.vendor), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px",
      color: COLORS.warmGray
    }
  }, v.category), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px",
      fontWeight: 600,
      color: COLORS.red
    }
  }, fmt(v.amount)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "10px 12px"
    }
  }, S.totalExpenses ? (v.amount / S.totalExpenses * 100).toFixed(1) : 0, "%"))))))), tab === "proforma" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
      gap: 16,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KPICard, {
    label: "Gross Revenue",
    value: fmtK(PF.gross),
    sub: `${D.numUnits} units x ${PF.avgOcc}% occ x $${PF.avgAdr} ADR`,
    accent: COLORS.gold
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Net to Owner",
    value: fmtK(PF.netOwner),
    sub: `${(PF.netOwner / PF.gross * 100).toFixed(1)}% margin`,
    accent: COLORS.green
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Known OpEx",
    value: fmtK(PF.opex + PF.mgmtFee + PF.propertyTax + PF.insurance + (PF.otherFixed || 0)),
    sub: "Direct + mgmt + tax + ins",
    accent: COLORS.red
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "NOI (After Known Fixed)",
    value: fmtK(PF.noiAfterKnown),
    sub: `${(PF.noiAfterKnown / PF.gross * 100).toFixed(1)}% NOI margin`,
    accent: COLORS.gold
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Blended ADR",
    value: fmt(PF.avgAdr),
    accent: COLORS.blue
  }), /*#__PURE__*/React.createElement(KPICard, {
    label: "Avg Occupancy",
    value: `${PF.avgOcc}%`,
    accent: COLORS.warmGray
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Monthly P&L Forecast"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 280
  }, /*#__PURE__*/React.createElement(ComposedChart, {
    data: PF.monthly
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "gross",
    name: "Gross Revenue",
    fill: COLORS.gold,
    opacity: 0.3,
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "netOwner",
    name: "Net to Owner",
    fill: COLORS.gold,
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "opex",
    name: "OpEx",
    fill: COLORS.red,
    opacity: 0.6,
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Line, {
    dataKey: "noi",
    name: "NOI",
    stroke: COLORS.green,
    strokeWidth: 2.5,
    dot: {
      r: 3,
      fill: COLORS.green
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Seasonal ADR & Occupancy"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 280
  }, /*#__PURE__*/React.createElement(ComposedChart, {
    data: PF.monthly
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee"
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "month",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    yAxisId: "left",
    tickFormatter: fmt,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    },
    domain: [300, 600]
  }), /*#__PURE__*/React.createElement(YAxis, {
    yAxisId: "right",
    orientation: "right",
    tickFormatter: v => v + "%",
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    },
    domain: [60, 90]
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(CustomTooltip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "adr",
    name: "ADR",
    fill: COLORS.gold,
    yAxisId: "left",
    radius: [4, 4, 0, 0]
  }), /*#__PURE__*/React.createElement(Line, {
    dataKey: "occ",
    name: "Occupancy %",
    stroke: COLORS.blue,
    strokeWidth: 2.5,
    yAxisId: "right",
    dot: {
      r: 3,
      fill: COLORS.blue
    }
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Revenue Waterfall: Gross \u2192 NOI"), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 320
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: PF.waterfall.map(w => ({
      ...w,
      absValue: Math.abs(w.value)
    })),
    layout: "vertical",
    margin: {
      left: 20,
      right: 40
    }
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "#eee",
    horizontal: false
  }), /*#__PURE__*/React.createElement(XAxis, {
    type: "number",
    tickFormatter: fmtK,
    fontSize: 11,
    tick: {
      fill: COLORS.warmGray
    }
  }), /*#__PURE__*/React.createElement(YAxis, {
    type: "category",
    dataKey: "name",
    width: 170,
    fontSize: 11,
    tick: {
      fill: COLORS.charcoal,
      fontWeight: 600
    }
  }), /*#__PURE__*/React.createElement(Tooltip, {
    formatter: (v, n, p) => [fmt(Math.abs(p.payload.value)), p.payload.value < 0 ? "Deduction" : "Total"]
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: "absValue",
    name: "Amount",
    radius: [0, 4, 4, 0]
  }, PF.waterfall.map((entry, i) => {
    const fills = {
      positive: COLORS.gold,
      negative: COLORS.red,
      subtotal: COLORS.green,
      opex: "#C47D4D",
      mgmt: "#9C27B0",
      total: COLORS.green
    };
    return /*#__PURE__*/React.createElement(Cell, {
      key: i,
      fill: fills[entry.type] || COLORS.gold
    });
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: `linear-gradient(135deg, ${COLORS.charcoal}, #3a3a3a)`,
      borderRadius: 12,
      padding: 24,
      color: COLORS.white
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: COLORS.gold,
      marginBottom: 16
    }
  }, "Annual P&L Summary \u2014 2026 Pro Forma"), /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 13
    }
  }, /*#__PURE__*/React.createElement("tbody", null, [{
    label: "Gross Revenue",
    value: fmt(PF.gross),
    pct: "100%",
    bold: true,
    color: COLORS.gold
  }, {
    label: "  OTA Commissions",
    value: `(${fmt(Math.abs(PF.waterfall.find(w => w.name.includes("OTA"))?.value || 0))})`,
    indent: true
  }, {
    label: "  Taxes — TOT",
    value: `(${fmt(Math.abs(PF.waterfall.find(w => w.name.includes("Tax"))?.value || 0))})`,
    indent: true
  }, {
    label: "  Processing Fees",
    value: `(${fmt(Math.abs(PF.waterfall.find(w => w.name.includes("Process"))?.value || 0))})`,
    indent: true
  }, {
    label: "Net to Owner",
    value: fmt(PF.netOwner),
    pct: `${(PF.netOwner / PF.gross * 100).toFixed(1)}%`,
    bold: true,
    color: COLORS.green,
    sep: true
  }, {
    label: "  Direct OpEx (cleaning, supplies, etc.)",
    value: `(${fmt(PF.opex)})`,
    indent: true
  }, {
    label: "  Management Fee (10%)",
    value: `(${fmt(PF.mgmtFee)})`,
    indent: true
  }, {
    label: "  Property Tax",
    value: `(${fmt(PF.propertyTax)})`,
    indent: true
  }, {
    label: "  Insurance",
    value: `(${fmt(PF.insurance)})`,
    indent: true
  }, {
    label: "  Other Fixed (internet, bookkeeping, etc.)",
    value: `(${fmt(PF.otherFixed || 0)})`,
    indent: true
  }, {
    label: "NOI (After Known Fixed Costs)",
    value: fmt(PF.noiAfterKnown),
    pct: `${(PF.noiAfterKnown / PF.gross * 100).toFixed(1)}%`,
    bold: true,
    color: COLORS.gold,
    sep: true
  }].map((row, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      borderTop: row.sep ? "1px solid #555" : "none"
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: row.bold ? "10px 12px" : "6px 12px 6px 24px",
      fontWeight: row.bold ? 700 : 400,
      color: row.indent ? "#aaa" : COLORS.white,
      fontSize: row.bold ? 13 : 12
    }
  }, row.label), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "6px 12px",
      textAlign: "right",
      fontWeight: row.bold ? 700 : 500,
      color: row.color || "#ccc",
      fontSize: row.bold ? 14 : 12
    }
  }, row.value), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: "6px 12px",
      textAlign: "right",
      color: "#888",
      fontSize: 12
    }
  }, row.pct || ""))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "#666",
      marginTop: 16,
      fontStyle: "italic"
    }
  }, "Model driven by actual performance data. Seasonal adjustments per SB market patterns."))), tab === "benchmark" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.white,
      borderRadius: 12,
      padding: 24,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(SectionTitle, null, "Casa Yano vs Santa Barbara STR Market"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 13,
      color: COLORS.warmGray,
      marginBottom: 20,
      lineHeight: 1.6
    }
  }, "Comparison based on publicly available SB STR market data."), /*#__PURE__*/React.createElement(CompBar, {
    label: "Average Daily Rate",
    value: S.blendedAdr,
    max: 600,
    format: fmt,
    color: COLORS.gold,
    benchmark: D.config.sbMedianAdr,
    benchLabel: "SB Median"
  }), /*#__PURE__*/React.createElement(CompBar, {
    label: "Owner Margin %",
    value: S.ownerMargin,
    max: 100,
    format: v => v + "%",
    color: COLORS.green,
    benchmark: 75,
    benchLabel: "SB Typical"
  }), /*#__PURE__*/React.createElement(CompBar, {
    label: "OTA Commission Rate",
    value: S.otaPct,
    max: 20,
    format: v => v + "%",
    color: COLORS.blue,
    benchmark: 15,
    benchLabel: "Industry Avg"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 24,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.greenLight,
      borderRadius: 12,
      padding: 24,
      border: `1px solid ${COLORS.green}33`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: COLORS.green,
      marginBottom: 12
    }
  }, "Strengths"), [`ADR ${Math.round((S.blendedAdr - D.config.sbMedianAdr) / D.config.sbMedianAdr * 100)}% above SB median`, `${S.ownerMargin}% owner margin — exceptional cost efficiency`, `${S.otaPct}% blended OTA commission vs 15% industry standard`, `${S.totalBookings} bookings in ${D.daysSinceLaunch} days — strong launch`].map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      fontSize: 12,
      color: COLORS.charcoal,
      marginBottom: 8,
      paddingLeft: 16,
      position: "relative",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: 0,
      color: COLORS.green,
      fontWeight: 700
    }
  }, "+"), s))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: COLORS.redLight,
      borderRadius: 12,
      padding: 24,
      border: `1px solid ${COLORS.red}33`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: COLORS.red,
      marginBottom: 12
    }
  }, "Watch List"), [`${S.otaBookingPct}% OTA dependency — platform risk + commission drag`, `Direct bookings only ${(100 - S.otaBookingPct).toFixed(0)}% — biggest margin lever`, `Repeat guest rate at ${S.repeatGuestPct}% — early days, build loyalty`].map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      fontSize: 12,
      color: COLORS.charcoal,
      marginBottom: 8,
      paddingLeft: 16,
      position: "relative",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: 0,
      color: COLORS.red,
      fontWeight: 700
    }
  }, "!"), s)))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: `linear-gradient(135deg, ${COLORS.charcoal}, #3a3a3a)`,
      borderRadius: 12,
      padding: 24,
      color: COLORS.white
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: COLORS.gold,
      marginBottom: 12
    }
  }, "Annualized Projection (if current pace holds)"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: 20
    }
  }, [{
    label: "Annualized Gross",
    value: fmtK(S.totalGross / D.daysSinceLaunch * 365),
    note: `Based on ${fmtK(S.totalGross)} / ${D.daysSinceLaunch} days`
  }, {
    label: "Annualized To Owner",
    value: fmtK(S.totalToOwner / D.daysSinceLaunch * 365),
    note: `At ${S.ownerMargin}% margin`
  }, {
    label: "Annualized Bookings",
    value: `~${Math.round(S.totalBookings / D.daysSinceLaunch * 365).toLocaleString()}`,
    note: "At current pace"
  }].map((item, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 24,
      fontWeight: 700,
      color: COLORS.gold
    }
  }, item.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: COLORS.white,
      marginTop: 2
    }
  }, item.label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "#888",
      marginTop: 2
    }
  }, item.note)))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "#666",
      marginTop: 16,
      fontStyle: "italic"
    }
  }, "Note: Annualized figures assume current pace continues year-round. Actual results will vary seasonally.")))));
}
ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(CasaYanoDashboard));
