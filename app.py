import streamlit as st
import calculations as calc
import iso
import semicircles 
import rectangles
# import pyramid
import sympy as sp

# --- HUVUDLAYOUT

st.subheader("The Right Place")
with st.expander("Visualizing generalizations of the golden rectangle and self-similarity in n-dimensional space"):
    st.markdown(
    """<small>Any rectangle, regardless of its ratio, can be extended in one dimension and retain its shape. 
    Consider the rectangle 1 : x. Multiplying the shorter side by x² yields a length that matches the proportion of the 
    original shape. The same result is obtained by adding x²-1 to the shorter side. Since the new side length is found by multiplying 
    the previous one by x², this creates the geometric sequence 1, x, x².</small>

THE GOLDEN RECTANGLE

<small>The golden rectangle is characterized by the property that its side lengths form a geometric sequence; the ratio of the 
shorter side to the longer side equals the ratio of the longer side to the sum of both sides. This relationship is expressed as:

1 + x = x²

Consequently, the golden rectangle retains its shape when the length of the longer side is added to the shorter side.</small>

ORTHOTOPES

<small>A rectangular cuboid with side lengths that form a geometric sequence (1 : x : x²), retains its shape if the value x³-1 is added to the shortest side.

An orthotopes – the generalization of rectangles and cuboids – with side lengths that form a geometric sequence, retains its shape if
the value is xⁿ−1 is added to the shortest side.</small> 

N-FACE

<small>This application visualizes this class of orthotopes, with a specific focus on those whose side lengths are derived from generalizations of the golden ratio.
The "n-face" button generates two isometric projections of an orthotope. The left projection is generated based on two user-defined parameters:

n = the number of dimensions

x = the ratio governing the side lengths

In the right projection, a value v is added to the shortest side. If v = xⁿ-1, the two projections become identical in shape. Selecting "rotate" aligns their orientation as well.</small>

1-FACES

<small>The "1-faces" button displays the side lengths of the orthotope represented as the radii of semicircles. Semicircles are also drawn whenever the sum of multiple lengths equals a power of x, illustrating how the geometric progression continues through these sums.

There are several algebraic generalizations of the golden ratio that yield this property. For instance, consider the equation 1 + x = xⁿ. 
An orthotope based on this relation retains its shape when the length of the second shortest side is added to the shortest side. Another example is the 
equation 1 + xⁿ⁻¹ = xⁿ. An orthotope defined by this relation preserves its shape when the length of the longest side is added to the shortest side.

For both equations, the classic golden ratio is recovered at n = 2. These generalizations also encompass the plastic number: it appears at 
n = 3 in the first example, and at n = 5 in the second.
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

valt_diagram = st.sidebar.radio(
    "Select visualization:",
    options=["n-face", "1-faces", "2-faces"],
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

elif valt_diagram == "2-faces":
    rectangles.render(math_data)
