import itertools
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp
from collections import deque

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    power_int = int(power)
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"x{''.join(superscripts.get(c, c) for c in str(power_int))}"

def get_layer_geometry_numeric(combo, x_numeric):
    """ Beräknar geometri och centrum baserat på flyttalsvärden """
    centers = []
    current_x = 0.0
    for k in combo:
        diameter = float(x_numeric**k)
        radius = diameter / 2.0
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return centers

def get_layer_geometry_from_list(combo, lengths_numeric):
    """ Beräknar geometri baserat på en färdig lista med diametrar (för 1 + v) """
    centers = []
    current_x = 0.0
    for k in combo:
        if k < len(lengths_numeric):
            diameter = float(lengths_numeric[k])
        else:
            diameter = 1.0
        radius = diameter / 2.0
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return centers

def find_math_structures_logical(n, minimal_poly, x_numeric):
    """ Sökning som dynamiskt sätter gränsen baserat på summan av huvudleden """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    target_value = sum(float(x_numeric**m) for m in range(n))
    max_k = n
    while float(x_numeric**max_k) <= target_value:
        max_k += 1
    
    MAX_POWER = max(max_k + 2, n + 5)
    VECTOR_SIZE = MAX_POWER + 1
    
    P_x = sp.expand(minimal_poly)
    huvudled_vektor = [0] * VECTOR_SIZE
    for i in range(n):
        if i < VECTOR_SIZE:
            huvudled_vektor[i] = 1
            
    regler_vektorer = []
    for k in range(VECTOR_SIZE):
        regel = sp.expand(P_x * x**k)
        vektor = [0] * VECTOR_SIZE
        giltig = True
        
        for p in range(VECTOR_SIZE):
            c = regel.coeff(x, p)
            if c != 0:
                vektor[p] = int(c)
                
        for p in range(VECTOR_SIZE, VECTOR_SIZE + 10):
            if regel.coeff(x, p) != 0:
                giltig = False
                break
        if giltig and any(v != 0 for v in vektor):
            regler_vektorer.append(vektor)

    giltiga_kombinationer = set()
    besökta = set()
    start_tuple = tuple(huvudled_vektor)
    kö = deque([start_tuple])
    besökta.add(start_tuple)
    giltiga_kombinationer.add(tuple(range(n)))
    
    while kö:
        aktuell = kö.popleft()
        for reg_vek in regler_vektorer:
            for tecken in [1, -1]:
                ny_vektor = [a + tecken * b for a, b in zip(aktuell, reg_vek)]
                if any(v < 0 for v in ny_vektor):
                    continue
                ny_tuple = tuple(ny_vektor)
                if ny_tuple in besökta:
                    continue
                potenser = [idx for idx, v in enumerate(ny_vektor) if v == 1]
                if potenser and max(potenser) > max_k:
                    continue
                if sum(ny_vektor) == len(potenser) and len(potenser) > 0:
                    giltiga_kombinationer.add(tuple(sorted(potenser)))
                if max(ny_vektor) <= 2:
                    if len(besökta) < 3000:
                        besökta.add(ny_tuple)
                        kö.append(ny_tuple)
                        
    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))

