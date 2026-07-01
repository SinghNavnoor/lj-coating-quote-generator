import base64
import uuid

import streamlit as st
import yaml
from pathlib import Path
from core.calculator import calculate_quote
from core.pdf_generator import generate_pdf

SOP_PATH = Path(__file__).parent / "config" / "sop.yaml"


@st.cache_resource
def load_sop():
    with open(SOP_PATH, "r") as f:
        return yaml.safe_load(f)


sop = load_sop()
company = sop["company"]

st.set_page_config(
    page_title=f"{company['name']} — Quote Generator",
    page_icon="🎨",
    layout="wide",
)

st.markdown("""
<style>
/* ── Lock to viewport, no outer scroll ── */
#MainMenu, footer, header { visibility: hidden; }

html, body {
    background: #ffffff !important;
    overflow: hidden !important;
    height: 100vh !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #ffffff !important;
    overflow: hidden !important;
    height: 100vh !important;
}

.block-container {
    padding: 1.6rem 2.25rem 0.5rem !important;
    max-width: 100% !important;
    overflow: hidden !important;
    background: #ffffff !important;
}

/* ── System font ── */
*, *::before, *::after {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                 "Helvetica Neue", Arial, sans-serif !important;
}

/* ── Page heading ── */
h1 {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: #1d1d1f !important;
    margin-bottom: 1.1rem !important;
    padding: 0 !important;
}

/* ── Column row ── */
[data-testid="stHorizontalBlock"] {
    gap: 0.85rem !important;
    align-items: flex-start !important;
}

/* ── Left card (column 1) and Right card (column 3) — top-level only ── */
.block-container > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) > div:first-child,
.block-container > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) > div:first-child {
    background: #ffffff !important;
    border: 2px solid #a8a8b0 !important;
    border-radius: 20px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.07), 0 8px 24px rgba(0,0,0,0.06) !important;
    height: calc(100vh - 90px) !important;
    overflow-y: auto !important;
    padding: 1.5rem 1.75rem !important;
    box-sizing: border-box !important;
}

/* ── Remove default Streamlit bordered-container styles (we don't use them) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    height: 100% !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    padding: 0 !important;
}

/* ── Form field labels ── */
[data-testid="stWidgetLabel"] p {
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    color: #8e8e93 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}

/* ── Inputs ── */
input[type="text"],
input[type="email"],
input[type="number"] {
    background: #f5f5f7 !important;
    border: 1px solid #d1d1d6 !important;
    border-radius: 10px !important;
    font-size: 0.875rem !important;
    color: #1d1d1f !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #f5f5f7 !important;
    border: 1px solid #d1d1d6 !important;
    border-radius: 10px !important;
    font-size: 0.875rem !important;
}

/* ── HR ── */
hr {
    border-top: 1px solid #e5e5ea !important;
    margin: 0.8rem 0 !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.73rem !important;
    color: #aeaeb2 !important;
    margin-top: 3px !important;
    line-height: 1.5 !important;
}

/* ── Green primary button ── */
[data-testid="baseButton-primary"] {
    background: #34c759 !important;
    border: none !important;
    color: #fff !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    border-radius: 14px !important;
    min-height: 5rem !important;
    box-shadow: 0 2px 8px rgba(52,199,89,0.35) !important;
    transition: all 0.15s ease !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #28a745 !important;
    box-shadow: 0 4px 14px rgba(52,199,89,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Download button (secondary) ── */
[data-testid="baseButton-secondary"] {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    background: #f5f5f7 !important;
    border: 1.5px solid #c7c7cc !important;
    color: #1d1d1f !important;
}
[data-testid="baseButton-secondary"]:hover {
    background: #e5e5ea !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-size: 0.8rem !important;
    padding: 0.6rem 0.85rem !important;
}

/* ── Middle column: vertically center content ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) > div:first-child {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
}
</style>
""", unsafe_allow_html=True)

# ── Minimal header ─────────────────────────────────────────────────────────
st.markdown(
    f"<h1>🎨 {company['name']}"
    f"<span style='font-weight:300;color:#aeaeb2;font-size:0.85rem;"
    f"margin-left:0.6rem;'>Quote Generator</span></h1>",
    unsafe_allow_html=True,
)

