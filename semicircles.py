import numpy as np
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------
# TEXTFORMATERING FÖR MATEMATISKA TEXTER
# --------------------------------------------------

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    if isinstance(power, float) and not power.is_integer():
        return f"x**{power}"
    
    power_int = int(power)
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    try:
        return f"x{''.join(superscripts.get(c, c) for c in str(power_int))}"
    except Exception:
        return f"x^{power_int}"


# --------------------------------------------------
# GEOMETRI OCH STRUKTURLOGIK
# --------------------------------------------------

def get_layer_geometry(combo, pool):
    starts = {}
    centers = []
    current_x = 0.0
    for k in combo:
        if k not in pool:
            continue
        diameter = pool[k]
        radius = diameter / 2.0
        starts[k] = round(current_x, 4)
        centers.append((k, round(current_x + radius, 4), diameter))
        current_x += diameter
    return starts, centers


# --- MATEMATISK INDEX-MAPPAD OVERLAP-ALGORITM ---
def evaluate_global_layout(main_order, sorted_matches, pool):
    """
    Ordnar alla komplexa kombinationer (även dubbla substitutioner som 4,6) 
    genom att mappa in ersättarna linjärt i huvudledens lediga positioner.
    Garanterar perfekt alignment utan brute force.
    """
    current_layout = []
    main_set = set(main_order)
    
    for combo in sorted_matches:
        combo_set = set(combo)
        
        # 1. Identifiera de gemensamma bas-elementen och de nya ersättarna
        shared_elements = main_set.intersection(combo_set)
        replacements = sorted(list(combo_set - main_set))
        
        aligned_combo = []
        rep_idx = 0
        
        # 2. Stega igenom huvudledens naturliga ordning
        for elem in main_order:
            if elem in shared_elements:
                # Om elementet finns kvar, behåll dess position
                aligned_combo.append(elem)
            else:
                # Om elementet har tagits bort, skjut in nästa tillgängliga ersättare i hålet
                if rep_idx < len(replacements):
                    aligned_combo.append(replacements[rep_idx])
                    rep_idx += 1
                    
        # Säkerhetsventil: Om det finns överblivna ersättare, lägg dem i slutet
        while rep_idx < len(replacements):
            aligned_combo.append(replacements[rep_idx])
            rep_idx += 1
            
        current_layout.append(tuple(aligned_combo))
        
    return current_layout


# --------------------------------------------------
# RENDER (Självständig modul med diagramspecifik sortering)
# --------------------------------------------------

def render(math_data):
    raw_matches = math_data.get("total_sum_matches", [])
    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    # --- DIAGRAMSPECIFIK STRUKTURERING AV DATAN ---
    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # Breddförhållande för kolumnerna
    col_plot, col_controls = st.columns()
    
    with col_controls:
        max_overlap = False
        if len(sorted_matches) > 1:
            max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")
        
        combo_labels = []
        for combo in sorted_matches:
            label = " + ".join(get_math_label(k) for k in combo)
            combo_labels.append(label)
            
        combo_options = ["None"] + combo_labels
        
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_options,
            index=0,
            key=f"circles_highlight_{math_data['n']}"
        )
        
        selected_idx = combo_options.index(selected_option) - 1

    with col_plot:
        n = math_data["n"]
        pool = math_data["circle_pool"]
        
        target_value = sum(pool[m] for m in range(n) if m in pool)
        if target_value == 0:
            target_value = 1.0
            
        line_color = "#000000"
        bg_color = "#FFFFFF"

        fig = go.Figure()
        x_lines, y_lines = [], []
        x_texts, y_texts, text_labels, text_positions = [], [], [], []
        theta_upper = np.linspace(0, np.pi, 40)

        if not max_overlap or len(sorted_matches) <= 1:
            final_layouts = sorted_matches
        else:
            final_layouts = evaluate_global_layout(main_line, sorted_matches, pool)

        # --- STEG 1: SOLID VIT FYLLNING OCH TEXTER ---
        if selected_idx >= 0 and selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            _, chosen_centers = get_layer_geometry(chosen_combo, pool)
            
            for k, x_center, diameter in chosen_centers:
                radius = diameter / 2.0
                cx = x_center + radius * np.cos(theta_upper)
                cy = 0.0 + radius * np.sin(theta_upper)
                
                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="none", fill="toself",
                    fillcolor="rgba(0, 0, 0, 1.0)",
                    hoverinfo="skip", showlegend=False
                ))
                
                x_texts.append(x_center)
                y_texts.append(radius * 0.5)
                text_labels.append(get_math_label(k))
                text_positions.append("middle center")

        # --- STEG 2: RITA ALLA LINJER ---
        all_radii = []
        for combo in final_layouts:
            _, final_centers = get_layer_geometry(combo, pool)
            
            for k, x_center, diameter in final_centers:
                radius = diameter / 2.0
                all_radii.append(radius)
                cx = x_center + radius * np.cos(theta_upper)
                cy = 0.0 + radius * np.sin(theta_upper)
                
                x_lines.extend(list(cx) + [None])
                y_lines.extend(list(cy) + [None])

        # Central horisontell stam
        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, mode="lines", 
            line=dict(color=line_color, width=0.3), 
            hoverinfo="skip", showlegend=False
        ))
        
        if x_texts:
            fig.add_trace(go.Scatter(
                x=x_texts, y=y_texts, text=text_labels, mode="text",
                textposition=text_positions, 
                textfont=dict(color=bg_color, size=11), 
                hoverinfo="skip", showlegend=False
            ))

        # --- DYNAMISK GLOBAL CENTRERING INUTI RAMEN ---
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
        required_y_space = total_graph_width * 0.5
        
        if max_actual_height > (required_y_space * 0.85):
            required_y_space = max_actual_height / 0.80
            total_x_span = required_y_space * 2.0
            extra_x_margin = (total_x_span - target_value) / 2.0
            x_min = -extra_x_margin
            x_max = target_value + extra_x_margin
        else:
            x_min = -base_x_margin
            x_max = target_value + base_x_margin
            
        y_center_point = max_actual_height / 2.0
        y_min = y_center_point - (required_y_space / 2.0)
        y_max = y_center_point + (required_y_space / 2.0)

        # --- LAYOUT OCH ABSOLUT AXELLÅSNING ---
        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=400, 
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(
            fig, 
            use_container_width=True, 
            key="semicircles_plot_clean"
        )
