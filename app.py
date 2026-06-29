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
    layout="centered",
)

st.title(f"🎨 {company['name']}")
st.subheader("Quote Generator")
st.divider()

# ── Client Info ────────────────────────────────────────────────────────────
st.markdown("### Client Information")
col1, col2 = st.columns(2)
with col1:
    client_name = st.text_input("Client / Company Name")
    address = st.text_input("Property Address")
with col2:
    phone = st.text_input("Contact Phone", placeholder="(555) 000-0000")
    email = st.text_input("Contact Email", placeholder="client@email.com")

st.divider()

# ── Job Details ────────────────────────────────────────────────────────────
st.markdown("### Job Details")

sqft = st.number_input(
    "Total Surface Area (sq ft)",
    min_value=0,
    value=0,
    step=50,
    help="Total square footage of all surfaces to be painted.",
)

tier_labels = {
    k: f"Tier {k} — {v['label']}  (${v['rate_per_sqft']:.0f}/sq ft)"
    for k, v in sop["tiers"].items()
}
tier_choice = st.selectbox(
    "Prep Tier",
    options=list(tier_labels.keys()),
    format_func=lambda k: tier_labels[k],
    help="Select the level of surface preparation required.",
)

tier_desc = sop["tiers"][tier_choice]["description"]
st.caption(f"ℹ️ {tier_desc}")

st.divider()

# ── Live Estimate Preview ──────────────────────────────────────────────────
if sqft > 0:
    result = calculate_quote(sqft, tier_choice, sop)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Square Footage", f"{sqft:,.0f} sq ft")
    col_b.metric("Rate", f"${result['rate_per_sqft']:.0f} / sq ft")
    col_c.metric("Estimated Total", f"${result['total']:,.2f}")
else:
    st.info("Enter square footage above to see a live estimate.")

st.divider()

# ── Generate ───────────────────────────────────────────────────────────────
st.markdown("### Generate Quote")

if st.button("📄 Generate PDF Quote", type="primary", use_container_width=True):
    errors = []
    if not client_name.strip():
        errors.append("Client name is required.")
    if not address.strip():
        errors.append("Property address is required.")
    if sqft <= 0:
        errors.append("Square footage must be greater than 0.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Generating PDF..."):
            result = calculate_quote(sqft, tier_choice, sop)
            pdf_bytes = generate_pdf(
                client_name=client_name.strip(),
                address=address.strip(),
                phone=phone.strip(),
                email=email.strip(),
                result=result,
                sop=sop,
            )

        st.success("Quote ready!")
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=f"quote_{client_name.strip().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
