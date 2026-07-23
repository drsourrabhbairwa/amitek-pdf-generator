import os
import io
import requests
from datetime import datetime
import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. PAGE CONFIGURATION & PASSWORD SECURITY
# ==========================================
st.set_page_config(
    page_title="AMITEK Document Generator",
    page_icon="📄",
    layout="centered"
)

def check_password():
    """Simple password protection layer with safe secrets fallback."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 AMITEK Portal Access")
        password_input = st.text_input("Enter Access Password", type="password")
        if st.button("Log In"):
            try:
                APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Amitek@2026")
            except Exception:
                APP_PASSWORD = "Amitek@2026"

            if password_input == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        return False
    return True

if not check_password():
    st.stop()


# ==========================================
# 2. GOOGLE SHEETS LOGGING FUNCTION
# ==========================================
def log_to_google_sheets(web_app_url, quote_no, client_name, client_type, pricing_strategy, grand_total):
    """Sends quote metadata to Google Sheets via Google Apps Script Web App."""
    if not web_app_url:
        return False
        
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "quote_no": quote_no,
        "client_name": client_name,
        "client_type": client_type,
        "pricing_strategy": pricing_strategy,
        "total_amount": f"₹ {grand_total:,.2f}"
    }
    try:
        response = requests.post(web_app_url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# ==========================================
# 3. PRODUCT CATALOG & PRICING DATA (From Price Chart)
# ==========================================
PRODUCT_CATALOG = {
    "Amitek-HWR 22": {
        "packages": {
            1: {"dealer": 925.0, "project": 1156.25, "client": 1651.79, "mrp": 2359.69},
            5: {"dealer": 912.5, "project": 1140.625, "client": 1629.46, "mrp": 2327.81},
            20: {"dealer": 882.5, "project": 1103.125, "client": 1575.89, "mrp": 2251.28}
        }
    },
    "Amitek CMP 78": {
        "packages": {
            1: {"dealer": 235.29, "project": 276.82, "client": 325.67, "mrp": 465.24},
            5: {"dealer": 210.08, "project": 247.16, "client": 290.77, "mrp": 415.39},
            20: {"dealer": 210.08, "project": 247.16, "client": 290.77, "mrp": 415.39}
        }
    },
    "Amitek- HMC 501": {
        "packages": {
            4: {"dealer": 187.50, "project": 234.375, "client": 275.74, "mrp": 393.91},
            20: {"dealer": 175.00, "project": 218.75, "client": 257.35, "mrp": 367.65}
        }
    },
    "Amitek Smart Duo Shield Damproof": {
        "packages": {
            1: {"dealer": 168.17, "project": 186.85, "client": 207.62, "mrp": 296.59},
            4: {"dealer": 151.35, "project": 168.17, "client": 186.85, "mrp": 266.93},
            20: {"dealer": 151.35, "project": 168.17, "client": 186.85, "mrp": 266.93}
        }
    },
    "Amitek TransShield Pro": {
        "packages": {
            4: {"dealer": 371.11, "project": 463.89, "client": 579.86, "mrp": 828.37},
            10: {"dealer": 324.44, "project": 405.56, "client": 506.94, "mrp": 724.21},
            20: {"dealer": 306.67, "project": 383.33, "client": 479.17, "mrp": 684.52}
        }
    }
}


# ==========================================
# 4. PDF GENERATION ENGINE (REPORTLAB)
# ==========================================
def generate_pdf(data, logo_filename="Untitled_design-removebg-preview.png"):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()

    PRIMARY_COLOR = colors.HexColor("#A6192E")  # AMITEK Red
    DARK_HEADER = colors.HexColor("#2C3E50")    # Dark Charcoal
    BG_LIGHT = colors.HexColor("#F8F9FA")       # Off-white

    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold')
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=8.5, leading=12, fontName='Helvetica')
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8.5, leading=12, fontName='Helvetica-Bold')
    th_style = ParagraphStyle('THStyle', parent=styles['Normal'], fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=colors.white)
    right_bold = ParagraphStyle('RightBold', parent=styles['Normal'], fontSize=9, leading=12, fontName='Helvetica-Bold', alignment=2)

    # --- HEADER SECTION (Clean company info without "Consigner:") ---
    company_text = (
        "<b>APP Paint Chemical Private Limited</b><br/>"
        "AMITEK TOWER, 14/120, Main Shipra Path Road, Mansarover, Jaipur, Rajasthan 302021<br/>"
        "<b>GST No.</b> 08AAUCA9834F1Z4 | <b>Contact:</b> +91-9251554683, 9352254008"
    )

    if os.path.exists(logo_filename):
        logo_img = RLImage(logo_filename, width=130, height=42)
    else:
        logo_img = Paragraph("<font size=16 color='#A6192E'><b>AMITEK</b></font>", title_style)

    header_table = Table([[logo_img, Paragraph(company_text, body_style)]], colWidths=[140, 383])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # --- CLIENT & QUOTE META DETAILS ---
    client_info_data = [
        [
            Paragraph(f"<b>Quote No:</b> {data['quote_no']}", body_style), 
            Paragraph(f"<b>Date:</b> {data['date']}", body_style)
        ],
        [
            Paragraph(f"<b>Client Name:</b> {data['client_name']}", body_style), 
            Paragraph(f"<b>Site Location:</b> {data['site_location']}", body_style)
        ]
    ]
    client_table = Table(client_info_data, colWidths=[261, 262])
    client_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 12))

    # --- LABOR COST SECTION ---
    if data['labor_data']:
        story.append(Paragraph("<b>Labor Cost Breakdown (per Sq. Ft.)</b>", title_style))
        story.append(Spacer(1, 4))
        
        labor_table_data = [[
            Paragraph("Area Name", th_style), 
            Paragraph("Area (Sq. Ft.)", th_style), 
            Paragraph("Rate / Sq. Ft.", th_style), 
            Paragraph("Total Amount", th_style)
        ]]
        
        for row in data['labor_data']:
            labor_table_data.append([
                Paragraph(row['area'], body_style),
                Paragraph(f"{row['sqft']:,.2f}", body_style),
                Paragraph(f"₹ {row['rate']:,.2f}", body_style),
                Paragraph(f"₹ {row['sqft'] * row['rate']:,.2f}", bold_style)
            ])
            
        l_table = Table(labor_table_data, colWidths=[203, 100, 100, 120])
        l_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(l_table)
        story.append(Spacer(1, 12))

    # --- BILLING SECTION ---
    if data['billing_data']:
        story.append(Paragraph("<b>Billing / Material Details</b>", title_style))
        story.append(Spacer(1, 4))
        
        bill_table_data = [[
            Paragraph("Item Description & Package", th_style), 
            Paragraph("Qty (Packs)", th_style), 
            Paragraph("Unit Price", th_style), 
            Paragraph("Amount", th_style)
        ]]
        
        for row in data['billing_data']:
            bill_table_data.append([
                Paragraph(row['item'], body_style),
                Paragraph(str(row['qty']), body_style),
                Paragraph(f"₹ {row['price']:,.2f}", body_style),
                Paragraph(f"₹ {row['qty'] * row['price']:,.2f}", bold_style)
            ])
            
        b_table = Table(bill_table_data, colWidths=[223, 80, 100, 120])
        b_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), DARK_HEADER),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(b_table)
        story.append(Spacer(1, 12))

    # --- FINANCIAL SUMMARY (Subtotal, GST, Grand Total) ---
    summary_data = [
        [Paragraph("<b>Subtotal:</b>", body_style), Paragraph(f"₹ {data['subtotal']:,.2f}", right_bold)],
        [Paragraph(f"<b>GST ({data['gst_pct']}%):</b>", body_style), Paragraph(f"₹ {data['gst_amount']:,.2f}", right_bold)],
        [Paragraph("<b>Grand Total:</b>", bold_style), Paragraph(f"<b>₹ {data['grand_total']:,.2f}</b>", right_bold)]
    ]
    sum_table = Table(summary_data, colWidths=[383, 140])
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(sum_table)

    # --- SIGNATURE SECTION ---
    if data['biller_name'].strip():
        story.append(Spacer(1, 20))
        sig_data = [
            [Paragraph("", body_style), Paragraph("<b>Authorized Signatory</b>", bold_style)],
            [Paragraph("", body_style), Paragraph(f"<b>Name:</b> {data['biller_name']}", body_style)],
            [Paragraph("", body_style), Paragraph("APP Paint Chemical Pvt. Ltd. (Seal)", body_style)]
        ]
        sig_table = Table(sig_data, colWidths=[300, 223])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('LINEABOVE', (1,0), (1,0), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ==========================================
# 5. STREAMLIT FORM INTERFACE
# ==========================================
st.title("📄 AMITEK Document Generator")
st.markdown("Fill in the fields below. Product pricing is automatically loaded from your price chart.")

web_app_url = "https://script.google.com/macros/s/AKfycbwVOXwd6-WOrk2WGqRypQvKNwaQgaXHuvjccu5_RxOvEz_dEZMm19vMEJgy3T199r2n8w/exec"

with st.form("amitek_quote_form"):
    st.subheader("🔒 Private Internal Fields (Hidden from PDF)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        client_type = st.selectbox("Client Type", ["End Client", "Dealer", "Contractor", "Other"])
    with col_p2:
        pricing_strategy = st.selectbox(
            "Pricing Strategy (Determines Price Tier)", 
            ["Dealer Price", "Project Price", "End Client Price", "MRP Price"]
        )

    st.subheader("📋 General Quote Information")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        quote_no = st.text_input("Quote Number", value="AMT-2026-001")
        client_name = st.text_input("Client Name *", value="")
    with col_q2:
        quote_date = st.date_input("Quote Date").strftime("%Y-%m-%d")
        site_location = st.text_input("Site Location / City", value="")

    st.subheader("🏗️ Labor Cost (per Sq. Ft.) [Optional]")
    show_labor = st.checkbox("Include Labor Cost Breakdown?")
    labor_list = []
    if show_labor:
        area_count = st.number_input("Number of Areas", min_value=1, max_value=10, value=1)
        for i in range(int(area_count)):
            c1, c2, c3 = st.columns([2, 1, 1])
            area_name = c1.text_input(f"Area #{i+1} Name", key=f"a_{i}", value=f"Area {i+1}")
            sqft = c2.number_input(f"Sq. Ft.", key=f"s_{i}", min_value=0.0, value=100.0)
            rate = c3.number_input(f"Rate / Sq.Ft. (₹)", key=f"r_{i}", min_value=0.0, value=25.0)
            if area_name.strip():
                labor_list.append({"area": area_name, "sqft": sqft, "rate": rate})

    st.subheader("📦 Billing / Material Details [Optional]")
    show_billing = st.checkbox("Include Billing Details?")
    billing_list = []
    
    # Map pricing strategy choice to dictionary keys
    strategy_key_map = {
        "Dealer Price": "dealer",
        "Project Price": "project",
        "End Client Price": "client",
        "MRP Price": "mrp"
    }
    selected_tier = strategy_key_map[pricing_strategy]

    if show_billing:
        item_count = st.number_input("Number of Items", min_value=1, max_value=10, value=1)
        for i in range(int(item_count)):
            c1, c2, c3 = st.columns([2, 1, 1])
            
            # Product Dropdown
            product_name = c1.selectbox(f"Product #{i+1}", list(PRODUCT_CATALOG.keys()), key=f"prod_{i}")
            
            # Available package sizes for selected product
            available_pkgs = list(PRODUCT_CATALOG[product_name]["packages"].keys())
            pkg_size = c2.selectbox(f"Package Size (Kg) #{i+1}", available_pkgs, key=f"pkg_{i}")
            
            qty = c3.number_input(f"Quantity (Packs) #{i+1}", min_value=1, value=10, key=f"qty_{i}")
            
            # Automatically fetch unit price per package (Rate per kg * Package size)
            rate_per_kg = PRODUCT_CATALOG[product_name]["packages"][pkg_size][selected_tier]
            unit_price = rate_per_kg * pkg_size
            
            item_desc = f"{product_name} ({pkg_size} Kg Pack)"
            billing_list.append({"item": item_desc, "qty": qty, "price": unit_price})

    st.subheader("💰 Taxes & Totals")
    gst_pct = st.number_input("GST Rate (%)", min_value=0.0, max_value=50.0, value=18.0, step=0.5)

    st.subheader("✍️ Biller & Authorization Details [Optional]")
    biller_name = st.text_input("Biller / Prepared By Name", value="")

    submit_btn = st.form_submit_button("⚙️ Generate PDF & Save Record")


# ==========================================
# 6. FORM SUBMISSION & OUTPUT
# ==========================================
if submit_btn:
    if not client_name.strip():
        st.error("Please enter a valid Client Name before generating.")
    else:
        total_labor = sum([r['sqft'] * r['rate'] for r in labor_list])
        total_billing = sum([r['qty'] * r['price'] for r in billing_list])
        subtotal = total_labor + total_billing
        gst_amount = subtotal * (gst_pct / 100.0)
        grand_total = subtotal + gst_amount

        doc_data = {
            "quote_no": quote_no,
            "date": quote_date,
            "client_name": client_name,
            "site_location": site_location,
            "labor_data": labor_list,
            "billing_data": billing_list,
            "subtotal": subtotal,
            "gst_pct": gst_pct,
            "gst_amount": gst_amount,
            "grand_total": grand_total,
            "biller_name": biller_name
        }

        pdf_bytes = generate_pdf(doc_data)

        if web_app_url:
            log_success = log_to_google_sheets(web_app_url, quote_no, client_name, client_type, pricing_strategy, grand_total)
            if log_success:
                st.success("📊 Record successfully saved to Google Sheets with Grand Total!")
            else:
                st.warning("⚠️ PDF generated, but failed to reach Google Sheets.")

        st.success("✅ PDF generated successfully!")

        st.download_button(
            label="📥 Download PDF Document",
            data=pdf_bytes,
            file_name=f"{quote_no}_{client_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
