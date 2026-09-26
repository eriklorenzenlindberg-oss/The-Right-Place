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
    """<small>More information coming soon.<br><br>
    Generalized golden ratios:<br>
    1+x=x^n<br>
    1+x^(n/2)=x^n<br>
    1+x^(n-1)=x^n<br><br>
    Generalization of the root-rectangles:<br>
    2=x^n<br>
    3=x^n<br>
    4=x^n<br><br>
    And so on...</small>""", 
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
st.sidebar.markdown("---")  # En linje för att separera inställningar och navigering
valt_diagram = st.sidebar.radio(
    "Select visualization:",
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
