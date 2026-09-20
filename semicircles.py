import itertools
import numpy as np
import plotly.graph_objects as go
import streamlit as st

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

def evaluate_global_layout(main_order, total_sum_matches, pool):
    main_starts, _ = get_layer_geometry(main_order, pool)
    current_layout = [main_order]
    total_score = 0
    
    for idx, combo in enumerate(total_sum_matches):
        if idx == 0:
            continue
            
        base_order = tuple(sorted(combo))
        best_dold_order = base_order
        best_dold_score = -1
        
        for perm in itertools.permutations(base_order):
            perm_starts, _ = get_layer_geometry(perm, pool)
            current_score = 0
            for k in perm:
                if k in main_starts and perm_starts[k] == main_starts[k]:
                    current_score += 1
                    
            if current_score > best_dold_score:
                best_dold_score = current_score
                best_dold_order = perm
                
        total_score += best_dold_score
        current_layout.append(best_dold_order)
        
    return total_score, current_layout

def render(math_data):
    total_sum_matches = math_data.get("total_sum_matches", [])
    if not total_sum_matches or len(total_sum_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    # Breddförhållande för kolumnerna (80% / 20%)
    col_plot, col_controls = st.columns([6, 3])
    
    with col_controls:
       
        max_overlap = False
        if len(total_sum_matches) > 1:
            max_overlap = st.checkbox("Overlap", value=False)
        
        
        
        
        combo_labels = []
        for combo in total_sum_matches:
            label = " + ".join(get_math_label(k) for k in sorted(combo))
            combo_labels.append(label)
            
        combo_options = ["None"] + combo_labels
        
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_options,
            index=0,
            label_visibility="collapsed"
        )
        
        selected_idx = combo_options.index(selected_option) - 1

    with col_plot:
        n = math_data["n"]
        pool = math_data["circle_pool"]
        
        target_value = sum(pool[m] for m in range(n) if m in pool)
        if target_value == 0:
            target_value = 1.0
            
        line_color = st.get_option("theme.primaryColor") or "#000000"
        bg_color = st.get_option("theme.backgroundColor") or "#FFFFFF"

        fig = go.Figure()
        x_lines, y_lines = [], []
        x_texts, y_texts, text_labels, text_positions = [], [], [], []
        theta_upper = np.linspace(0, np.pi, 40)

                # --- KORRIGERING: Hämta enbart huvudleden (index 0) och gör om till en tuple ---
        main_base_order = tuple(sorted(total_sum_matches[0]))

        if not max_overlap or len(total_sum_matches) <= 1:
            final_layouts = [tuple(sorted(combo)) for combo in total_sum_matches]
        else:
            best_global_score = -1
            final_layouts = []
            
            # Nu kommer den att tillåta att cirklarna (0, 1, 2) i huvudleden kastas om perfekt!
            for main_perm in itertools.permutations(main_base_order):
                score, layout = evaluate_global_layout(main_perm, total_sum_matches, pool)
                if score > best_global_score:
                    best_global_score = score
                    final_layouts = layout


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
        # Vi sparar alla radier för att ta reda på vilken båge som är absolut högst i just denna layout
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
            line=dict(color=line_color, width=1), 
            hoverinfo="skip", showlegend=False
        ))
        
        if x_texts:
            fig.add_trace(go.Scatter(
                x=x_texts, y=y_texts, text=text_labels, mode="text",
                textposition=text_positions, 
                textfont=dict(color=bg_color, size=11), 
                hoverinfo="skip", showlegend=False
            ))

        # --- DYNAMISK GLOBAL CENTRERING I EN FAST 1:2 RUTA ---
        # Ta reda på den faktiska fysiska maxhöjden i det aktuella diagrammet
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        
        # Vi lägger till en grundmarginal på 10% av bredden för andningsrum
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
        
        # Eftersom bildrutan ska vara exakt 1:2 (t.ex. 800x400) måste den synliga Y-rymden 
        # vara exakt hälften av den synliga X-rymden för att cirklarna ska förbli runda.
        required_y_space = total_graph_width * 0.5
        
        if max_actual_height > (required_y_space * 0.85):
            # FALL 1: Diagrammet är "högt" (en stor dominant cirkel).
            # Vi justerar X-axeln och ökar marginalerna på sidorna så att höjden får plats utan att klippas!
            required_y_space = max_actual_height / 0.80
            total_x_span = required_y_space * 2.0
            extra_x_margin = (total_x_span - target_value) / 2.0
            x_min = -extra_x_margin
            x_max = target_value + extra_x_margin
        else:
            # FALL 2: Diagrammet är "långsmalt" (många små cirklar).
            # Vi behåller standardmarginalen på sidorna.
            x_min = -base_x_margin
            x_max = target_value + base_x_margin
            
        # Beräkna det vertikala fönstret symmetriskt runt diagrammets mittpunkt i höjdled
        # så att baslinjen hamnar perfekt balanserad och aldrig för långt ner på skärmen.
        y_center_point = max_actual_height / 2.0
        y_min = y_center_point - (required_y_space / 2.0)
        y_max = y_center_point + (required_y_space / 2.0)

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=400, # Låser den fysiska rutan till ett rent, fast format på skärmen
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(fig, use_container_width=True, key="semicircles_plot_clean")
