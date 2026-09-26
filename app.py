import streamlit as st
import calculations as calc
import iso
import semicircles 
# TILLFÄLLIGT BORTKOMMENTERADE IMPORTER:
# import rectangles
# import pyramid
import sympy as sp

# --- HUVUDLAYOUT

st.subheader("The Right Place")
with st.expander("Visualizing generalizations of the golden ratio and self-similarity in n-dimensional space"):
    st.markdown(
    """<small>The golden rectangle is characterized by its self-similar properties. Its short side (1) 
    relates to the long side (x) as the long side relates to the sum of both sides (1 + x = x²). 
    Therefore, the golden rectangle retains its proportions when the length of the long side is added to the short side.

    
This app visualizes orthotopes – the n-dimensional generalizations of rectangles and cuboids – whose side lengths form a 
geometric progression. For any such orthotope, there is a specific value that can be added to the shortest side so that 
the orthotope retains its n-dimensional shape. If the sums of the side lengths further extend the geometric progression, the 
orthotope can be considered an n-dimensional counterpart to the golden rectangle.


There are several algebraic generalizations of the golden ratio that yield this property. For instance, consider the equation 1 + x = xⁿ. An orthotope based on this relation retains its shape when its second shortest side is added to its shortest side. Another example is the equation 1 + xⁿ⁻¹ = xⁿ. An orthotope defined by this relation preserves its shape when its longest side is added to its shortest side.
For both equations, the classic golden ratio is recovered at n = 2. These generalizations also encompass the plastic number: it appears at n = 3 in the first example, and at n = 5 in the second.
</small>""", 
    unsafe_allow_html=True
)

# --------------------------------------------------
# 1. SIDOMENY
# --------------------------------------------------

# STÄDAD CSS: Sätter kritvit bakgrund och neutral mörk text ENBART i sidomenyn
st.sidebar.markdown(
    """
    <style>
    div[data-testid="stSidebar"] div[data-baseweb="input"], 
    div[data-testid="stSidebar"] div[data-baseweb="number-input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CCCCCC !important;
    }
    div[data-testid="stSidebar"] div[data-baseweb="input"] input, 
    div[data-testid="stSidebar"] div[data-baseweb="number-input"] input {
        color: #31333F !important;
        -webkit-text-fill-color: #31333F !important;
    }
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

eq_input = st.sidebar.text_input(
    "x:", 
    value="1+x=x^n"
)

placeholder_x = st.sidebar.empty()

add_value_str = st.sidebar.text_input(
    "v:", 
    value="x^n-1"
)

placeholder_v = st.sidebar.empty()


# --------------------------------------------------
# NAVIGERING I SIDOFÄLTET
# --------------------------------------------------

    options=["n-face", "1-faces"],
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
# Här skriver vi direkt till st.empty() utan extra containers
if not math_data["is_equation"]:
    placeholder_x.markdown(f"$x = {sp.latex(math_data['x_symbolic'])}$")
else:
    if math_data["minimal_poly"] is not None:
        n_sym = sp.Symbol("n")
        poly_display = math_data["minimal_poly"].subs(n_sym, n)
        placeholder_x.markdown(f"$x \\Rightarrow {sp.latex(poly_display)} = 0$")
       
placeholder_v.markdown(f"$v \\Rightarrow {sp.latex(math_data['v_simplified'])}$")
      

# --------------------------------------------------
# ÄKTA LAZY LOADING (Kör bara det diagram som faktiskt visas)
# --------------------------------------------------
if valt_diagram == "n-face":
    iso.render(math_data)

elif valt_diagram == "1-faces":
    semicircles.render(math_data)
