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

    # PANEL-LAYOUT: En kolumn för det kombinerade diagrammet, en för kontrollerna
    col_plot, col_controls = st.columns([8, 2])

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
        line_color, bg_color = "#FFFFFF", "rgba(0,0,0,0)"
        fig = go.Figure()
        theta_upper = np.linspace(0, np.pi, 40)
        
        # Bestäm avståndet (mellanrummet) mellan diagrammen
        gap = target_value * 0.4
        fig2_offset = target_value + gap

        # Listor för att samla alla bakgrundslinjer
        x_all_background, y_all_background = [], []
        all_radii = []

        # --------------------------------------------------
        # STRIKT LOOP FÖR BÅDA DIAGRAMMEN (fig_idx 0 och 1)
        # --------------------------------------------------
        for fig_idx in range(2):
            # Det andra diagrammet flyttas i koordinatsystemet
            offset = 0.0 if fig_idx == 0 else fig2_offset
            
            # 1. Rita bakgrundslinjer för detta diagram
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
                        
                        # 90-graders rotation: x_ny = -cy, y_ny = cx + offset
                        x_all_background.extend(list(-cy) + [None])
                        y_all_background.extend(list(cx + offset) + [None])

            # Baslinjen för detta diagram
            x_all_background.extend([0.0, 0.0, None])
            y_all_background.extend([offset, offset + target_value, None])

            # 2. Rita den markerade (tjocka) linjen för detta diagram
            if 0 <= selected_idx < len(final_layouts):
                chosen_combo = final_layouts[selected_idx]
                chosen_combo_centers = get_layer_geometry_numeric(chosen_combo, x_numeric)
                for k, x_center, diameter in chosen_combo_centers:
                    radius = diameter / 2.0
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    
                    fig.add_trace(go.Scatter(
                        x=-cy, y=cx + offset, 
                        mode="lines", 
                        line=dict(color=line_color, width=2.5), 
                        hoverinfo="skip", 
                        showlegend=False
                    ))

        # Lägg till alla bakgrundslinjer på en och samma gång
        fig.add_trace(go.Scatter(
            x=x_all_background, y=y_all_background, 
            mode="lines", 
            line=dict(color=line_color, width=0.7), 
            hoverinfo="skip", 
            showlegend=False
        ))

        # --- GEMENSAM SKALNING BASERAD PÅ TOTALA OMFÅNGET ---
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        
        # Totala y-axeln sträcker sig över båda diagrammen plus mellanrummet
        total_y_span = fig2_offset + target_value
        margin_y = total_y_span * 0.05
        y_min = -margin_y
        y_max = total_y_span + margin_y

        # Centrera x-axeln utifrån cirklarnas maximala utskjut
        x_center_point = max_actual_height / 2.0
        required_x_space = (y_max - y_min) * 0.5 
        x_min = -(x_center_point + required_x_space)
        x_max = -(x_center_point - required_x_space)

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=450, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(fig, use_container_width=True, key=f"semicircles_combined_{n}")

    st.markdown(
        """
        <style>
        .modebar { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
