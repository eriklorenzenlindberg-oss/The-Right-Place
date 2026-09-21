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


# --- DETERMINISTISK GEOMETRISK MÅLSÖKARE ---
def evaluate_global_layout(main_order, total_sum_matches, pool):
    """
    Placerar cirklarna deterministiskt genom att matcha dolda skarvar 
    mot huvudledens kända koordinater. Garanterar O(n^2) komplexitet.
    """
    # 1. Kartlägg huvudledens exakta geometriska startpunkter (vårt facit)
    main_starts, _ = get_layer_geometry(main_order, pool)
    main_positions = set(main_starts.values())
    
    current_layout = [main_order]
    
    # 2. Rikta in varje dolt led linjärt utifrån facit
    for idx, combo in enumerate(total_sum_matches):
        if idx == 0:
            continue
            
        remaining_elements = list(combo)
        aligned_combo = []
        current_x = 0.0
        
        while remaining_elements:
            best_element = remaining_elements[0]
            min_distance = float('inf')
            
            # Hitta det element som lägger sin startpunkt närmast en existerande skarv i huvudleden
            for elem in remaining_elements:
                # Beräkna potentiellt fel/avstånd till närmaste skarv
                distances = [abs(current_x - pos) for pos in main_positions]
                current_min = min(distances) if distances else 0.0
                
                # Om elementet dessutom har ett strukturellt släktskap, ge det prioritet
                if elem in main_starts and round(current_x, 4) == main_starts[elem]:
                    current_min -= 10.0  # Matematisk bonus för perfekt passform
                
                if current_min < min_distance:
                    min_distance = current_min
                    best_element = elem
            
            # Registrera elementet och stega framåt längs baslinjen
            aligned_combo.append(best_element)
            remaining_elements.remove(best_element)
            if best_element in pool:
                current_x += pool[best_element]
                
        current_layout.append(tuple(aligned_combo))
        
    return current_layout


# --------------------------------------------------
# RENDER (Självständig modul med inbyggda kontroller)
# --------------------------------------------------

def render(math_data):
    total_sum_matches = math_data.get("total_sum_matches", [])
    if not total_sum_matches or len(total_sum_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    # Breddförhållande för kolumnerna (60% / 30%)
    col_plot, col_controls = st.columns([6, 3])
    
    with col_controls:
        max_overlap = False
        if len(total_sum_matches) > 1:
            max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")
        
        combo_labels = []
        for combo in total_sum_matches:
            label = " + ".join(get_math_label(k) for k in sorted(combo))
            combo_labels.append(label)
            
        combo_options = ["None"] + combo_labels
        
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_options,
            index=0,
            key="circles_highlight"
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

        # Huvudleden (index 0) sorteras strikt i sin naturliga grundordning
        main_base_order = tuple(sorted(total_sum_matches[0]))

        if not max_overlap or len(total_sum_matches) <= 1:
            final_layouts = [tuple(sorted(combo)) for combo in total_sum_matches]
        else:
            # Anropar den nya geometriska målsökaren
            final_layouts = evaluate_global_layout(main_base_order, total_sum_matches, pool)

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
