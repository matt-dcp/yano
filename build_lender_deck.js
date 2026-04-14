const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";
pres.author = "Driven Capital Partners";
pres.title = "Casa Yano — Lender Presentation";

const C = {
  dark: "2D2D2D", gold: "C5A55A", white: "FFFFFF", light: "F5F5F5",
  green: "4CAF50", blue: "2196F3", gray: "9E9E9E", warmGray: "888888",
  darkGold: "A68A3E", lightGold: "F5ECD7",
};

// ═══════════════════════════════════════════════════
// SLIDE 1: Cover
// ═══════════════════════════════════════════════════
let s1 = pres.addSlide();
s1.background = { color: C.dark };

// Gold accent bar at top
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.gold } });

s1.addText("Casa Yano", {
  x: 0.8, y: 1.2, w: 8.4, h: 1.2,
  fontSize: 54, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});
s1.addText("210 W Yanonali St, Santa Barbara, CA 93101", {
  x: 0.8, y: 2.4, w: 8.4, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: C.white, margin: 0
});
s1.addText("6-Unit Short-Term Rental", {
  x: 0.8, y: 2.95, w: 8.4, h: 0.45,
  fontSize: 16, fontFace: "Arial", color: C.warmGray, margin: 0
});

// Bottom section
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.6, w: 10, h: 0.015, fill: { color: C.gold, transparency: 50 } });
s1.addText("Lender Presentation  \u2014  April 2026", {
  x: 0.8, y: 4.75, w: 5, h: 0.4,
  fontSize: 13, fontFace: "Arial", color: C.warmGray, margin: 0
});
s1.addText("Prepared by Driven Capital Partners", {
  x: 0.8, y: 5.1, w: 5, h: 0.35,
  fontSize: 11, fontFace: "Arial", color: C.warmGray, italic: true, margin: 0
});


// ═══════════════════════════════════════════════════
// SLIDE 2: Investment Summary
// ═══════════════════════════════════════════════════
let s2 = pres.addSlide();
s2.background = { color: C.white };

// Title bar
s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.dark } });
s2.addText("Investment Summary", {
  x: 0.8, y: 0.1, w: 8, h: 0.7,
  fontSize: 24, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});

// Story bullets (left side)
s2.addText([
  { text: "Acquired March 2024", options: { bold: true, breakLine: true, fontSize: 12 } },
  { text: "Purchase price: $2,475,000", options: { breakLine: true, fontSize: 11, color: C.warmGray } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "Full Gut Renovation", options: { bold: true, breakLine: true, fontSize: 12 } },
  { text: "Hard costs: $1,406K  |  Soft costs: $160K  (Oct 2024 \u2013 Nov 2025)", options: { breakLine: true, fontSize: 11, color: C.warmGray } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "Operations Commenced Dec 18, 2025", options: { bold: true, breakLine: true, fontSize: 12 } },
  { text: "111 days operating with strong revenue ramp", options: { breakLine: true, fontSize: 11, color: C.warmGray } },
  { text: "", options: { breakLine: true, fontSize: 6 } },
  { text: "Seeking Refinance", options: { bold: true, breakLine: true, fontSize: 12 } },
  { text: "Recapitalize construction basis with stabilized debt", options: { fontSize: 11, color: C.warmGray } },
], { x: 0.8, y: 1.15, w: 4.8, h: 3.5, fontFace: "Arial", color: C.dark, valign: "top" });

// Key metrics card (right side)
s2.addShape(pres.shapes.RECTANGLE, {
  x: 6.0, y: 1.15, w: 3.5, h: 3.8,
  fill: { color: C.light },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.08 }
});
s2.addText("KEY METRICS", {
  x: 6.2, y: 1.3, w: 3.1, h: 0.35,
  fontSize: 10, fontFace: "Arial", color: C.warmGray, bold: true, charSpacing: 3, margin: 0
});
s2.addShape(pres.shapes.RECTANGLE, { x: 6.2, y: 1.65, w: 3.1, h: 0.015, fill: { color: C.gold } });

