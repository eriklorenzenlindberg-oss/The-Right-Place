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
    """
    Beräknar geometri och centrum baserat på en färdig lista med diametrar.
    Detta gör att ändringen till (1 + v) på index 0 slår igenom helt naturligt.
    """
    centers = []
    current_x = 0.0
    for k in combo:
        if k < len(lengths_numeric):
            diameter = float(lengths_numeric[k])
        else:
            diameter = 1.0  # Säker fallback
            
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

def evaluate_global_layout_from_list(sorted_matches, lengths_numeric):
    """ Optimerar layout utifrån de specifika diametrarna i lengths_numeric """
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
            centers = get_layer_geometry_numeric_or_list(perm, lengths_numeric) if 'get_layer_geometry_numeric_or_list' in globals() else get_layer_geometry_from_list(perm, lengths_numeric)
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

def draw_one_vertical_plot(fig, final_layouts, lengths_numeric, x_offset, selected_idx, line_color):
    """ Ritar ett enskilt vertikalt roterat diagram inuti en delad figur """
    theta_upper = np.linspace(0, np.pi, 40)
    x_background, y_background = [], []

    # 1. Rita alla unika bakgrundscirklar (Tunna linjer)
    drawn_circles = set()
    for combo in final_layouts:
        centers = get_layer_geometry_from_list(combo, lengths_numeric)
        for k, x_center, diameter in centers:
            radius = diameter / 2.0
            
            circle_id = (k, round(x_center, 5))
            if circle_id not in drawn_circles:
                drawn_circles.add(circle_id)
                cx = x_center + radius * np.cos(theta_upper)
                cy = radius * np.sin(theta_upper)
                
                # 90-graders rotation + horisontell placering (x_offset)
                x_background.extend(list(-cy + x_offset) + [None])
                y_background.extend(list(cx) + [None])

    # Beräkna baslinjens totala längd utifrån den första kombinationen (huvudleden)
    first_combo_centers = get_layer_geometry_from_list(final_layouts[0], lengths_numeric) if final_layouts else []
    target_value = sum(d for _, _, d in first_combo_centers) if first_combo_centers else 1.0

    # Lägg till baslinjen för detta diagram
    x_background.extend([x_offset, x_offset, None])
    y_background.extend([0.0, target_value, None])

    fig.add_trace(go.Scatter(
        x=x_background, y=y_background, 
        mode="lines", 
        line=dict(color=line_color, width=0.7), 
        hoverinfo="skip", 
        showlegend=False
    ))

    # 2. Rita den markerade kombinationen (Tjock linje)
    if 0 <= selected_idx < len(final_layouts):
        chosen_combo = final_layouts[selected_idx]
        chosen_centers = get_layer_geometry_from_list(chosen_combo, lengths_numeric)
        for k, x_center, diameter in chosen_centers:
            radius = diameter / 2.0
            cx = x_center + radius * np.cos(theta_upper)
            cy = radius * np.sin(theta_upper)
            
            fig.add_trace(go.Scatter(
                x=-cy + x_offset, y=cx, 
                mode="lines", 
                line=dict(color=line_color, width=2.5), 
                hoverinfo="skip", 
                showlegend=False
            ))
            
    return target_value

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
    # Säkra upp hämtningen av listorna från calculations.py
    lengths1_numeric = math_data.get("lengths1_numeric", [float(x_numeric**k) for k in range(n)])
    lengths2_numeric = math_data.get("lengths2_numeric", lengths1_numeric.copy())
    
    raw_matches = find_math_structures_logical(n, minimal_poly, x_numeric)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # Kontrollpanelen till höger, diagrammen till vänster
    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key=f"circles_overlap_{n}")
        
        if max_overlap:
            final_layouts1 = evaluate_global_layout_from_list(sorted_matches, lengths1_numeric)
            final_layouts2 = evaluate_global_layout_from_list(sorted_matches, lengths2_numeric)
        else:
            final_layouts1 = sorted_matches
            final_layouts2 = sorted_matches

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
        
        # --- RITA DIAGRAM 1: STANDARD (VÄNSTER) ---
        target_val1 = draw_one_vertical_plot(fig, final_layouts1, lengths1_numeric, 0.0, selected_idx, line_color)
        
        # --- RITA DIAGRAM 2: MODIFIERAD 1 + v (HÖGER) ---
        # Beräkna maxradie för figur 1 för att sätta ett horisontellt mellanrum
        centers_sample1 = get_layer_geometry_from_list(final_layouts1[0], lengths1_numeric) if final_layouts1 else []
        max_rad1 = max((d/2.0) for _, _, d in centers_sample1) if centers_sample1 else (target_val1 * 0.5)
        
        gap = max_rad1 * 0.8
        fig2_x_offset = -(max_rad1 * 2.0 + gap)
        
        target_val2 = draw_one_vertical_plot(fig, final_layouts2, lengths2_numeric, fig2_x_offset, selected_idx, line_color)

