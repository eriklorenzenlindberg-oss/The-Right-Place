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

def get_layer_geometry_symbolic(combo, pool_symbolic):
    """ Beräknar geometri och centrum med 100% symbolisk exakthet """
    starts = {}
    centers = []
    current_x = sp.Integer(0)
    for k in combo:
        if k not in pool_symbolic: continue
        diameter = pool_symbolic[k]
        radius = diameter / 2
        starts[k] = current_x
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return starts, centers

def evaluate_global_layout(sorted_matches, pool_symbolic):
    """ Matchar layouter med exakt symbolisk algebra i stället för flyttal """
    optimized_layouts = []
    for idx, combo_keys in enumerate(sorted_matches):
        best_score = -1000
        best_layout = tuple(sorted(list(combo_keys)))
        for perm in itertools.permutations(combo_keys):
            _, current_centers = get_layer_geometry_symbolic(perm, pool_symbolic)
            score = 0
            for k, x_center, _ in current_centers:
                for prev_layout in optimized_layouts:
                    _, prev_centers = get_layer_geometry_symbolic(prev_layout, pool_symbolic)
                    for pk, px_center, _ in prev_centers:
                        # Exakt symbolisk jämförelse: drar bort och förenklar till 0
                        if pk == k and sp.simplify(px_center - x_center) == 0:
                            score += 1
            if score > best_score:
                best_score = score
                best_layout = perm
        optimized_layouts.append(best_layout)
    return optimized_layouts

def find_math_structures_logical(n, minimal_poly):
    """ Exakt sökning utan flyttal - Din stabila originalstruktur """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    P_x = sp.expand(minimal_poly)
    MAX_POWER = max(15, n + 5)
    VECTOR_SIZE = MAX_POWER + 1
    
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
                if sum(ny_vektor) == len(potenser) and len(potenser) > 0:
                    giltiga_kombinationer.add(tuple(sorted(potenser)))
                    
                if max(ny_vektor) <= 2:
                    if len(besökta) < 3000:
                        besökta.add(ny_tuple)
                        kö.append(ny_tuple)
                        
    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    pool_symbolic = math_data["circle_pool_symbolic"]
    x_numeric = math_data["x_numeric"]
    x_sym = sp.Symbol("x")
    
    raw_matches = find_math_structures_logical(n, minimal_poly)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    target_value = sum(float(x_numeric**m) for m in range(n))
    if target_value == 0: target_value = 1.0

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # Exakt algebraisk matchning av layouten (Flyttalsfri!)
    overlap_layouts = evaluate_global_layout(sorted_matches, pool_symbolic)

    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")
        final_layouts = overlap_layouts if max_overlap else sorted_matches

        combo_labels = [" + ".join(get_math_label(k) for k in combo) for combo in final_layouts]
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_labels,
            index=0,
            key=f"circles_highlight_{n}_{max_overlap}"
        )
        selected_idx = combo_labels.index(selected_option)

    with col_plot:
        line_color, bg_color = "#000000", "#FFFFFF"
        fig = go.Figure()
        x_lines, y_lines = [], []
        theta_upper = np.linspace(0, np.pi, 40)

        # Rita den markerade kombinationen (Enbart linjer, ingen fyllning)
        if 0 <= selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            _, chosen_centers_sym = get_layer_geometry_symbolic(chosen_combo, pool_symbolic)
            for k, x_center_sym, diameter_sym in chosen_centers_sym:
                x_center = float(x_center_sym.subs(x_sym, x_numeric).evalf())
                diameter = float(diameter_sym.subs(x_sym, x_numeric).evalf())
                radius = diameter / 2.0
                cx = x_center + radius * np.cos(theta_upper)
                cy = radius * np.sin(theta_upper)
                
                fig.add_trace(go.Scatter(
                    x=cx, y=cy, 
                    mode="lines", 
                    line=dict(color=line_color, width=2.5), 
                    hoverinfo="skip", 
                    showlegend=False
                ))

        all_radii, drawn_circles = [], set()
        for combo in final_layouts:
            _, final_centers_sym = get_layer_geometry_symbolic(combo, pool_symbolic)
            for k, x_center_sym, diameter_sym in final_centers_sym:
                x_center = float(x_center_sym.subs(x_sym, x_numeric).evalf())
                diameter = float(diameter_sym.subs(x_sym, x_numeric).evalf())
                radius = diameter / 2.0
                all_radii.append(radius)
                
                # Unikt ID baseras på den exakta symboliska strängen
                circle_id = (k, str(x_center_sym))
                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_lines.extend(list(cx) + [None])
                    y_lines.extend(list(cy) + [None])

        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode="lines", line=dict(color=line_color, width=0.4), hoverinfo="skip", showlegend=False))

        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
        required_y_space = total_graph_width * 0.5

        if max_actual_height > (required_y_space * 0.85):
            required_y_space = max_actual_height / 0.80
            total_x_span = required_y_space * 2.0
            x_min = -(total_x_span - target_value) / 2.0
            x_max = target_value + (total_x_span - target_value) / 2.0
        else:
            x_min, x_max = -base_x_margin, target_value + base_x_margin

        y_center_point = max_actual_height / 2.0
        y_min = y_center_point - (required_y_space / 2.0)
        y_max = y_center_point + (required_y_space / 2.0)

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=400, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )
        st.plotly_chart(fig, use_container_width=True, key="semicircles_plot_clean")