const metrics = [
  ["Total Basis (QBO)", "$4,200,000"],
  ["Existing Debt", "$1,500,000"],
  ["2026 NOI (Projected)", "$356,201"],
  ["Return on Cost", "8.5%"],
  ["Implied Value (6% Cap)", "$5,937,000"],
];
let my = 1.85;
for (const [label, val] of metrics) {
  s2.addText(label, { x: 6.3, y: my, w: 2.0, h: 0.35, fontSize: 10, fontFace: "Arial", color: C.warmGray, margin: 0 });
  s2.addText(val, { x: 8.0, y: my, w: 1.2, h: 0.35, fontSize: 11, fontFace: "Arial", color: C.dark, bold: true, align: "right", margin: 0 });
  my += 0.38;
}

// Bottom highlight bar
s2.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 4.75, w: 8.4, h: 0.55, fill: { color: C.lightGold } });
s2.addText([
  { text: "Total Basis: $4.2M", options: { bold: true } },
  { text: "  \u2192  ", options: { color: C.warmGray } },
  { text: "Projected NOI: $356K", options: { bold: true } },
  { text: "  \u2192  ", options: { color: C.warmGray } },
  { text: "Implied Value: $5.94M", options: { bold: true, color: C.darkGold } },
], { x: 0.8, y: 4.75, w: 8.4, h: 0.55, fontSize: 12, fontFace: "Arial", color: C.dark, align: "center", valign: "middle" });


// ═══════════════════════════════════════════════════
// SLIDE 3: Property & Renovation
// ═══════════════════════════════════════════════════
let s3 = pres.addSlide();
s3.background = { color: C.white };

s3.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.dark } });
s3.addText("Property & Renovation", {
  x: 0.8, y: 0.1, w: 8, h: 0.7,
  fontSize: 24, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});

// Left: Scope of Work
s3.addText("SCOPE OF WORK", {
  x: 0.8, y: 1.15, w: 4.2, h: 0.3,
  fontSize: 10, fontFace: "Arial", color: C.warmGray, bold: true, charSpacing: 3, margin: 0
});
s3.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.45, w: 2.5, h: 0.015, fill: { color: C.gold } });

const scope = [
  "Full gut renovation to studs",
  "Rebuilt foundation with pylon underpinning",
  "New framing, windows, roof, stucco",
  "All new plumbing & electrical",
  "New insulation, drywall, mini splits",
  "All new interiors: flooring, kitchens, baths",
  "New hardscape & landscape throughout",
];
s3.addText(
  scope.map((s, i) => ({ text: s, options: { bullet: true, breakLine: i < scope.length - 1, fontSize: 11 } })),
  { x: 0.8, y: 1.6, w: 4.2, h: 2.8, fontFace: "Arial", color: C.dark, lineSpacingMultiple: 1.4, valign: "top" }
);

// Right: Timeline
s3.addText("TIMELINE", {
  x: 5.5, y: 1.15, w: 4, h: 0.3,
  fontSize: 10, fontFace: "Arial", color: C.warmGray, bold: true, charSpacing: 3, margin: 0
});
s3.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: 1.45, w: 2.0, h: 0.015, fill: { color: C.gold } });

const timeline = [
  ["Mar 2024", "Acquired"],
  ["Oct 2024", "Construction begins"],
  ["Nov 2025", "Construction complete"],
  ["Dec 2025", "First booking"],
  ["Q1 2026", "Strong operational ramp"],
];
let ty = 1.7;
for (const [date, event] of timeline) {
  // Gold dot
  s3.addShape(pres.shapes.OVAL, { x: 5.6, y: ty + 0.1, w: 0.15, h: 0.15, fill: { color: C.gold } });
  s3.addText(date, { x: 5.9, y: ty, w: 1.3, h: 0.35, fontSize: 10, fontFace: "Arial", color: C.dark, bold: true, margin: 0 });
  s3.addText(event, { x: 7.2, y: ty, w: 2.3, h: 0.35, fontSize: 10, fontFace: "Arial", color: C.warmGray, margin: 0 });
  ty += 0.42;
}

// Bottom: Cost bar (QBO capitalized basis)
const totalBasis = 4200000;
s3.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 4.55, w: 8.4, h: 0.75, fill: { color: C.light } });

const acqW = 8.4 * (2475000 / totalBasis);
const conW = 8.4 * (1566000 / totalBasis);
const carryW = 8.4 - acqW - conW;
s3.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 4.55, w: acqW, h: 0.75, fill: { color: C.dark } });
s3.addText([
  { text: "Acquisition\n", options: { fontSize: 9, color: C.warmGray } },
  { text: "$2,475,000", options: { fontSize: 12, bold: true, color: C.white } },
], { x: 0.8, y: 4.55, w: acqW, h: 0.75, fontFace: "Arial", align: "center", valign: "middle" });

s3.addText([
  { text: "Construction\n", options: { fontSize: 9, color: C.warmGray } },
  { text: "$1,566,000", options: { fontSize: 12, bold: true, color: C.dark } },
], { x: 0.8 + acqW, y: 4.55, w: conW, h: 0.75, fontFace: "Arial", align: "center", valign: "middle" });

s3.addShape(pres.shapes.RECTANGLE, { x: 0.8 + acqW + conW, y: 4.55, w: carryW, h: 0.75, fill: { color: C.lightGold } });
s3.addText([
  { text: "Carry Costs*\n", options: { fontSize: 8, color: C.warmGray } },
  { text: "$159,000", options: { fontSize: 11, bold: true, color: C.dark } },
], { x: 0.8 + acqW + conW, y: 4.55, w: carryW, h: 0.75, fontFace: "Arial", align: "center", valign: "middle" });

s3.addText("Total Capitalized Basis: $4,200,000 (per QBO)    *Capitalized interest, insurance & taxes during construction", {
  x: 0.8, y: 5.35, w: 8.4, h: 0.25,
  fontSize: 9, fontFace: "Arial", color: C.warmGray, align: "right", margin: 0
});


// ═══════════════════════════════════════════════════
// SLIDE 4: Operating Performance
// ═══════════════════════════════════════════════════
let s4 = pres.addSlide();
s4.background = { color: C.white };

s4.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.dark } });
s4.addText("Year-to-Date Operating Performance", {
  x: 0.8, y: 0.1, w: 8, h: 0.7,
  fontSize: 24, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});

// Monthly table
const tblHeader = [
  { text: "Month", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
  { text: "Gross Revenue", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
  { text: "ADR", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
  { text: "Occupancy", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
  { text: "Status", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
];
const months = [
  ["Jan '26", "$40,041", "$286", "75.3%", { text: "ACTUAL", options: { color: C.green, bold: true, align: "center" } }],
  ["Feb '26", "$54,065", "$398", "81.0%", { text: "ACTUAL", options: { color: C.green, bold: true, align: "center" } }],
  ["Mar '26", "$68,024", "$415", "88.2%", { text: "ACTUAL", options: { color: C.green, bold: true, align: "center" } }],
  ["Apr '26", "$72,555", "$487", "82.8%", { text: "BOOKED", options: { color: C.blue, bold: true, align: "center" } }],
];
const tblRows = months.map((m, i) => m.map((v, j) => {
  if (typeof v === "object") return v;
  return { text: v, options: { align: j === 0 ? "left" : "center", fill: { color: i % 2 === 0 ? C.light : C.white } } };
}));

s4.addTable([tblHeader, ...tblRows], {
  x: 0.8, y: 1.2, w: 8.4,
  colW: [1.4, 2.0, 1.4, 1.4, 1.4],
  fontSize: 11, fontFace: "Arial",
  border: { pt: 0.5, color: "DDDDDD" },
  rowH: [0.4, 0.4, 0.4, 0.4, 0.4],
});

// Callouts
const callouts = [
  ["$234K", "YTD Gross Revenue", "Q1 + April booked"],
  ["75% \u2192 88%", "Occupancy Trend", "Strong Q1 ramp"],
  ["$414", "Blended ADR", "Across all channels"],
  ["88.8%", "Owner Margin", "Net of OTA fees & taxes"],
];
let cx = 0.8;
for (const [big, label, sub] of callouts) {
  s4.addShape(pres.shapes.RECTANGLE, {
    x: cx, y: 3.7, w: 2.0, h: 1.5, fill: { color: C.light },
    shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.06 }
  });
  s4.addText(big, { x: cx, y: 3.85, w: 2.0, h: 0.5, fontSize: 20, fontFace: "Arial", color: C.dark, bold: true, align: "center", margin: 0 });
  s4.addText(label, { x: cx, y: 4.35, w: 2.0, h: 0.35, fontSize: 10, fontFace: "Arial", color: C.warmGray, bold: true, align: "center", margin: 0 });
  s4.addText(sub, { x: cx, y: 4.65, w: 2.0, h: 0.3, fontSize: 9, fontFace: "Arial", color: C.gray, align: "center", margin: 0 });
  cx += 2.15;
}


// ═══════════════════════════════════════════════════
// SLIDE 5: Forward Bookings
// ═══════════════════════════════════════════════════
let s5 = pres.addSlide();
s5.background = { color: C.white };

s5.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.dark } });
s5.addText("Forward Revenue on the Books", {
  x: 0.8, y: 0.1, w: 8, h: 0.7,
  fontSize: 24, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});

const fwdHeader = [
  { text: "Month", options: { fill: { color: C.dark }, color: C.white, bold: true } },
  { text: "PF Target", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "right" } },
  { text: "Booked", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "right" } },
  { text: "% Booked", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "center" } },
];
const fwdData = [
  ["Apr", "$72,555", "$72,555", "100.0%"],
  ["May", "$70,468", "$45,556", "64.6%"],
  ["Jun", "$79,704", "$27,997", "35.1%"],
  ["Jul", "$86,526", "$12,220", "14.1%"],
  ["Aug", "$82,134", "$4,343", "5.3%"],
  ["Sep", "$53,130", "$14,827", "27.9%"],
  ["Oct", "$49,275", "$10,333", "21.0%"],
  ["Nov", "$49,275", "$1,204", "2.4%"],
  ["Dec", "$56,595", "$3,729", "6.6%"],
];

