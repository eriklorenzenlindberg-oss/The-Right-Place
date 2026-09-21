import streamlit as st
import calculations as calc
import iso
# TILLFÄLLIGT BORTKOMMENTERADE IMPORTER (Slås på sen när vi fixar deras filer):
# import semicircles
# import rectangles
# import pyramid
import sympy as sp

st.subheader("The Right Place")

# --------------------------------------------------
# 1. BYGG GRÄNSSNITTET MED STREAMLITS INBYGGDA INSTÄLLNINGAR
# --------------------------------------------------

primary_blue = st.get_option("theme.primaryColor") or "#0041BA"

st.sidebar.markdown(
    f"""
    <style>
    div[data-baseweb="input"], div[data-baseweb="number-input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid {primary_blue} !important;
    }}
    div[data-baseweb="input"] input, div[data-baseweb="number-input"] input {{
        color: {primary_blue} !important;
        -webkit-text-fill-color: {primary_blue} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

n = st.sidebar.number_input(
    "n:", 
    min_value=2, 
    max_value=15, 
    value=4, 
    step=1
)

st.sidebar.text("")

eq_input = st.sidebar.text_input(
    "x:", 
    value="1+x=x^n"
)

placeholder_x = st.sidebar.empty()
st.sidebar.text("")

add_value_str = st.sidebar.text_input(
    "v:", 
    value="x^n-1"
)

placeholder_v = st.sidebar.empty()
st.sidebar.text("")


# --------------------------------------------------
# 2. KÖR BERÄKNINGARNA (Grundmatematiken)
# --------------------------------------------------
math_data = calc.get_math_data(
    n,
    eq_input,
    add_value_str
)


# --------------------------------------------------
# 3. FYLL I PLATSHÅLLARNA MED RESULTATEN
# --------------------------------------------------
with placeholder_x:
    with st.container():
        if not math_data["is_equation"]:
            st.markdown(f"$x = {sp.latex(math_data['x_symbolic'])}$")
        else:
            if math_data["minimal_poly"] is not None:
                n_sym = sp.Symbol("n")
                poly_display = math_data["minimal_poly"].subs(n_sym, n)
                st.markdown(f"$x \\Rightarrow {sp.latex(poly_display)} = 0$")
       

with placeholder_v:
    with st.container():
        st.markdown(f"$v \\Rightarrow {sp.latex(math_data['v_simplified'])}$")
      


# --------------------------------------------------
# TABS
# --------------------------------------------------
tab_iso, = st.tabs(
    [
        "n-face",
    ],
    key="main_navigation_tabs"
)


# --------------------------------------------------
# ISOLERADE RENDER-FUNKTIONER (Helt renodlade!)
# --------------------------------------------------

def render_tab_iso(math_data):
    # Alla reglage och layout sköts nu helt internt av iso.py!
    iso.render(math_data)


# --------------------------------------------------
# ÄKTA LAZY LOADING
# --------------------------------------------------

with tab_iso:
    render_tab_iso(math_data)
