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

with st.expander("Visualizing generalizations of the golden rectangle and self-similarity in n-dimensional space"):
    st.markdown(
        """<small>
        Any rectangle that is not a square can be extended in one dimension without deformation.
        Take a rectangle with the aspect ratio 1 : x.  (where x > 1). By multiplying the shorter side with x², 
        the rectangle changes in size and orientation but retains its shape. The same result is obtained by 
        adding x² - 1 to the shorter side. This relationship is expressed by the geometric progression formed 
        by the three distinct side lengths of the two configurations:

        1, x, x²

        The golden rectangle is characterized by its sides forming a geometric progression; the shorter side is to the longer side as the longer side is to the sum of both sides:
        1 + x = x²
        Consequently, the golden rectangle retains its shape when the length of the longer side is added to the shorter side.

        </small>ORTHOTOPE<small>

        Any rectangular cuboid with side lengths that form a geometric sequence (1 : x : x²) retains its shape if the shortest side is multiplied by x³, or if x³ - 1 is added to it. 

        The n-dimensional generalization of the rectangle and the cuboid is called an orthotope. Any orthotope with side lengths that form a geometric sequence (1, x, ..., xⁿ⁻¹) retains its shape if the shortest side is multiplied by xⁿ, or if xⁿ - 1 is added to it.

        </small>APPLICATION<small>

        The Right Place visualizes this class of orthotopes, with a specific focus on those whose side lengths are derived from the golden ratio or its generalizations.
        The "n-face" button generates two isometric projections of an orthotope based on user-defined parameters:

        n = the number of dimensions

        x = the ratio governing the side lengths

        v = the value added to the shortest side

        Figure 1 is generated from n and x. Figure 2 shows the orthotope when v is added to the shortest side. 
        If v = xⁿ - 1, the two projections become identical in shape. Selecting "rotate" aligns the orientation of Figure 2 with that of Figure 1.

        </small>1-FACES<small>

        The "1-faces" button displays the side lengths of the orthotope — or its types of 1-faces — represented as the radii of semicircles. When x equals the golden ratio or a generalized golden ratio, such as:

        1 + x = xⁿ

        or

        1 + xⁿ⁻¹ = xⁿ

        the diagram also illustrates how sums of multiple lengths extend the geometric progression of the sides. An orthotope based on the equation 1 + x = xⁿ retains its shape when the length of the second shortest side is added to the shortest side. An orthotope based on the equation 1 + xⁿ⁻¹ = xⁿ retains his shape when the length of the longest side is added to the shortest side.
        For both these examples, the classic golden ratio is obtained when n = 2. The plastic ratio is obtained when n = 3 in the former equation, and when n = 5 in the latter. 

        </small>2-FACES<small>

        The "2-faces" button displays all types of 2-dimensional faces bounding the orthotope, and how this set is altered when extending its shortest side.

        </small>3-FACES<small>

        [Work in progress]
        </small>""", 
        unsafe_allow_html=True
    )

# RÄTTAT: Radioknapparna ligger nu längst ut till vänster (utanför expandern)
valt_diagram = st.radio(
    "k-face:",
    options=["n-face", "1-faces", "2-faces", "3-faces"],
    key="main_navigation_radio",
    horizontal=True
)

# RÄTTAT: Tog bort det extra kommatecknet efter b_kol
a_kol, b_kol = st.columns([4, 1])


# --------------------------------------------------
# KOLUMN B: HUVUDPARAMETRAR (n, x, v) -> Ligger till höger
# --------------------------------------------------
with b_kol:
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
# KOLUMN A: DIAGRAM -> Ligger till vänster (tar upp 4/5 delar)
# --------------------------------------------------
with a_kol:
    # ÄKTA LAZY LOADING
    if valt_diagram == "n-face":
        iso.render(math_data)

    elif valt_diagram == "1-faces":
        semicircles.render(math_data)

    elif valt_diagram == "2-faces":
        rectangles.render(math_data)

    elif valt_diagram == "3-faces":
        pyramid.render(math_data)
