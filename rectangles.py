import math

import plotly.graph_objects as go
import streamlit as st
import sympy as sp

X = sp.Symbol("x")

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"x{''.join(superscripts.get(c, c) for c in str(power))}"

def exact_power_exponent(expr, numeric_value, math_data):
    """
    Returnerar j (heltal, kan vara negativt) om expr exakt är x^j, annars None.
    Kontrollen är exakt (delbarhet med minimalpolynomet). Det numeriska värdet
    används bara för att välja vilket j som ska kontrolleras.
    Negativa j behövs när v < 1, t.ex. v = 1/x.
    """
    x = math_data["x_numeric"]
    if expr is None or x <= 1.0 or numeric_value <= 0:
        return None
    j = round(math.log(numeric_value) / math.log(x))
    if abs(j) > 200:
        return None
    try:
        minimal_poly = sp.expand(math_data["minimal_poly"])
        # expr = x^j  <=>  expr - x^j = 0  (för j < 0: expr * x^(-j) - 1 = 0)
        diff = expr - X ** j if j >= 0 else expr * X ** (-j) - 1
        # Uttryck som 1 + 1/x är bråk: x är inte noll, så täljaren avgör
        numerator, _ = sp.fraction(sp.together(sp.expand(diff)))
        if sp.rem(sp.expand(numerator), minimal_poly, X) == 0:
            return j
    except Exception:
        pass
    return None


def v_is_zero(math_data, v_num):
    """True om v exakt är 0 (t.ex. v = 0 eller v = x^2 - x - 1 när x^2 = x + 1)."""
    if abs(v_num) > 1e-12:
        return False
    v = math_data.get("v_exact")
    if v is None:
        return True
    try:
        numerator, _ = sp.fraction(sp.together(sp.expand(v)))
        minimal_poly = sp.expand(math_data["minimal_poly"])
        return sp.rem(sp.expand(numerator), minimal_poly, X) == 0
    except Exception:
        return False


def gnomon_exponent(math_data):
    """
    Returnerar m (1 <= m < n) om v exakt är x^m, annars None.
    Kontrollen är exakt: v - x^m ska vara delbart med minimalpolynomet.
    """
    n = math_data["n"]
    v = math_data.get("v_exact")
    if v is None or math_data["x_numeric"] <= 1.0:
        return None
    try:
        minimal_poly = sp.expand(math_data["minimal_poly"])
        for m in range(1, n):
            if sp.rem(sp.expand(v - X ** m), minimal_poly, X) == 0:
                return m
    except Exception:
        pass
    return None


