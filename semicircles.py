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

def find_math_structures_logical(n, minimal_poly, x_numeric):
    """ Sökning som dynamiskt sätter gränsen baserat på summan av huvudleden """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    # Beräkna max tillåten potens baserat på din regel: x^k <= summan av huvudleden
    target_value = sum(float(x_numeric**m) for m in range(n))
    
    # Vi loopar uppåt tills x^k passerar target_value för att hitta den exakta matematiska gränsen
    max_k = n
    while float(x_numeric**max_k) <= target_value:
        max_k += 1
    
    # Vi lägger till en liten marginal (t.ex. +2) för säkerhets skull vid avrundningar, 
    # men sätter ett golv på minst n+5 så små ekvationer inte stryps för tidigt.
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
                
                # Här tillämpar vi din regel strängt under själva sökningen:
                # Om kombinationen innehåller en potens som är större än vår geometriska maxgräns, utesluter vi den.
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
    """ 
    En stabil, numerisk ersättare till den gamla layout-loopen.
    Matchar permutationer mot en global databas av existerande centrum.
    """
    optimized_layouts = []
    global_drawn_centers = set() # Sparar par av (potens, avrundat_centrum)
    
    for idx, combo_keys in enumerate(sorted_matches):
        if idx == 0:
            # Huvudleden sätter baslinjen
            optimized_layouts.append(combo_keys)
            centers = get_layer_geometry_numeric(combo_keys, x_numeric)
            for k, x_center, _ in centers:
                global_drawn_centers.add((k, round(x_center, 5)))
            continue
            
        best_score = -1
        best_layout = tuple(sorted(list(combo_keys)))
        
        # Testa permutationer för att hitta var vi återanvänder flest cirklar
        for perm in itertools.permutations(combo_keys):
            centers = get_layer_geometry_numeric(perm, x_numeric)
            score = 0
            for k, x_center, _ in centers:
                if (k, round(x_center, 5)) in global_drawn_centers:
                    score += 5  # Hög poäng för perfekt överlappning av exakt samma cirkel
            
            if score > best_score:
                best_score = score
                best_layout = perm
                
        optimized_layouts.append(best_layout)
        # Uppdatera den globala poolen med cirklarna från den valda layouten
        final_centers = get_layer_geometry_numeric(best_layout, x_numeric)
        for k, x_center, _ in final_centers:
            global_drawn_centers.add((k, round(x_center, 5)))
            
    return optimized_layouts

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
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

    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key="circles_overlap")
        
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
        height=100,
        line_color, bg_color = "#000000", "#FFFFFF"
        fig = go.Figure()
        x_lines, y_lines = [], []
        theta_upper = np.linspace(0, np.pi, 40)

        # Rita den markerade kombinationen (Tjock linje)
        if 0 <= selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            chosen_centers = get_layer_geometry_numeric(chosen_combo, x_numeric)
            for k, x_center, diameter in chosen_centers:
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

        # Rita alla unika cirklar i bakgrunden (Tunna linjer)
        all_radii = []
        drawn_circles = set()
        for combo in final_layouts:
            centers = get_layer_geometry_numeric(combo, x_numeric)
            for k, x_center, diameter in centers:
                radius = diameter / 2.0
                all_radii.append(radius)
                
                circle_id = (k, round(x_center, 5))
                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_lines.extend(list(cx) + [None])
                    y_lines.extend(list(cy) + [None])

        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, 
            mode="lines", 
            line=dict(color=line_color, width=0.4), 
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
