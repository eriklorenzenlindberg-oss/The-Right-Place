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
    STABIL GRUND: Beräknar geometri baserat på en färdig lista med diametrar.
    Detta gör att ändringen till (1 + v) på index 0 slår igenom helt naturligt.
    """
    centers = []
    current_x = 0.0
    for k in combo:
        # Hämta diametern direkt från listan baserat på potensen k
        if k < len(lengths_numeric):
            diameter = float(lengths_numeric[k])
        else:
            diameter = 1.0 # Säker fallback
            
        radius = diameter / 2.0
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return centers


def draw_one_vertical_plot(fig, final_layouts, lengths_numeric, x_offset, selected_idx, line_color):
    """
    STABIL GRUND: Ritar ett enskilt vertikalt diagram.
    Genom att skicka in 'fig' och 'x_offset' kan vi placera hur många 
    diagram vi vill bredvid varandra utan att de krockar eller staplas på mobilen.
    """
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

    # Beräkna baslinjens totala längd utifrån den första kombinationen
    first_combo_centers = get_layer_geometry_from_list(final_layouts[0], lengths_numeric) if final_layouts else []
    target_value = sum(d for _, _, d in first_combo_centers) if first_combo_centers else 1.0

    # Lägg till baslinjen för detta diagram
    x_background.extend([x_offset, x_offset, None])
    y_background.extend([0.0, target_value, None])

    # Lägg till bakgrundslagret i figuren
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
    
    # Hämta de färdiga listorna direkt från calculations.py
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

    # Kontrollpanelen till höger
    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=True, key="circles_overlap")
        
        if max_overlap:
            # Vi optimerar layouterna separat utifrån respektive diagram-längder
            final_layouts1 = evaluate_global_layout_numeric_v2(sorted_matches, lengths1_numeric)
            final_layouts2 = evaluate_global_layout_numeric_v2(sorted_matches, lengths2_numeric)
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
        # Placeras vid x_offset = 0.0
        target_val1 = draw_one_vertical_plot(fig, final_layouts1, lengths1_numeric, 0.0, selected_idx, line_color)
        
        # --- RITA DIAGRAM 2: MODIFIERAD 1 + v (HÖGER) ---
        # Vi sätter ett dynamiskt mellanrum baserat på hur mycket det första diagrammet bygger utåt
        max_rad1 = max((d/2.0) for _, _, d in get_layer_geometry_from_list(final_layouts1[0], lengths1_numeric))
        gap = max_rad1 * 0.8
        fig2_x_offset = -(max_rad1 * 2.0 + gap)
        
        target_val2 = draw_one_vertical_plot(fig, final_layouts2, lengths2_numeric, fig2_x_offset, selected_idx, line_color)

        # --- EXAKT 1:1 SKALNING FÖR HELA BILDEN ---
        max_rad2 = max((d/2.0) for _, _, d in get_layer_geometry_from_list(final_layouts2[0], lengths2_numeric))
        
        # Y-axeln (höjden) anpassas efter det längsta diagrammet
        max_target = max(target_val1, target_val2)
        y_min = -max_target * 0.05
        y_max = max_target + (max_target * 0.05)

        # X-axeln sträcker sig över båda diagrammens bredd och mellanrummet
        x_min = fig2_x_offset - (max_rad2 * 1.1)
        x_max = max_rad1 * 0.1

        # Tvinga kvadratiska proportioner utan stretch
        y_span = y_max - y_min
        x_span = x_max - x_min
        if y_span > x_span:
            diff = (y_span - x_span) / 2.0
            x_min -= diff
            x_max += diff
        else:
            diff = (x_span - y_span) / 2.0
            y_min -= diff
            y_max += diff

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=450, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(fig, use_container_width=True, key=f"semicircles_combined_{n}")

    # Göm verktygsraden
    st.markdown("<style>.modebar { display: none !important; }</style>", unsafe_allow_html=True)
