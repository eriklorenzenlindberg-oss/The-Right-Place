import streamlit as st
import calculations as calc
import iso
# TILLFÄLLIGT BORTKOMMENTERADE IMPORTER:
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
# TABS (Bortkommenterat on_change och övriga flikar)
# --------------------------------------------------
# Vi skapar bara en flik nu för att testa iso-vyn isolerat
tab_iso, = st.tabs(
    [
        "n-face",
    ],
    # on_change="rerun",  # Borttaget då det kan orsaka oändliga laddnings-loopar
    key="main_navigation_tabs"
)


# --------------------------------------------------
# ISOLERADE RENDER-FUNKTIONER
# --------------------------------------------------

def render_tab_iso(math_data):
    col_plot, col_controls = st.columns([7, 1])
    with col_controls:
        st.text(" ")
        st.text(" ")
        st.text(" ")
        st.text(" ")
        st.text(" ")
        st.text(" ")

        rotate_fig2 = st.checkbox("Rotate", value=False)
        show_nodes = st.checkbox("Nodes", value=False)
        node_size = st.slider("Node size", 1, 3, 1)
        linewidth = st.slider("Line width", 0.1, 1.0, 0.3, 0.1)     

    with col_plot:
        iso.render(math_data, linewidth, node_size, show_nodes, rotate_fig2)


# --------------------------------------------------
# ÄKTA LAZY LOADING (Endast ISO aktiv)
# --------------------------------------------------

with tab_iso:
        render_tab_iso(math_data)
