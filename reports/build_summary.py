"""Builds reports/findings_summary.pdf (two pages). Numbers are copied from the executed notebook
(notebooks/01_january_effect.ipynb); re-check them if the notebook changes."""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
RED = colors.HexColor("#c0392b")
base = ParagraphStyle("b", fontName="Helvetica", fontSize=9.3, leading=12.2, spaceAfter=4)
h1 = ParagraphStyle("h1", parent=base, fontName="Helvetica-Bold", fontSize=17, leading=21, spaceAfter=2)
sub = ParagraphStyle("sub", parent=base, fontSize=8.5, textColor=colors.HexColor("#555555"), spaceAfter=8)
h2 = ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=6, spaceAfter=3, textColor=RED, keepWithNext=1)
bul = ParagraphStyle("bul", parent=base, leftIndent=11, bulletIndent=0, spaceAfter=2.5)
small = ParagraphStyle("sm", parent=base, fontSize=7.8, leading=10, textColor=colors.HexColor("#444444"))

def B(t): return Paragraph(t, bul, bulletText="\u2022")
def img(name, w):
    from PIL import Image as PI
    iw, ih = PI.open(FIG / name).size
    return Image(str(FIG / name), width=w, height=w * ih / iw)

S = []
S += [Paragraph("In-store transactions run about 19% higher in January", h1),
      Paragraph("Exploratory analysis of retail_store_sales.csv (12,575 transactions, Jan 2022 - Jan 2025). Prepared 20 Oct 2026.", sub)]
S += [Paragraph("The finding, in plain language", h2),
      Paragraph("In each of the last three Januaries (2022-2024), the stores recorded about <b>19% more transactions per day</b> than in the other "
                "eleven months: <b>6.5 per day versus 5.5</b>. Online transactions did not rise (+2%). The pattern points the same way in all three years, "
                "survives the checks on page 2, and stays statistically significant after correcting for the 40 comparisons I looked at "
                "(adjusted p = 0.006). Whether it is a true seasonal effect cannot be settled from this file alone: it covers only three Januaries, "
                "the data looks synthetic, and the in-store split was identified after the fact.", base)]
S += [Paragraph("Hypothesis and how it arose", h2),
      Paragraph("<b>Hypothesis:</b> in-store transactions per day are higher in January than in other months. I scanned 15 comparisons "
                "(spend, quantity and volume by category, channel, payment, discount, weekday, month, customer). Only category-vs-spend survived "
                "correction, and that is just a price effect (Milk Products has the lowest unit prices). Monthly volume was borderline "
                "(p = 0.077) and hinted at January. The all-channel January bump (+10%) does <i>not</i> survive full correction (adjusted p = 0.08), "
                "which prompted the split by channel.", base)]
S += [img("fig3_january_uplift_by_channel.png", 5.6 * inch), Spacer(1, 4)]
rows = [["", "January / day", "Other months / day", "Ratio", "Raw p", "Adjusted p (40 looks)"],
        ["In-store", "6.54", "5.48", "1.19", "0.00015", "0.006"],
        ["Online", "5.81", "5.70", "1.02", "0.50", "1.00"],
        ["All channels", "12.34", "11.18", "1.10", "0.0019", "0.076"]]
t = Table(rows, colWidths=[0.95*inch, 1.0*inch, 1.35*inch, 0.6*inch, 0.8*inch, 1.5*inch])
t.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.3), ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f4")), ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fbe9e7")),
                       ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbbbbb")),
                       ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
S += [t, Spacer(1, 3), Paragraph("Daily averages over 2022-2024 (1,096 days). Tests: Mann-Whitney on daily counts; Bonferroni adjustment for 40 looks.", small)]

S += [Paragraph("Is it an artefact of how the data was collected?", h2),
      B("<b>Month length:</b> counts are per day, so 28- and 31-day months compare fairly."),
      B("<b>Gaps and dropped rows:</b> no calendar day is missing in 3 years; rows with unrecoverable amounts occur at the same rate in January and other months (4.8%); "
        "the result is identical using raw rows and cleaned rows."),
      B("<b>One lucky year or a few busy days:</b> leaving out any one year keeps the all-channel ratio at 1.09-1.12; dropping January's five busiest days "
        "leaves +7% (p = 0.02). In-store ratios by year: 1.11, 1.23, 1.23 (single-year p = 0.19, 0.005, 0.01)."),
      B("<b>Record ordering:</b> transaction IDs carry no information about date (rank correlation 0.004)."),
      B("<b>Out-of-sample:</b> January 2025 (18 days, held out) shows 114 in-store transactions against 118 expected under the January pattern and 99 under "
        "no effect (one-sided p = 0.07). Mildly supportive, not proof.")]
S += [Paragraph("Context: all channels together", h2),
      Paragraph("Combining channels, January is the busiest month but the gap is modest and the error bars overlap with other months. "
                "This is why the headline rests on the in-store result rather than the all-channel bump.", base),
      img("fig1_transactions_per_day_by_month.png", 4.6 * inch), Spacer(1, 4)]
S += [Paragraph("Patterns that looked promising and did not hold", h2),
      img("fig4_disproved_january_basket.png", 4.3 * inch),
      B("<b>\"January shoppers spend more per visit.\"</b> Pooled, it looks real (136 vs 129 per transaction, p = 0.002), but it is almost entirely January 2022 (+15). "
        "2023 (+4) and 2024 (+2) are within noise; without 2022, p = 0.17."),
      B("<b>\"Discounts lead to bigger baskets.\"</b> No effect on quantity (5.54 vs 5.58) or spend (130.5 vs 129.9)."),
      B("<b>\"Fridays are the best day.\"</b> Friday has the highest average spend, but a best-of-seven weekday this good occurs by chance 10% of the time; "
        "transactions per day are flat across weekdays (11.2-11.4)."),
      B("<b>Unexplained:</b> average spend in April 2024 is unusually high (148.8 vs 129.2). After correcting for 40 looks it is not distinguishable from luck (p = 0.14); "
        "flagged, not claimed.")]
S += [Paragraph("Limits and recommended next step", h2),
      B("Three Januaries is a small sample of seasons. The in-store/online split was found post hoc (and paid for in the correction). The dataset looks synthetic "
        "(equal category sizes, 25 prices per category), so this describes the file, not a real retailer. <b>Spend is pre-discount</b> "
        "(total = price x quantity even when a discount is flagged), so discount effects on revenue cannot be measured."),
      B("<b>Next step:</b> do not change staffing or stock on this alone. Repeat the test on a real store POS extract and, if it holds, check what drives January "
        "footfall (promotions, hours, local events). Full method, all 40 looks and every chart are in the notebook.")]

doc = SimpleDocTemplate(str(HERE / "findings_summary.pdf"), pagesize=letter, leftMargin=0.7*inch, rightMargin=0.7*inch,
                        topMargin=0.55*inch, bottomMargin=0.5*inch, title="In-store transactions run about 19% higher in January",
                        author="Exploratory analysis")
doc.build(S)
