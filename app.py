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
    """<small>TWO DIMENSIONS
Any rectangle that is not a square can be extended in one dimension without deformation.
Take a rectangle with the aspect ratio 1 : x.  (where x > 1). By multiplying the shorter side by the square of the aspect ratio, x², the rectangle changes in size and orientation but retains its shape. The same result is obtained by adding x² - 1 to the shorter side. This relationship is expressed by the geometric progression formed by the three distinct side lengths of the two configurations:

1, x, x²

THE GOLDEN RECTANGLE

The golden rectangle is characterized by its sides forming a geometric progression; the shorter side is to the longer side as the longer side is to the sum of both sides:
1 + x = x²
Consequently, the golden rectangle retains its shape when the length of the longer side is added to the shorter side.

THREE DIMENSIONS

Any rectangular cuboid with side lengths that form a geometric sequence (1 : x : x²) retains its shape if the shortest side is multiplied by x³, or if x³ - 1 is added to it. 

N DIMENSIONS

The n-dimensional generalization of the rectangle and the cuboid is called an orthotope. Any orthotope with side lengths that form a geometric sequence (1, x, ..., xⁿ⁻¹) retains its shape if the shortest side is multiplied by xⁿ, or if xⁿ - 1 is added to it.

THE APPLICATION

The Right Place visualizes this class of orthotopes, with a specific focus on those whose side lengths are derived from the golden ratio or its generalizations.
The "n-face" button generates two isometric projections of an orthotope based on user-defined parameters:
n = the number of dimensions
x = the ratio governing the side lengths
v = the value added to the shortest side
Figure 1 is generated from n and x. Figure 2 shows the orthotope when v is added to the shortest side. If v = xⁿ - 1, the two projections become identical in shape. Selecting "rotate" aligns the orientation of Figure 2 with that of Figure 1.

1-FACES

The lines and rectangles that bound a cuboid can be generalized to k-faces.
The "1-faces" button displays the side lengths of the orthotope — or its types of 1-faces — represented as the radii of semicircles. When x equals the golden ratio or a generalized golden ratio, such as:
1 + x = xⁿ
or
1 + xⁿ⁻¹ = xⁿ
the diagram also illustrates how sums of multiple lengths extend the geometric progression of the sides. An orthotope based on the equation 1 + x = xⁿ retains its shape when the length of the second shortest side is added to the shortest side. An orthotope based on the equation 1 + xⁿ⁻¹ = xⁿ retains his shape when the length of the longest side is added to the shortest side.
For both these examples, the classic golden ratio is obtained when n = 2. The plastic ratio is obtained when n = 3 in the former equation, and when n = 5 in the latter. 

2-FACES

The "2-faces" button displays all types of 2-dimensional faces bounding the orthotope, and how this set is altered when extending its shortest side.

3-FACES

[Work in progress]
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