def render(math_data):
    n = math_data["n"]
    
    # EXAKT SAMMA STRUKTUR SOM ISO: Hämtar listorna direkt
    powers = math_data["lengths1_numeric"]  # [x⁰, x¹, x², ..., xⁿ⁻¹]
    lengths2 = math_data["lengths2_numeric"]
    
    # Plockar ut det numeriska v på ett säkert sätt via index 0
    v_num = lengths2[0] - powers[0]
    gnomon_m = gnomon_exponent(math_data)
    v_zero = v_is_zero(math_data, v_num)  # v = 0: ingen streckad linje och ingen "+v"

    # Exponenter för kolumnerna i figur 2: v = x^j_v och 1 + v = x^j_sum (annars None).
    # Behövs för att veta vilka proportioner kolumnerna har.
    v_exact = math_data.get("v_exact")
    j_v = exact_power_exponent(v_exact, v_num, math_data) if v_num > 0 else None
    j_sum = exact_power_exponent(
        None if v_exact is None else 1 + v_exact, lengths2[0], math_data
    )
    
    line_color = "#FFFFFF"
    bg_color = "rgba(0,0,0,0)"
    
    # --- INSTÄLLNINGAR FÖR DEN STRECKADE KOLUMNEN ---
    dashed_line_color = "#FFFFFF"  
    dashed_line_width = 0.5        # Tunn linje
    dashed_pattern = "3px,3px"     # Streck och mellanrum, kommaseparerat (t.ex. "5px,3px")
    
    # --- SKRAFFERING FÖR GNOMON (samma för rektanglar och kvadrat) ---
    hatch = dict(shape="/", size=6, solidity=0.35, fgcolor="#FFFFFF")  # 45 graders linjer
    
    # --- PANEL-LAYOUT (Exakt som i iso.py) ---
    col_plot, col_controls = st.columns([8, 2])
    
    with col_controls:
        # Sätter en unik nyckel så den inte krockar med iso
        rotate = st.checkbox("Rearrange fig. 2", value=False, key="rectangles_rotate")
        #gnomon = st.checkbox("Gnomon", value=False, key="rectangles_gnomon")
        #if gnomon and gnomon_m is None:
            #st.caption("No gnomon: v is not a power x^m with 1 ≤ m < n.")

        proportions = st.checkbox("Proportions", value=False, key="rectangles_proportions")
        prop_d = None
        if proportions:
            prop_d = st.selectbox(
                "Proportion:",
                options=list(range(1, n)),
                format_func=lambda d: f"1 : {get_math_label(d)}",
                key=f"rectangles_proportion_{n}",
            )
    
    with col_plot:
        fig = go.Figure()
        x_lines, y_lines = [], []
        x_texts, y_texts, text_labels, text_positions = [], [], [], []
        
        # Alla rektanglar med sidornas exponenter: (figur, x0, y0, x1, y1, exp bredd, exp höjd).
        # Används för att markera en proportion med diagonaler.
        prop_rects = []
        
        # Rektanglar i figur 2 som har samma form som extrarektanglarna (gnomon)
        x_marked, y_marked = [], []
        col_starts = {}  # x-läge där varje kolumn i figur 2 börjar
        
        # Separata listor för de streckade linjerna i Fig 2
        x_dashed, y_dashed = [], []
        
        # Med Rearrange ritas den streckade kolumnen som en rad längst ner (om v > 0):
        # raderna blir uppifrån och ner x^2, ..., x^(n-1), 1, v.
        row_layout = rotate and v_num > 0
        
        unit = powers[0]  # Detta är alltid 1.0
        left_col_width = unit + v_num  
        gap = unit * 5.0
        x_max_fig1 = 0.0

        # --------------------------------------------------
        # STRIKT LOOP FÖR BÅDA FIGURERNA
        # --------------------------------------------------
        for fig_idx in range(2):
            x_start = 0.0 if fig_idx == 0 else (x_max_fig1 + gap)
            x_offset = x_start
            y_row_bottom = 0.0

            if fig_idx == 1 and rotate:
                x_label_pos = x_start + left_col_width
            else:
                x_label_pos = x_start
            
            # 1. Höjdannotationer
            for i in range(n - 1):
                p = (n - 1) - i
                if fig_idx == 1 and rotate and p == 1: continue 
                
                x_texts.append(x_label_pos - (unit * 0.3))
                y_texts.append(y_row_bottom + (powers[p]/2))
                text_labels.append(get_math_label(p))
                text_positions.append("middle left")
                
                y_row_bottom += powers[p]

            # 2. Rektanglar och bredd-texter
            for col in range(n - 1):
                if fig_idx == 1:
                    col_starts[col] = x_offset
                # --- Generera den streckade kolumnen 1 i Figur 2 ---
                if fig_idx == 1 and col == 0:
                    if row_layout:
                        # Den streckade kolumnen ritas som en rad längst ner (se "Vid rotation")
                        x_offset += left_col_width
                        continue
                    n_dash_before, n_rect_before = len(x_dashed), len(prop_rects)
                    dash_col_width = unit 
                    x_dl = x_start + v_num
                    x_dr = x_dl + dash_col_width
                    
                    # Beräkna totalhöjden för den streckade kolumnen
                    total_dash_height = sum(powers[power] for power in range(n - 1, 0, -1))
                    
                    # 1. Lång sammanhängande vänsterlinje (nerifrån och upp)
                    x_dashed.extend([x_dl, x_dl, None])
                    y_dashed.extend([0.0, total_dash_height, None])
                    
                    # 2. Lång sammanhängande högerlinje (nerifrån och upp)
                    x_dashed.extend([x_dr, x_dr, None])
                    y_dashed.extend([0.0, total_dash_height, None])
                    
                    # 3. Horisontella avdelare
                    y_dash_offset = 0.0
                    # Bottenlinje
                    x_dashed.extend([x_dl, x_dr, None])
                    y_dashed.extend([y_dash_offset, y_dash_offset, None])
                    
                    for power in range(n - 1, 0, -1):
                        y_before = y_dash_offset
                        y_dash_offset += powers[power]
                        # Mellanväggar och topplinje
                        x_dashed.extend([x_dl, x_dr, None])
                        y_dashed.extend([y_dash_offset, y_dash_offset, None])
                        # Kolumn 1 (bredd 1) och, utan Rearrange, kolumn v (bredd v)
                        prop_rects.append((1, x_dl, y_before, x_dr, y_dash_offset, 0, power))
                        if not rotate and v_num > 0:
                            prop_rects.append((1, x_start, y_before, x_start + v_num, y_dash_offset, j_v, power))
                    
                    if v_zero:
                        # v = 0: ingen streckad kolumn (den skulle bara ligga ovanpå kolumnen)
                        del x_dashed[n_dash_before:]
                        del y_dashed[n_dash_before:]
                        del prop_rects[n_rect_before:]
                    
                    if rotate:
                        x_offset += left_col_width
                        continue
                    else:
                        width = left_col_width
                else:
                    width = powers[col]

                if not (fig_idx == 1 and rotate):
                    if fig_idx == 1 and col == 0 and v_num > 0:
                        # 1 står under kolumnen med bredden 1 (den streckade) och v under
                        # kolumnen med extrarektanglarna, som är v bred och ligger till vänster
                        x_texts.extend([x_start + v_num / 2, x_start + v_num + unit / 2])
                        y_texts.extend([-(unit * 0.3)] * 2)
                        text_labels.extend(["v", "1"])
                        text_positions.extend(["bottom center"] * 2)
                    else:
                        x_texts.append(x_offset + (width/2))
                        y_texts.append(-(unit * 0.3))
                        text_labels.append(("1" if v_zero else "1+v") if (fig_idx == 1 and col == 0) else get_math_label(col))
                        text_positions.append("bottom center")

                y_offset = 0.0
                for power in range(n - 1, col, -1):
                    x0, y0 = x_offset, y_offset
                    x1, y1 = x0 + width, y0 + powers[power]
                    x_lines.extend([x0, x1, x1, x0, x0, None])
                    y_lines.extend([y0, y0, y1, y1, y0, None])
                    prop_rects.append((fig_idx, x0, y0, x1, y1,
                                       j_sum if (fig_idx == 1 and col == 0) else col, power))
                    # Sidorna x^col och x^power: formen {x^m, x^p} om en av dem är x^m
                    if (gnomon and gnomon_m is not None and fig_idx == 1 and col >= 1
                            and (col == gnomon_m or power == gnomon_m)):
                        x_marked.extend([x0, x1, x1, x0, x0, None])
                        y_marked.extend([y0, y0, y1, y1, y0, None])
                    y_offset += powers[power]
                x_offset += width

            if fig_idx == 1:
                col_starts[n - 1] = x_offset

            if fig_idx == 0:
                x_max_fig1 = x_offset 

            # 3. Vid rotation
            if fig_idx == 1 and rotate:
                y_bottom = -left_col_width
                
                if row_layout:
                    # Raden (1+v) delas i raden 1 (överst, streckad) och raden v (under)
                    x_texts.extend([x_label_pos - (unit * 0.3)] * 2)
                    y_texts.extend([-unit / 2, -unit - v_num / 2])
                    text_labels.extend(["1", "v"])
                    text_positions.extend(["middle left"] * 2)
                else:
                    x_texts.append(x_label_pos - (unit * 0.3))
                    y_texts.append(y_bottom + (left_col_width / 2))
                    text_labels.append("1" if v_zero else "1+v")
                    text_positions.append("middle left")
                
                x_row_offset = x_start + left_col_width
                for col in range(1, n):
                    x0, y0 = x_row_offset, y_bottom
                    x1, y1 = x0 + powers[col], 0
                    x_lines.extend([x0, x1, x1, x0, x0, None])
                    y_lines.extend([y0, y0, y1, y1, y0, None])
                    prop_rects.append((1, x0, y0, x1, y1, col, j_sum))
                    if row_layout:
                        # Streckad kontur runt cellerna i raden 1 (höjd 1, närmast rutnätet)
                        x_dashed.extend([x0, x1, x1, x0, x0, None])
                        y_dashed.extend([-unit, -unit, 0.0, 0.0, -unit, None])
                        prop_rects.append((1, x0, -unit, x1, 0.0, col, 0))        # raden 1: x^col × 1
                        prop_rects.append((1, x0, y_bottom, x1, -unit, col, j_v))  # raden v: x^col × v
                    
                    x_texts.append(x_row_offset + (powers[col]/2))
                    y_texts.append(y_bottom - (unit * 0.3))
                    text_labels.append(get_math_label(col))
                    text_positions.append("bottom center")
                    
                    x_row_offset += powers[col]
                x_offset = max(x_offset, x_row_offset)

        # --------------------------------------------------
        # TRACES & LAYOUT (Matchad höjd och hastighet med iso)
        # --------------------------------------------------
        # Gnomon: markerade rektanglar och den tänkta kvadraten får exakt samma skraffering
        # (kvadraten utan kontur). Ritas före linjerna så att konturerna ligger överst.
        if x_marked:
            fig.add_trace(go.Scatter(
                x=x_marked, y=y_marked, mode="none", fill="toself",
                fillcolor="rgba(0,0,0,0)", fillpattern=hatch,
                hoverinfo="skip", showlegend=False
            ))
        if gnomon and gnomon_m is not None and gnomon_m in col_starts:
            sx = col_starts[gnomon_m]
            sy = sum(powers[q] for q in range(gnomon_m + 1, n))
            side = powers[gnomon_m]
            fig.add_trace(go.Scatter(
                x=[sx, sx + side, sx + side, sx, sx],
                y=[sy, sy, sy + side, sy + side, sy],
                mode="none", fill="toself", fillcolor="rgba(0,0,0,0)",
                fillpattern=hatch,
                hoverinfo="skip", showlegend=False
            ))

        # Huvudlinjer (Solida)
        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode="lines", line=dict(color=line_color, width=1.0), hoverinfo="skip", showlegend=False))
        
        # Proportion: en diagonal i varje rektangel med den valda proportionen 1 : x^d.
        # Stående rektanglar: från övre vänstra hörnet. Liggande: från nedre vänstra hörnet.
        if prop_d is not None:
            x_diag, y_diag = [], []
            for _, x0, y0, x1, y1, w_exp, h_exp in prop_rects:
                if w_exp is None or h_exp is None or abs(h_exp - w_exp) != prop_d:
                    continue
                x_diag.extend([x0, x1, None])
                if h_exp > w_exp:   # stående
                    y_diag.extend([y1, y0, None])
                else:               # liggande
                    y_diag.extend([y0, y1, None])
            if x_diag:
                fig.add_trace(go.Scatter(
                    x=x_diag, y=y_diag, mode="lines",
                    line=dict(color=line_color, width=1.0),
                    hoverinfo="skip", showlegend=False
                ))
        
        # Den streckade kolumnen som ett eget lager
        if x_dashed:
            fig.add_trace(go.Scatter(
                x=x_dashed, y=y_dashed, mode="lines", 
                line=dict(color=dashed_line_color, width=dashed_line_width, dash=dashed_pattern), 
                hoverinfo="skip", showlegend=False
            ))
        
        # Textetiketter
        fig.add_trace(go.Scatter(
            x=x_texts, y=y_texts, text=text_labels, mode="text",
            textposition=text_positions, textfont=dict(color=line_color, size=11),
            hoverinfo="skip", showlegend=False
        ))

        x_start_fig2 = x_max_fig1 + gap
        y_top = sum(powers[p] for p in range(1, n))
        x_right = x_start_fig2 + left_col_width + sum(powers[k] for k in range(1, n))
        span = max(x_right - (-unit * 0.5), y_top - (-left_col_width))
        margin = span * 0.05
        x_min = -unit * 0.5 - margin
        x_max = x_right + margin
        y_min = -left_col_width - margin
        y_max = y_top + margin

        fig.update_layout(
            height=290,  # Samma höjd som iso för visuell symmetri!
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False, 
            margin=dict(l=5, r=5, t=5, b=5),
            dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[y_min, y_max])
        )
        
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': False},
                        key="rectangles_plot_short")
