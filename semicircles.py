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

def extract_rules_from_poly(minimal_poly, max_power=15):
    """ Skapar exakta omskrivningsregler utifrån minimalpolynomet """
    if minimal_poly is None:
        return []
        
    x = sp.Symbol("x")
    P_x = sp.expand(minimal_poly)
    rules = []
    
    for p in range(max_power):
        shifted_poly = sp.expand(P_x * x**p)
        terms = {}
        for t in sp.Add.make_args(shifted_poly):
            c, sub_target = t.as_coeff_mul(x)
            
            if sub_target and isinstance(sub_target, sp.Pow):
                pow_val = int(sub_target.exp)
            elif sub_target and sub_target == x:
                pow_val = 1
            else:
                pow_val = 0
            terms[pow_val] = int(c)
            
        if not terms:
            continue
            
        highest_pow = max(terms.keys())
        highest_coeff = terms[highest_pow]
        from_pows = []
        valid_rule = True
        
        for pow_val, coeff in terms.items():
            if pow_val == highest_pow:
                continue
            if (coeff > 0 and highest_coeff > 0) or (coeff < 0 and highest_coeff < 0):
                valid_rule = False
                break
            for _ in range(abs(coeff)):
                from_pows.append(pow_val)
                
        if valid_rule and from_pows:
            rules.append((tuple(sorted(from_pows)), highest_pow))
            
    return list(set(rules))

def find_math_structures_logical(n, minimal_poly):
    """ Din stabila original-sökning som garanterat hittar ALLA kombinationer """
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

def optimize_single_layout_by_rewriting(combo_keys, rules, n):
    """ 
    Tar en osorterad kombination och hittar den permutation som bäst 
    matchar stegen från omskrivningsreglerna (t.ex. flyttar 3 först, sen 2).
    """
    combo_set = set(combo_keys)
    best_score = -1
    best_permutation = tuple(sorted(list(combo_keys)))
    
    # Eftersom kombinationerna oftast är korta (få element) är en kontrollerad
    # permutations-poängsättning baserad på regler extremt snabb och exakt.
    for perm in itertools.permutations(combo_keys):
        score = 0
        current_list = list(perm)
        
        # Kolla om ordningen matchar våra kända algebraiska skift
        for r_from, r_to in rules:
            # Om regeln (t.ex. 0,1 -> 3) tillämpas, vill vi att elementen 
            # som ersätts eller skapas behåller den ordning vi förväntar oss
            if r_to in current_list:
                idx = current_list.index(r_to)
                # Premierar om potenser som hör ihop hamnar i logisk följd
                if idx > 0 and current_list[idx-1] in r_from:
                    score += 2
                if idx < len(current_list) - 1 and current_list[idx+1] in r_from:
                    score += 2
                    
        # Extra poäng om vi lyckas hålla element som fanns i huvudleden i stigande ordning
        for i in range(len(current_list) - 1):
            if current_list[i] < n and current_list[i+1] < n:
                if current_list[i] < current_list[i+1]:
                    score += 1
                    
        if score > best_score:
            best_score = score
            best_permutation = perm
            
    return best_permutation

def get_layer_geometry_numeric(combo, x_numeric):
    centers = []
    current_x = 0.0
    for k in combo:
        diameter = float(x_numeric**k)
        radius = diameter / 2.0
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return centers

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    x_numeric = math_data["x_numeric"]
    
    # 1. Hitta alla kombinationer med din säkra originalmetod
    raw_matches = find_math_structures_logical(n, minimal_poly)

    if not raw_matches:
        st.info("The main line is missing from the data.")
        return

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # 2. Hämta algebraiska regler för att styra ordningen
    rules = extract_rules_from_poly(minimal_poly, max_power=max(15, n + 5))

    target_value = sum(float(x_numeric**m) for m in range(n))
    if target_value == 0: target_value = 1.0

    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key="circles_overlap")
        
        # Om overlap är aktivt, ordna varje rad optimalt utifrån reglerna
        if max_overlap:
            final_layouts = []
            for combo in sorted_matches:
                if combo == main_line:
                    final_layouts.append(list(main_line))
                else:
                    optimized = optimize_single_layout_by_rewriting(combo, rules, n)
                    final_layouts.append(list(optimized))
        else:
            final_layouts = [list(combo) for combo in sorted_matches]

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

        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
