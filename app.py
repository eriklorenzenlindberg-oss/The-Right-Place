import streamlit as st
import calculations as calc
import iso
import semicircles 
import rectangles
import pyramid
import sympy as sp

# 1. SÄTT SIDAN TILL BREDBILD
st.set_page_config(layout="wide")

# --- HUVUDLAYOUT
st.subheader("The Right Place")

# Skapa de tre kolumnerna enligt din önskade fördelning
a_kol, b_kol, c_kol = st.columns([1, 1, 4])


# --------------------------------------------------
# KOLUMN A: HUVUDPARAMETRAR (n, x, v)
# --------------------------------------------------
with a_kol:
    
    n = st.number_input(
        "n (dimensions):", 
        min_value=2, 
        max_value=15, 
        value=4, 
        step=1
    )

    eq_input = st.text_input(
        "x (ratio):", 
        value="1+x=x^n"
    )

    placeholder_x = st.empty()

    add_value_str = st.text_input(
        "v (adds to side 1):", 
        value="x^n-1"
    )

    placeholder_v = st.empty()


# --------------------------------------------------
# KOLUMN B: RADIOKNAPPARNA (Navigering)
# --------------------------------------------------
with b_kol:
    
    valt_diagram = st.radio(
        "k-face:",
        options=["n-face", "1-faces", "2-faces", "3-faces"],
        key="main_navigation_radio"
    )


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
if not math_data["is_equation"]:
    placeholder_x.markdown(f"$\\small x = {sp.latex(math_data['x_symbolic'])}$")
else:
    if math_data["minimal_poly"] is not None:
        n_sym = sp.Symbol("n")
        poly_display = math_data["minimal_poly"].subs(n_sym, n)
        placeholder_x.markdown(f"$\\small x \\Rightarrow {sp.latex(poly_display)} = 0$")
       
placeholder_v.markdown(f"$\\small v \\Rightarrow {sp.latex(math_data['v_simplified'])}$")


# --------------------------------------------------
# KOLUMN C: EXPANDER OCH DIAGRAM
# --------------------------------------------------
with c_kol:
    with st.expander("Visualizing generalizations of the golden rectangle and self-similarity in n-dimensional space"):
        st.markdown(
            """<small>
            Any rectangle that is not a square can be extended in one dimension without deformation...
            [Hela din introduktionstext ligger här]
            </small>""", 
            unsafe_allow_html=True
        )

    # ÄKTA LAZY LOADING (Nu inuti kolumn C)
    if valt_diagram == "n-face":
        iso.render(math_data)

    elif valt_diagram == "1-faces":
        semicircles.render(math_data)

    elif valt_diagram == "2-faces":
        rectangles.render(math_data)

    elif valt_diagram == "3-faces":
        pyramid.render(math_data)
