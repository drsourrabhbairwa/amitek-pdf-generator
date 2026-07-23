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
# 3. PDF GENERATION ENGINE (REPORTLAB)
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

    # --- HEADER SECTION ---
    consigner_text = (
        "<b>Consigner:</b><br/>"
        "<b>APP Paint Chemical Private Limited</b><br/>"
        "AMITEK TOWER, 14/120, Main Shipra Path Road, Mansarover, Jaipur, Rajasthan 302021<br/>"
        "<b>GST No.</b> 08AAUCA9834F1Z4<br/>"
        "<b>Contact:</b> +91-9251554683, 9352254008, 9352497771"
    )

    if os.path.exists(logo_filename):
        logo_img = RLImage(logo_filename, width=140, height=45)
    else:
        logo_img = Paragraph("<font size=18 color='#A6192E'><b>AMITEK</b></font>", title_style)

    header_table = Table([[logo_img, Paragraph(consigner_text, body_style)]], colWidths=[150, 373])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
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
    story.append(Spacer(1, 15))

    # --- LABOR COST SECTION ---
    if data['labor_data']:
        story.append(Paragraph("<b>Labor Cost Breakdown (per Sq. Ft.)</b>", title_style))
        story.append(Spacer(1, 5))
        
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
        story.append(Spacer(1, 15))

    # --- BILLING SECTION ---
    if data['billing_data']:
        story.append(Paragraph("<b>Billing / Material Details</b>", title_style))
        story.append(Spacer(1, 5))
        
        bill_table_data = [[
            Paragraph("Item Description", th_style), 
            Paragraph("Qty", th_style), 
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
        story.append(Spacer(1, 15))

    # --- SIGNATURE SECTION ---
    if data['biller_name'].strip():
        story.append(Spacer(1, 25))
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
# 4. STREAMLIT FORM INTERFACE
# ==========================================
st.title("📄 AMITEK Document Generator")
st.markdown("Fill in the fields below. **Empty sections will automatically be hidden on the generated PDF.**")

web_app_url = "https://script.google.com/macros/s/AKfycbwVOXwd6-WOrk2WGqRypQvKNwaQgaXHuvjccu5_RxOvEz_dEZMm19vMEJgy3T199r2n8w/exec"

with st.form("amitek_quote_form"):
    st.subheader("🔒 Private Internal Fields (Hidden from PDF)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        client_type = st.selectbox("Client Type", ["End Client", "Dealer", "Contractor", "Other"])
    with col_p2:
        pricing_strategy = st.selectbox("Pricing Strategy", ["Standard Rate", "Discounted Dealer Rate", "Margin + 15%", "Custom Tender"])

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
    if show_billing:
        item_count = st.number_input("Number of Items", min_value=1, max_value=10, value=1)
        for i in range(int(item_count)):
            c1, c2, c3 = st.columns([2, 1, 1])
            item_name = c1.text_input(f"Item #{i+1} Description", key=f"item_{i}", value="Chemical Coating A")
            qty = c2.number_input(f"Qty", key=f"q_{i}", min_value=1, value=10)
            price = c3.number_input(f"Unit Price (₹)", key=f"p_{i}", min_value=0.0, value=500.0)
            if item_name.strip():
                billing_list.append({"item": item_name, "qty": qty, "price": price})

    st.subheader("✍️ Biller & Authorization Details [Optional]")
    biller_name = st.text_input("Biller / Prepared By Name", value="")

    submit_btn = st.form_submit_button("⚙️ Generate PDF & Save Record")


# ==========================================
# 5. FORM SUBMISSION & OUTPUT
# ==========================================
if submit_btn:
    if not client_name.strip():
        st.error("Please enter a valid Client Name before generating.")
    else:
        total_labor = sum([r['sqft'] * r['rate'] for r in labor_list])
        total_billing = sum([r['qty'] * r['price'] for r in billing_list])
        grand_total = total_labor + total_billing

        doc_data = {
            "quote_no": quote_no,
            "date": quote_date,
            "client_name": client_name,
            "site_location": site_location,
            "labor_data": labor_list,
            "billing_data": billing_list,
            "biller_name": biller_name
        }

        pdf_bytes = generate_pdf(doc_data)

        if web_app_url:
            log_success = log_to_google_sheets(web_app_url, quote_no, client_name, client_type, pricing_strategy, grand_total)
            if log_success:
                st.success("📊 Record successfully saved to Google Sheets!")
            else:
                st.warning("⚠️ PDF generated, but failed to reach Google Sheets.")

        st.success("✅ PDF generated successfully!")

        st.download_button(
            label="📥 Download PDF Document",
            data=pdf_bytes,
            file_name=f"{quote_no}_{client_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