const fwdRows = fwdData.map((row, i) => {
  const pct = parseFloat(row[3]);
  const pctColor = pct >= 60 ? C.green : pct >= 25 ? C.gold : "E53935";
  return [
    { text: row[0], options: { fill: { color: i % 2 === 0 ? C.light : C.white } } },
    { text: row[1], options: { align: "right", fill: { color: i % 2 === 0 ? C.light : C.white } } },
    { text: row[2], options: { align: "right", bold: true, fill: { color: i % 2 === 0 ? C.light : C.white } } },
    { text: row[3], options: { align: "center", bold: true, color: pctColor, fill: { color: i % 2 === 0 ? C.light : C.white } } },
  ];
});

s5.addTable([fwdHeader, ...fwdRows], {
  x: 0.8, y: 1.15, w: 5.5,
  colW: [1.0, 1.5, 1.5, 1.2],
  fontSize: 10, fontFace: "Arial",
  border: { pt: 0.5, color: "DDDDDD" },
  rowH: [0.35, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
});

// Right side callouts
s5.addShape(pres.shapes.RECTANGLE, {
  x: 6.8, y: 1.15, w: 2.7, h: 1.6, fill: { color: C.lightGold },
  shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.06 }
});
s5.addText("TOTAL FORWARD\nBOOKED", {
  x: 6.8, y: 1.25, w: 2.7, h: 0.5,
  fontSize: 10, fontFace: "Arial", color: C.warmGray, bold: true, align: "center", charSpacing: 2, margin: 0
});
s5.addText("$192,764", {
  x: 6.8, y: 1.75, w: 2.7, h: 0.55,
  fontSize: 28, fontFace: "Arial", color: C.dark, bold: true, align: "center", margin: 0
});
s5.addText("across 9 months", {
  x: 6.8, y: 2.3, w: 2.7, h: 0.3,
  fontSize: 10, fontFace: "Arial", color: C.warmGray, align: "center", margin: 0
});

s5.addShape(pres.shapes.RECTANGLE, {
  x: 6.8, y: 3.0, w: 2.7, h: 1.1, fill: { color: C.light },
  shadow: { type: "outer", color: "000000", blur: 4, offset: 1, angle: 135, opacity: 0.06 }
});
s5.addText([
  { text: "April fully booked\n", options: { bold: true, fontSize: 11, breakLine: true } },
  { text: "May at 65%\n", options: { bold: true, fontSize: 11, breakLine: true } },
  { text: "Forward bookings provide\nrevenue visibility beyond actuals", options: { fontSize: 9, color: C.warmGray } },
], { x: 6.9, y: 3.1, w: 2.5, h: 0.9, fontFace: "Arial", color: C.dark, valign: "top" });

