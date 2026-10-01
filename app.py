import streamlit as st
import calculations as calc
import iso
import semicircles 
import rectangles
import pyramid
import sympy as sp

# 1. SÄTT SIDAN TILL BREDBILD
st.set_page_config(layout="wide")

# CSS-trick för att tvinga de två översta kolumnerna att ligga sida vid sida på mobilen
st.markdown(
    """
    <style>
    /* Hittar container-raden för de två översta kolumnerna och hindrar dem från att wrappa */
    [data-testid="stHorizontalBlock"]:id-av-övre-raden { 
        flex-wrap: nowrap !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- HUVUDLAYOUT
st.subheader("The Right Place")

# RAD 1: Skapa två kolumner överst (Inställningar och Visualisering)
# Genom att sätta dem i en egen rad separerad från diagrammet, staplas de inte lika aggressivt.
oversta_raden = st.container()
with oversta_raden:
    # Vi kan använda ett explicit mönster för att tvinga layouten på mobilen
    a_kol, b_kol = st.columns([1, 1])

    # KOLUMN A: HUVUDPARAMETRAR
    with a_kol:
        st.markdown("### Settings")
        n = st.number_input("n (dimensions):", min_value=2, max_value=15, value=4, step=1)
        eq_input = st.text_input("x (ratio):", value="1+x=x^n")
        placeholder_x = st.empty()
        add_value_str = st.text_input("v (value added to side 1 (Fig. 2)):", value="x^n-1")
        placeholder_v = st.empty()

    # KOLUMN B: RADIOKNAPPARNA
    with b_kol:
        st.markdown("### Visualization")
        valt_diagram = st.radio(
            "Select visualization:",
            options=["n-face", "1-faces", "2-faces", "3-faces"],
            key="main_navigation_radio"
        )

# En linje som separerar övre delen från diagrammet
st.write("---")

# RAD 2: Expandern och diagrammet hamnar direkt under (använder hela bredden på mobilen)
expander_container = st.container()


# --------------------------------------------------
# 2. KÖR BERÄKNINGARNA (Samma som innan)
# --------------------------------------------------
math_data = calc.get_math_data(n, eq_input, add_value_str)


# --------------------------------------------------
# 3. FYLL I PLATSHÅLLARNA
# --------------------------------------------------
if not math_data["is_equation"]:
    placeholder_x.markdown(f"$\\small x = {sp.latex(math_data['x_symbolic'])}$")
else:
    if math_data["minimal_poly"] is not None:
        n_sym = sp.Symbol("n")
        poly_display = math_data["minimal_poly"].subs(n_sym, n)
        placeholder_x.markdown(f"$\\small x \\Rightarrow {sp.latex(poly_display)} = 0$")
       
placeholder_v.markdown(f"$\\small v \\Rightarrow {sp.latex(math_data['v_simplified'])}$")


# --------------------------------------------------
# RAD 2 INNEHÅLL: DIAGRAM OCH EXPANDER
# --------------------------------------------------
with expander_container:
    with st.expander("Visualizing generalizations of the golden rectangle and self-similarity in n-dimensional space"):
        st.markdown(
            """<small>
            Any rectangle that is not a square can be extended in one dimension without deformation...
            </small>""", 
            unsafe_allow_html=True
        )

    # Diagrammet ritas nu under kolumnerna och tar upp full bredd
    if valt_diagram == "n-face":
        iso.render(math_data)
    elif valt_diagram == "1-faces":
        semicircles.render(math_data)
    elif valt_diagram == "2-faces":
        rectangles.render(math_data)
    elif valt_diagram == "3-faces":
        pyramid.render(math_data)
