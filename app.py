import streamlit as st
import calculations as calc
import iso
import semicircles
import rectangles
import pyramid
import sympy as sp

st.subheader("The Right Place")

# --------------------------------------------------
# 1. BYGG GRÄNSSNITTET MED STREAMLITS INBYGGDA INSTÄLLNINGAR
# --------------------------------------------------

# 1. Hämta din blåa standardfärg dynamiskt från temat
primary_blue = st.get_option("theme.primaryColor") or "#0041BA"

# 2. Applicera riktad CSS enbart på sidomenyns inmatningsrutor
st.sidebar.markdown(
    f"""
    <style>
    /* Gör bakgrunden på rutorna helt vit */
    div[data-baseweb="input"], div[data-baseweb="number-input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid {primary_blue} !important;
    }}
    
    /* Tvinga texten och siffrorna inuti rutorna att bli blå */
    div[data-baseweb="input"] input, div[data-baseweb="number-input"] input {{
        color: {primary_blue} !important;
        -webkit-text-fill-color: {primary_blue} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# Inbyggd rubrik direkt i sifferinmatningen
n = st.sidebar.number_input(
    "n:", 
    min_value=2, 
    max_value=15, 
    value=4, 
    step=1
)

st.sidebar.text("") # Skapar lite andningsrum istället för streckade linjer

# Inbyggd rubrik direkt i textfältet för x
eq_input = st.sidebar.text_input(
    "x:", 
    value="1+x=x^n"
)

placeholder_x = st.sidebar.empty()
st.sidebar.text("")

# Inbyggd rubrik direkt i textfältet för v
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
tab_iso, tab_circles, tab_rect, tab_pyr = st.tabs(
    [
        "n-face",
        "1-faces",
        "2-faces",
        "3-faces",
    ],
    on_change="rerun", 
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


def render_tab_circles(math_data):
    # Vi rensar bort kolumnerna och checkboxarna härifrån, 
    # eftersom semicircles.py sköter det själv nu!
    semicircles.render(math_data)



def render_tab_rect(math_data):
    rectangles.render(math_data)


def render_tab_pyr(math_data):
    col_plot, col_controls = st.columns([4, 1])
    with col_controls:
        z_gap = st.slider("Z-separation", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
        x_gap = st.slider("Separera rader", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

    with col_plot:
        pyramid.render(math_data, z_gap, x_gap)


# --------------------------------------------------
# ÄKTA LAZY LOADING
# --------------------------------------------------

with tab_iso:
    if tab_iso.open:
        render_tab_iso(math_data)

with tab_circles:
    if tab_circles.open:
        render_tab_circles(math_data)

with tab_rect:
    if tab_rect.open:
        render_tab_rect(math_data)

#with tab_pyr:
    if tab_pyr.open:
        render_tab_pyr(math_data)
