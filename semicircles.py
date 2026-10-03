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

def get_layer_geometry_numeric_v2(combo, lengths_numeric):
    """ 
    UPPDATERAD: Hämtar diametern direkt från de förberäknade listorna 
    (lengths1_numeric eller lengths2_numeric) baserat på potensen k.
    """
    centers = []
    current_x = 0.0
    for k in combo:
        # k är potensen (t.ex. 0, 1, 2...). Vi mappar den mot index i listan.
        if k < len(lengths_numeric):
            diameter = float(lengths_numeric[k])
        else:
            # Fallback om potensen är utanför grundlängderna (beräknas som vanligt)
            diameter = float(lengths_numeric[0] * (lengths_numeric[1]**k) if len(lengths_numeric) > 1 else 1.0)
            
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

def evaluate_global_layout_numeric_v2(sorted_matches, lengths_numeric):
    """ Optimerar layout utifrån de specifika diametrarna i lengths_numeric """
    optimized_layouts = []
    global_drawn_centers = set()
    
    for idx, combo_keys in enumerate(sorted_matches):
        if idx == 0:
            optimized_layouts.append(combo_keys)
            centers = get_layer_geometry_numeric_v2(combo_keys, lengths_numeric)
            for k, x_center, _ in centers:
                global_drawn_centers.add((k, round(x_center, 5)))
            continue
            
        best_score = -1
        best_layout = tuple(sorted(list(combo_keys)))
        
        for perm in itertools.permutations(combo_keys):
            centers = get_layer_geometry_numeric_v2(perm, lengths_numeric)
            score = 0
            for k, x_center, _ in centers:
                if (k, round(x_center, 5)) in global_drawn_centers:
                    score += 5
            
            if score > best_score:
                best_score = score
                best_layout = perm
                
        optimized_layouts.append(best_layout)
        final_centers = get_layer_geometry_numeric_v2(best_layout, lengths_numeric)
        for k, x_center, _ in final_centers:
            global_drawn_centers.add((k, round(x_center, 5)))
            
    return optimized_layouts

def draw_single_rotated_plot(final_layouts, selected_idx, lengths_numeric, line_color, bg_color):
    """ Hjälpfunktion för att bygga ett enskilt roterat diagram """
    fig = go.Figure()
    x_lines, y_lines = [], []
    theta_upper = np.linspace(0, np.pi, 40)
    
    # Beräkna totala längden för baslinjen baserat på den första kombinationen (huvudleden)
    first_combo_centers = get_layer_geometry_numeric_v2(final_layouts[0], lengths_numeric)
    target_value = sum(c[2] for c in first_combo_centers) if first_combo_centers else 1.0

    # 1. Rita den markerade kombinationen (Tjock linje)
    if 0 <= selected_idx < len(final_layouts):
        chosen_combo = final_layouts[selected_idx]
        chosen_centers = get_layer_geometry_numeric_v2(chosen_combo, lengths_numeric)
        for k, x_center, diameter in chosen_centers:
            radius = diameter / 2.0
            cx = x_center + radius * np.cos(theta_upper)
            cy = radius * np.sin(theta_upper)
            
            # Rotation 90 grader moturs: x_ny = -cy, y_ny = cx
            fig.add_trace(go.Scatter(
                x=-cy, y=cx, 
                mode="lines", 
                line=dict(color=line_color, width=2.5), 
                hoverinfo="skip", 
                showlegend=False
            ))

    # 2. Rita alla unika cirklar i bakgrunden (Tunna linjer)
    all_radii = []
    drawn_circles = set()
    for combo in final_layouts:
        centers = get_layer_geometry_numeric_v2(combo, lengths_numeric)
        for k, x_center, diameter in centers:
            radius = diameter / 2.0
            all_radii.append(radius)
            
            circle_id = (k, round(x_center, 5))
            if circle_id not in drawn_circles:
                drawn_circles.add(circle_id)
                cx = x_center + radius * np.cos(theta_upper)
                cy = radius * np.sin(theta_upper)
                
                x_lines.extend(list(-cy) + [None])
                y_lines.extend(list(cx) + [None])

    # Roterad baslinje
    x_lines.extend([0.0, 0.0, None])
    y_lines.extend([0.0, target_value, None])

    fig.add_trace(go.Scatter(
        x=x_lines, y=y_lines, 
        mode="lines", 
        line=dict(color=line_color, width=0.7), 
        hoverinfo="skip", 
        showlegend=False
    ))

    # Geometrisk skalning 1:1
    max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
    base_x_margin = target_value * 0.05
    total_graph_width = target_value + (2 * base_x_margin)
    required_y_space = total_graph_width * 0.5

    if max_actual_height > (required_y_space * 0.85):
        required_y_space = max_actual_height / 0.80
        total_x_span = required_y_space * 2.0
        y_min = -(total_x_span - target_value) / 2.0
        y_max = target_value + (total_x_span - target_value) / 2.0
    else:
        y_min, y_max = -base_x_margin, target_value + base_x_margin

    y_center_point = max_actual_height / 2.0
    x_min = -(y_center_point + (required_y_space / 2.0))
    x_max = -(y_center_point - (required_y_space / 2.0))

    fig.update_layout(
        plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10), height=400, dragmode=False,
        xaxis=dict(visible=False, range=[x_min, x_max]),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
    )
    return fig

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
    # Hämta de förberäknade listorna med längder/diametrar från calculations.py
    lengths1_numeric = math_data["lengths1_numeric"]
    lengths2_numeric = math_data["lengths2_numeric"]
    
    raw_matches = find_math_structures_logical(n, minimal_poly, x_numeric)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # NY LAYOUT: Tre kolumner (Vänster diagram, Höger diagram, Kontroller längst till höger)
    col_plot1, col_plot2, col_controls = st.columns([4, 4, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key="circles_overlap")
        
        if max_overlap:
            final_layouts1 = evaluate_global_layout_numeric_v2(sorted_matches, lengths1_numeric)
            final_layouts2 = evaluate_global_layout_numeric_v2(sorted_matches, lengths2_numeric)
        else:
            final_layouts1 = sorted_matches
            final_layouts2 = sorted_matches

        combo_labels = [" + ".join(get_math_label(k) for k in combo) for combo in final_layouts1]
        selected_option = st.radio(
