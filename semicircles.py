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

def get_layer_geometry_from_list(combo, lengths_numeric):
    """ Stabil grund: Beräknar geometri och centrum baserat på en färdig lista med diametrar """
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

def find_math_structures_from_list(n, minimal_poly, lengths_numeric):
    """ Dynamisk sökning anpassad för en godtycklig lista med diametrar (t.ex. med 1 + v) """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    # Max tillåten längd baseras på summan av huvudledens diametrar i listan
    target_value = sum(float(lengths_numeric[m]) for m in range(n) if m < len(lengths_numeric))
    
    # Hitta den geometriska maxgränsen baserat på listans värden
    max_k = n
    while max_k < len(lengths_numeric) and float(lengths_numeric[max_k]) <= target_value:
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

def evaluate_global_layout_from_list(sorted_matches, lengths_numeric):
    """ Matchar permutationer mot en global pool utifrån en specifik diameterlista """
    optimized_layouts = []
    global_drawn_centers = set()
    for idx, combo_keys in enumerate(sorted_matches):
        if idx == 0:
            optimized_layouts.append(combo_keys)
            centers = get_layer_geometry_from_list(combo_keys, lengths_numeric)
            for k, x_center, _ in centers:
                global_drawn_centers.add((k, round(x_center, 5)))
            continue
        best_score = -1
        best_layout = tuple(sorted(list(combo_keys)))
        for perm in itertools.permutations(combo_keys):
            centers = get_layer_geometry_from_list(perm, lengths_numeric)
            score = 0
            for k, x_center, _ in centers:
                if (k, round(x_center, 5)) in global_drawn_centers:
                    score += 5
            if score > best_score:
                best_score = score
                best_layout = perm
        optimized_layouts.append(best_layout)
        final_centers = get_layer_geometry_from_list(best_layout, lengths_numeric)
        for k, x_center, _ in final_centers:
            global_drawn_centers.add((k, round(x_center, 5)))
    return optimized_layouts

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
    lengths1_numeric = math_data.get("lengths1_numeric", [float(x_numeric**k) for k in range(n)])
    lengths2_numeric = math_data.get("lengths2_numeric", lengths1_numeric.copy())
    
    # --------------------------------------------------
    # SÖK STRUKTURER SEPARAT FÖR BÅDA DIAGRAMMEN
    # --------------------------------------------------
    raw_matches1 = find_math_structures_from_list(n, minimal_poly, lengths1_numeric)
    raw_matches2 = find_math_structures_from_list(n, minimal_poly, lengths2_numeric)
    
    if not raw_matches1 or len(raw_matches1) == 0:
        st.info("The main line is missing from the data.")
        return

    # Sortera kombinationer för Diagram 1
    unique_combos1 = set(tuple(sorted(list(combo))) for combo in raw_matches1)
    main_line1 = max(unique_combos1, key=len)
    hidden_lines1 = sorted(list(unique_combos1 - {main_line1}), key=lambda c: (len(c), c))
    sorted_matches1 = [main_line1] + hidden_lines1

    # Sortera kombinationer för Diagram 2
    unique_combos2 = set(tuple(sorted(list(combo))) for combo in raw_matches2)
    main_line2 = max(unique_combos2, key=len)
    hidden_lines2 = sorted(list(unique_combos2 - {main_line2}), key=lambda c: (len(c), c))
    sorted_matches2 = [main_line2] + hidden_lines2

    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key=f"circles_overlap_{n}")
        if max_overlap:
            final_layouts1 = evaluate_global_layout_from_list(sorted_matches1, lengths1_numeric)
            final_layouts2 = evaluate_global_layout_from_list(sorted_matches2, lengths2_numeric)
        else:
            final_layouts1 = sorted_matches1
            final_layouts2 = sorted_matches2

        # Kontrollerna (radioknapparna) styrs utifrån Diagram 1:s etiketter
        combo_labels = [" + ".join(get_math_label(k) for k in combo) for combo in final_layouts1]
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
        
        # Mät radier för diagram 1 & 2
        centers_sample1 = get_layer_geometry_from_list(main_line1, lengths1_numeric)
        target_value1 = sum(d for _, _, d in centers_sample1) if centers_sample1 else 1.0
        max_radius1 = max((d/2.0) for _, _, d in centers_sample1) if centers_sample1 else (target_value1 * 0.5)
        
        centers_sample2 = get_layer_geometry_from_list(main_line2, lengths2_numeric)
        target_value2 = sum(d for _, _, d in centers_sample2) if centers_sample2 else 1.0
        max_radius2 = max((d/2.0) for _, _, d in centers_sample2) if centers_sample2 else (target_value2 * 0.5)
        
        # Horisontellt avstånd baserat på diagrammens storlek
        gap = max_radius1 * 0.8
        fig2_x_offset = max_radius2 * 2.0 + gap

        # --- BERÄKNA HÖJDJUSTERING SÅ ATT CIRKEL x LINJERAR FÖR BÅDA ---
        bottom_x_fig1 = 0.0
        for k, x_center, diameter in centers_sample1:
            if k == 1:
                bottom_x_fig1 = x_center - (diameter / 2.0)
                break
                
        bottom_x_fig2 = 0.0
        for k, x_center, diameter in centers_sample2:
            if k == 1:
                bottom_x_fig2 = x_center - (diameter / 2.0)
                break
        
        y_offset_fig2 = bottom_x_fig1 - bottom_x_fig2

        # --------------------------------------------------
        # DIAGRAM 1: STANDARD (VÄNSTER) - Alla dolda strukturer
        # --------------------------------------------------
        x_bg1, y_bg1 = [], []
        drawn_circles1 = set()
        for combo in final_layouts1:
            centers = get_layer_geometry_from_list(combo, lengths1_numeric)
            for k, x_center, diameter in centers:
                radius = diameter / 2.0
                circle_id = (k, round(x_center, 5))
                if circle_id not in drawn_circles1:
                    drawn_circles1.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_bg1.extend(list(-cy) + [None])
                    y_bg1.extend(list(cx) + [None])

        x_bg1.extend([0.0, 0.0, None])
        y_bg1.extend([0.0, target_value1, None])
        fig.add_trace(go.Scatter(x=x_bg1, y=y_bg1, mode="lines", line=dict(color=line_color, width=0.7), hoverinfo="skip", showlegend=False))

        # Markera vald kombination i Diagram 1
        if 0 <= selected_idx < len(final_layouts1):
            chosen_combo = final_layouts1[selected_idx]
            chosen_centers = get_layer_geometry_from_list(chosen_combo, lengths1_numeric)
            for k, x_center, diameter in chosen_centers:
