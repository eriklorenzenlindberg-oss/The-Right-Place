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
    st.markdown("<small>"More information coming soon.

                Generalized golden ratios:

                1+x=x^n

                1+x^(n/2)=x^n

                1+x^(n-1)=x^n

                Generalization of the "root rectangles":

                2=x^n

                3=x^n

                4=x^n

                And so on.."
    
                </small>", unsafe_allow_html=True)


# --------------------------------------------------
# 1. BYGG GRÄNSSNITTET MED STREAMLITS INBYGGDA INSTÄLLNINGAR
# --------------------------------------------------

primary_blue = st.get_option("theme.primaryColor") or "#0041BA"

st.sidebar.markdown(
    f"""
    <style>
    div[data-baseweb="input"], div[data-baseweb="number-input"] {{
        background-color: #FDFBF7 !important;
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
# NYTT: NAVIGERING I SIDOFÄLTET (Ersätter st.tabs)
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
# ÄKTA LAZY LOADING (Kör bara det diagram som faktiskt visas)
# --------------------------------------------------

if valt_diagram == "n-face":
    iso.render(math_data)

elif valt_diagram == "1-faces":
    semicircles.render(math_data)
