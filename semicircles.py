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
    
    # Generera regler genom att skifta polynomet med x^p
    for p in range(max_power):
        shifted_poly = sp.expand(P_x * x**p)
        terms = {}
        for t in sp.Add.make_args(shifted_poly):
            c, sub_target = t.as_coeff_mul(x)
            
            # Säkrare typkontroll med isinstance i stället för .is_Pow
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


def rewrite_sequence(current_sequence, rule_from, rule_to):
    """ Tillämpar en framåtriktad omskrivning och bevarar relativ ordning """
    seq_list = list(current_sequence)
    temp_from = list(rule_from)
    indices_to_remove = []
    
    for item in temp_from:
        if item in seq_list:
            idx = seq_list.index(item)
            indices_to_remove.append(idx)
            seq_list[idx] = None
        else:
            return None
            
    new_seq = []
    inserted = False
    for idx, item in enumerate(list(current_sequence)):
        if idx in indices_to_remove:
            if not inserted:
                new_seq.append(rule_to)
                inserted = True
        else:
            new_seq.append(item)
    return tuple(new_seq)

def find_math_structures_logical_ordered(n, minimal_poly):
    """ 
    Ersätter den gamla sökningen. Hittar kombinationer och genererar dem 
    direkt som färdigordnade sekvenser baserat på minimalpolynomet.
    """
    if minimal_poly is None:
        return [tuple(range(n))], {tuple(range(n)): tuple(range(n))}
        
    rules = extract_rules_from_poly(minimal_poly, max_power=max(15, n + 5))
    start_node = tuple(range(n))
    
    visited = set([start_node])
    queue = deque([start_node])
    
    # Karta från osorterad matematisk identitet -> optimalt ordnad sekvens
    results = {}
    
    while queue:
        current = queue.popleft()
        identity = tuple(sorted(list(current)))
        if identity not in results:
            results[identity] = current
            
        for r_from, r_to in rules:
            # 1. Framåtriktad regel (Mindre potenser blir en högre)
            activated = rewrite_sequence(current, r_from, r_to)
            if activated and activated not in visited:
                visited.add(activated)
                queue.append(activated)
                
            # 2. Bakåtriktad regel (En högre potens delas upp)
            if r_to in current:
                idx = current.index(r_to)
                activated_back = current[:idx] + r_from + current[idx+1:]
                if activated_back and activated_back not in visited:
                    visited.add(activated_back)
                    queue.append(activated_back)
                    
    # Sortera för Streamlit (Huvudleden först, sen efter storlek)
    main_line = tuple(range(n))
    hidden_lines = sorted([k for k in results.keys() if k != main_line], key=lambda c: (len(c), c))
    sorted_identities = [main_line] + hidden_lines
    
    return sorted_identities, results

def get_layer_geometry_numeric(combo, x_numeric):
    """ Beräknar geometri steg för steg utifrån sekvensens faktiska ordning """
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
    
    # Hämta de sorterade identiteterna samt kartan med de matematiskt ordnade sekvenserna
    sorted_identities, ordered_sequences_map = find_math_structures_logical_ordered(n, minimal_poly)

    if not sorted_identities:
        st.info("The main line is missing from the data.")
        return

    target_value = sum(float(x_numeric**m) for m in range(n))
    if target_value == 0: target_value = 1.0

    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        # Vi behåller kryssrutan för bakåtkompatibilitet i ditt UI, 
        # men logiken använder nu alltid den optimala matematiska ordningen!
        max_overlap = st.checkbox("Overlap", value=True, key="circles_overlap")
        
        # Hämta de faktiska listorna baserat på om användaren valt overlap eller rå sortering
        if max_overlap:
            final_layouts = [ordered_sequences_map[ident] for ident in sorted_identities]
        else:
            final_layouts = [list(ident) for ident in sorted_identities]

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

        # 1. Rita den markerade kombinationen (Tjock linje)
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

        # 2. Rita alla andra linjer i bakgrunden (Tunna linjer)
        all_radii = []
        drawn_circles = set()
        
        for combo in final_layouts:
            centers = get_layer_geometry_numeric(combo, x_numeric)
            for k, x_center, diameter in centers:
                radius = diameter / 2.0
                all_radii.append(radius)
                
                # Unikt ID baseras på storlek och avrundat centrum för rit-poolen
                circle_id = (k, round(x_center, 5))
                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_lines.extend(list(cx) + [None])
                    y_lines.extend(list(cy) + [None])

        # Lägg till baslinjen
        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, 
            mode="lines", 
            line=dict(color=line_color, width=0.4), 
            hoverinfo="skip", 
            showlegend=False
        ))

        # Dynamisk beräkning av grafruta och skalor (Bevarar 1:1)
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