# ── Session state ──────────────────────────────────────────────────────────
def _new_id():
    return uuid.uuid4().hex

def _add_material():
    st.session_state.materials.append({"id": _new_id()})

def _remove_material(mid):
    st.session_state.materials = [m for m in st.session_state.materials if m["id"] != mid]

if "materials" not in st.session_state:
    st.session_state.materials = [{"id": _new_id()}]
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "pdf_client_name" not in st.session_state:
    st.session_state.pdf_client_name = "quote"

col_left, col_mid, col_right = st.columns([5, 1.6, 5], gap="small")

# ── LEFT: Step 1 — Data Entry ──────────────────────────────────────────────
with col_left:
    with st.container(border=True):
        st.markdown(
            '<span style="display:inline-block;background:#f5f5f7;border:1px solid #c7c7cc;'
            'color:#8e8e93;font-size:0.62rem;font-weight:700;letter-spacing:0.12em;'
            'text-transform:uppercase;padding:2px 10px;border-radius:999px;margin-bottom:5px;">'
            'Step 1</span>'
            '<div style="font-size:1rem;font-weight:700;color:#1d1d1f;margin-bottom:0.85rem;">'
            'Enter Quote Details</div>',
            unsafe_allow_html=True,
        )

        # Client section
        st.markdown(
            '<div style="font-size:0.62rem;font-weight:700;color:#aeaeb2;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.35rem;">'
            'Client</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            client_name = st.text_input("Name", placeholder="Client or company")
            address = st.text_input("Address", placeholder="Property address")
        with c2:
            phone = st.text_input("Phone", placeholder="(555) 000-0000")
            email = st.text_input("Email", placeholder="client@email.com")

        st.divider()

        # Materials section
        st.markdown(
            '<div style="font-size:0.62rem;font-weight:700;color:#aeaeb2;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.35rem;">'
            'Materials</div>',
            unsafe_allow_html=True,
        )

        # Column headers
        lh1, lh2, lh3 = st.columns([4, 2, 0.6])
        with lh1:
            st.markdown(
                '<p style="font-size:0.67rem;font-weight:600;color:#8e8e93;'
                'letter-spacing:0.07em;text-transform:uppercase;margin:0 0 2px 0;">Item Name</p>',
                unsafe_allow_html=True,
            )
        with lh2:
            st.markdown(
                '<p style="font-size:0.67rem;font-weight:600;color:#8e8e93;'
                'letter-spacing:0.07em;text-transform:uppercase;margin:0 0 2px 0;">Cost ($)</p>',
                unsafe_allow_html=True,
            )

        for item in st.session_state.materials:
            mid = item["id"]
            c1, c2, c3 = st.columns([4, 2, 0.6])
            with c1:
                st.text_input(
                    "item_name", key=f"name_{mid}",
                    label_visibility="collapsed",
                    placeholder="e.g. Brushes, Primer…",
                )
            with c2:
                st.number_input(
                    "item_cost", key=f"cost_{mid}",
                    label_visibility="collapsed",
                    min_value=0.0, value=0.0, step=1.0, format="%.2f",
                )
            with c3:
                st.button(
                    "×", key=f"del_{mid}",
                    on_click=_remove_material, args=(mid,),
                    help="Remove item",
                )

        st.button("＋ Add Item", key="add_mat", on_click=_add_material)

        # Compute materials total from current widget values
        materials_items = [
            {
                "name": st.session_state.get(f"name_{item['id']}", ""),
                "cost": float(st.session_state.get(f"cost_{item['id']}", 0.0)),
            }
            for item in st.session_state.materials
        ]
        materials_total = sum(i["cost"] for i in materials_items)

        st.divider()

        # Labor section
        st.markdown(
            '<div style="font-size:0.62rem;font-weight:700;color:#aeaeb2;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.35rem;">'
            'Labor</div>',
            unsafe_allow_html=True,
        )

        l1, l2, l3 = st.columns(3)
        with l1:
            num_workers = st.number_input("Workers", min_value=1, value=1, step=1, key="labor_workers")
        with l2:
            hourly_rate = st.number_input("Rate ($/hr)", min_value=0.0, value=0.0, step=0.50, key="labor_rate", format="%.2f")
        with l3:
            hours = st.number_input("Hours", min_value=0.0, value=0.0, step=0.5, key="labor_hours", format="%.1f")

        labor_total = num_workers * hourly_rate * hours
        grand_total = materials_total + labor_total

        # Live total preview
        if grand_total > 0:
            st.markdown(
                f'<div style="background:#f5f5f7;border-radius:12px;padding:0.65rem 1rem;margin-top:0.6rem;">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                f'<span style="font-size:0.78rem;color:#8e8e93;">Materials</span>'
                f'<span style="font-size:0.78rem;color:#1d1d1f;">${materials_total:,.2f}</span>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
                f'<span style="font-size:0.78rem;color:#8e8e93;">Labor</span>'
                f'<span style="font-size:0.78rem;color:#1d1d1f;">${labor_total:,.2f}</span>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;border-top:1px solid #e5e5ea;padding-top:6px;">'
                f'<span style="font-size:0.85rem;color:#8e8e93;font-weight:600;">Estimated Total</span>'
                f'<span style="font-size:1rem;color:#1d1d1f;font-weight:700;">${grand_total:,.2f}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── MIDDLE: Step 2 — Generate ──────────────────────────────────────────────
with col_mid:
    st.markdown(
        '<span style="display:inline-block;background:#f5f5f7;border:1px solid #c7c7cc;'
        'color:#8e8e93;font-size:0.62rem;font-weight:700;letter-spacing:0.12em;'
        'text-transform:uppercase;padding:2px 10px;border-radius:999px;">'
        'Step 2</span>',
        unsafe_allow_html=True,
    )

    generate_clicked = st.button(
        "⚡ Generate\nInvoice",
        type="primary",
        use_container_width=True,
        key="generate_btn",
    )

    if generate_clicked:
        errors = []
        if not client_name.strip():
            errors.append("Client name is required.")
        if not address.strip():
            errors.append("Address is required.")
        if grand_total <= 0:
            errors.append("Add at least one material or labor cost.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            with st.spinner(""):
                result = calculate_quote(materials_items, num_workers, hourly_rate, hours)
                st.session_state.pdf_bytes = generate_pdf(
                    client_name=client_name.strip(),
                    address=address.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    result=result,
                    sop=sop,
                )
                st.session_state.pdf_client_name = client_name.strip()
            st.success("✓ Ready")

# ── RIGHT: Step 3 — Preview & Download ────────────────────────────────────
with col_right:
    with st.container(border=True):
        st.markdown(
            '<span style="display:inline-block;background:#f5f5f7;border:1px solid #c7c7cc;'
            'color:#8e8e93;font-size:0.62rem;font-weight:700;letter-spacing:0.12em;'
            'text-transform:uppercase;padding:2px 10px;border-radius:999px;margin-bottom:5px;">'
            'Step 3</span>'
            '<div style="font-size:1rem;font-weight:700;color:#1d1d1f;margin-bottom:0.75rem;">'
            'Preview & Download</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.pdf_bytes:
            b64 = base64.b64encode(st.session_state.pdf_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" width="100%"'
                f' style="height:calc(100vh - 290px);border:none;border-radius:10px;'
                f'display:block;"></iframe>',
                unsafe_allow_html=True,
            )
            st.write("")
            safe_name = st.session_state.pdf_client_name.replace(" ", "_")
            st.download_button(
                label="↓   Step 3: Download PDF",
                data=st.session_state.pdf_bytes,
                file_name=f"quote_{safe_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.markdown(
                '<div style="display:flex;flex-direction:column;align-items:center;'
                'justify-content:center;height:calc(100vh - 290px);text-align:center;">'
                '<div style="font-size:2.5rem;margin-bottom:0.75rem;opacity:0.3;">📄</div>'
                '<p style="color:#8e8e93;font-size:0.85rem;line-height:1.65;margin:0;">'
                'Your invoice preview will appear here.<br>'
                '<span style="color:#c7c7cc;font-size:0.78rem;">'
                'Complete the form and click Generate Invoice.</span></p>'
                '</div>',
                unsafe_allow_html=True,
            )