// Footer note
s5.addText("Forward bookings represent confirmed reservations with deposits received. PF targets based on seasonal model calibrated from actual performance.", {
  x: 0.8, y: 5.15, w: 8.4, h: 0.3,
  fontSize: 8, fontFace: "Arial", color: C.gray, italic: true, margin: 0
});


// ═══════════════════════════════════════════════════
// SLIDE 6: Pro Forma
// ═══════════════════════════════════════════════════
let s6 = pres.addSlide();
s6.background = { color: C.white };

s6.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.dark } });
s6.addText("2026 Pro Forma \u2014 Blended Forecast", {
  x: 0.8, y: 0.1, w: 8, h: 0.7,
  fontSize: 24, fontFace: "Georgia", color: C.gold, bold: true, margin: 0
});

const plHeader = [
  { text: "", options: { fill: { color: C.dark }, color: C.white } },
  { text: "Amount", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "right" } },
  { text: "% of Gross", options: { fill: { color: C.dark }, color: C.white, bold: true, align: "right" } },
];
const plData = [
  ["Gross Revenue", "$761,792", "100.0%", true, false],
  ["OTA Commissions", "($81,796)", "", false, true],
  ["Taxes (TOT)", "($72,649)", "", false, true],
  ["Processing Fees", "($5,401)", "", false, true],
  ["Net to Owner", "$677,157", "89.2%", true, false],
  ["Direct OpEx", "($180,598)", "", false, true],
  ["Management Fee (10%)", "($76,179)", "", false, true],
  ["Property Tax", "($26,679)", "", false, true],
  ["Insurance", "($13,500)", "", false, true],
  ["Other Fixed Costs", "($24,000)", "", false, true],
  ["Net Operating Income", "$356,201", "46.4%", true, false],
];

const plRows = plData.map(([label, amt, pct, isBold, isIndent], i) => {
  const isNoi = label === "Net Operating Income";
  const isNet = label === "Net to Owner";
  const bgColor = isNoi ? "E8F5E9" : isNet ? C.lightGold : (i % 2 === 0 ? C.light : C.white);
  const textColor = isNoi ? C.green : C.dark;
  return [
    { text: isIndent ? `   ${label}` : label, options: { bold: isBold, fill: { color: bgColor }, color: textColor } },
    { text: amt, options: { align: "right", bold: isBold, fill: { color: bgColor }, color: textColor } },
    { text: pct, options: { align: "right", bold: isBold, fill: { color: bgColor }, color: isNoi ? C.green : C.warmGray } },
  ];
});

s6.addTable([plHeader, ...plRows], {
  x: 0.8, y: 1.15, w: 5.8,
  colW: [3.0, 1.5, 1.3],
  fontSize: 11, fontFace: "Arial",
  border: { pt: 0.5, color: "DDDDDD" },
  rowH: [0.35, 0.32, 0.32, 0.32, 0.32, 0.35, 0.32, 0.32, 0.32, 0.32, 0.32, 0.4],
});

// Right side: key numbers
const bigNums = [
  ["$762K", "Gross Revenue"],
  ["$677K", "Net to Owner"],
  ["$356K", "NOI"],
  ["46.4%", "NOI Margin"],
];
let ny = 1.2;
for (const [num, label] of bigNums) {
  s6.addText(num, { x: 7.2, y: ny, w: 2.3, h: 0.45, fontSize: 22, fontFace: "Arial", color: C.dark, bold: true, align: "center", margin: 0 });
  s6.addText(label, { x: 7.2, y: ny + 0.42, w: 2.3, h: 0.25, fontSize: 9, fontFace: "Arial", color: C.warmGray, align: "center", margin: 0 });
  ny += 0.85;
}

// Methodology note
s6.addText("Pro forma blends 3 months of closed actuals with seasonal projections calibrated from actual performance. Model back-tests at 4.9% mean absolute error.", {
  x: 0.8, y: 5.15, w: 8.4, h: 0.3,
  fontSize: 8, fontFace: "Arial", color: C.gray, italic: true, margin: 0
});


// ═══════════════════════════════════════════════════
// SAVE
// ═══════════════════════════════════════════════════
pres.writeFile({ fileName: "/Users/mattshamus/Downloads/Claude Code/casa-yano-site/Casa_Yano_Lender_Deck.pptx" })
  .then(() => console.log("Saved Casa_Yano_Lender_Deck.pptx"))
  .catch(err => console.error(err));