def evaluate_global_layout_numeric(sorted_matches, x_numeric):
    """ Matchar permutationer mot en global databas av existerande centrum """
    optimized_layouts = []
    global_drawn_centers = set()
    for idx, combo_keys in enumerate(sorted_matches):
        if idx == 0:
            optimized_layouts.append(combo_keys)
            centers = get_layer_geometry_numeric(combo_keys, x_numeric)
            for k, x_center, _ in centers:
                global_drawn_centers.add((k, round(x_center, 5)))
            continue
        best_score = -1
        best_layout = tuple(sorted(list(combo_keys)))
        for perm in itertools.permutations(combo_keys):
            centers = get_layer_geometry_numeric(perm, x_numeric)
            score = 0
            for k, x_center, _ in centers:
                if (k, round(x_center, 5)) in global_drawn_centers:
                    score += 5
            if score > best_score:
                best_score = score
                best_layout = perm
        optimized_layouts.append(best_layout)
        final_centers = get_layer_geometry_numeric(best_layout, x_numeric)
        for k, x_center, _ in final_centers:
            global_drawn_centers.add((k, round(x_center, 5)))
    return optimized_layouts

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
    lengths1_numeric = math_data.get("lengths1_numeric", [float(x_numeric**k) for k in range(n)])
    lengths2_numeric = math_data.get("lengths2_numeric", lengths1_numeric.copy())
    
    raw_matches = find_math_structures_logical(n, minimal_poly, x_numeric)
    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    target_value = sum(float(x_numeric**m) for m in range(n))
    if target_value == 0: target_value = 1.0

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key=f"circles_overlap_{n}")
        if max_overlap:
            final_layouts = evaluate_global_layout_numeric(sorted_matches, x_numeric)
        else:
            final_layouts = sorted_matches

        combo_labels = [" + ".join(get_math_label(k) for k in combo) for combo in final_layouts]
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_labels,
            index=0,
            key=f"circles_highlight_{n}_{max_overlap}"
        )
        selected_idx = combo_labels.index(selected_option)

    with col_plot:
        line_color, bg_color = "#FFFFFF", "rgba(0,0,0,0)"
        fig = go.Figure()
        theta_upper = np.linspace(0, np.pi, 40)
        
        # SÄKERT UTGÅNGSPUNKT: Hämta geometri utifrån den första valda layouten (huvudleden)
        chosen_base_layout = final_layouts[0] if final_layouts else main_line
        centers_sample = get_layer_geometry_numeric(chosen_base_layout, x_numeric)
        max_radius = max((d/2.0) for _, _, d in centers_sample) if centers_sample else (target_value * 0.5)
        
        # Geometri för diagram 2 (Enbart huvudleden med 1 + v)
        main_centers_v = get_layer_geometry_from_list(chosen_base_layout, lengths2_numeric)
        max_rad2 = max((d/2.0) for _, _, d in main_centers_v) if main_centers_v else max_radius
        
        # POSITIV OFFSET: Flyttar diagram 2 till höger om diagram 1
        gap = max_radius * 0.8
        fig2_x_offset = max_rad2 * 2.0 + gap

        # --- BERÄKNA FÖRSKJUTNING I HÖJDLED (Y-AXELN) FÖR ATT LINJERA CIRKEL x ---
        y_offset_fig2 = 0.0
        
        bottom_x_fig1 = 0.0
        for k, x_center, diameter in centers_sample:
            if k == 1:
                bottom_x_fig1 = x_center - (diameter / 2.0)
                break
                
        bottom_x_fig2 = 0.0
        for k, x_center, diameter in main_centers_v:
            if k == 1:
                bottom_x_fig2 = x_center - (diameter / 2.0)
                break
        
        y_offset_fig2 = bottom_x_fig1 - bottom_x_fig2

        # --------------------------------------------------
        # DIAGRAM 1: STANDARD (VÄNSTER)
        # --------------------------------------------------
        x_bg1, y_bg1 = [], []
        drawn_circles = set()
        for combo in final_layouts:
            centers = get_layer_geometry_numeric(combo, x_numeric)
            for k, x_center, diameter in centers:
                radius = diameter / 2.0
                circle_id = (k, round(x_center, 5))
                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_bg1.extend(list(-cy) + [None])
                    y_bg1.extend(list(cx) + [None])

        # Baslinje 1
        x_bg1.extend([0.0, 0.0, None])
        y_bg1.extend([0.0, target_value, None])
        
        fig.add_trace(go.Scatter(x=x_bg1, y=y_bg1, mode="lines", line=dict(color=line_color, width=0.7), hoverinfo="skip", showlegend=False))

        # Markera vald kombination i Diagram 1
        if 0 <= selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            chosen_centers = get_layer_geometry_numeric(chosen_combo, x_numeric)
            for k, x_center, diameter in chosen_centers:
                radius = diameter / 2.0
                cx = x_center + radius * np.cos(theta_upper)
                cy = radius * np.sin(theta_upper)
                fig.add_trace(go.Scatter(x=-cy, y=cx, mode="lines", line=dict(color=line_color, width=2.5), hoverinfo="skip", showlegend=False))


        # --------------------------------------------------
        # DIAGRAM 2: MODIFIERAD (HÖGER) - Med höjdjustering
        # --------------------------------------------------
        x_bg2, y_bg2 = [], []
        
        for k, x_center, diameter in main_centers_v:
            radius = diameter / 2.0
            cx = x_center + radius * np.cos(theta_upper)
            cy = radius * np.sin(theta_upper)
            
            x_bg2.extend(list(-cy + fig2_x_offset) + [None])
            y_bg2.extend(list(cx + y_offset_fig2) + [None])

        # Baslinje 2
        target_value_v = sum(d for _, _, d in main_centers_v) if main_centers_v else target_value
        x_bg2.extend([fig2_x_offset, fig2_x_offset, None])
        y_bg2.extend([y_offset_fig2, y_offset_fig2 + target_value_v, None])
        
        fig.add_trace(go.Scatter(x=x_bg2, y=y_bg2, mode="lines", line=dict(color=line_color, width=2.5), hoverinfo="skip", showlegend=False))


        # --- GEMENSAM SKALNING ---
        y_max_bound = max(target_value, y_offset_fig2 + target_value_v)
        y_min_bound = min(0.0, y_offset_fig2)
        
        y_min = y_min_bound - (y_max_bound - y_min_bound) * 0.05
        y_max = y_max_bound + (y_max_bound - y_min_bound) * 0.05
        
        x_min = -(max_radius * 2.0) - (max_radius * 0.1)
        x_max = fig2_x_offset + (max_radius * 0.1)

        y_span = y_max - y_min
        x_span = x_max - x_min
        if y_span > x_span:
            diff = (y_span - x_span) / 2.0
            x_min -= diff
            x_max += diff
        else:
            diff = (x_span - y_span) / 2.0
            y_min -= diff
            y_max += diff

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=290, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(fig, use_container_width=True, key=f"semicircles_combined_{n}")

    st.markdown("<style>.modebar { display: none !important; }</style>", unsafe_allow_html=True)
