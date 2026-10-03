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
        line_color, bg_color = "#FFFFFF", "rgba(0,0,0,0)"
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
                
                # ROTATION 90 GRADER: x_ny = -cy, y_ny = cx
                fig.add_trace(go.Scatter(
                    x=-cy, y=cx, 
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
                    
                    # ROTATION 90 GRADER: x_ny = -cy, y_ny = cx
                    x_lines.extend(list(-cy) + [None])
                    y_lines.extend(list(cx) + [None])

        # Ursprunglig baslinje: x=[0.0, target_value], y=[0.0, 0.0]
        # Roterad 90 grader: x=[-0.0, -0.0], y=[0.0, target_value]
        x_lines.extend([0.0, 0.0, None])
        y_lines.extend([0.0, target_value, None])

        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, 
            mode="lines", 
            line=dict(color=line_color, width=0.7), 
            hoverinfo="skip", 
            showlegend=False
        ))

        # Geometrisk skalning 1:1 (Anpassad för den roterade layouten)
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

        # CSS-hack tvingar webbläsaren att dölja hela verktygsraden
        st.markdown(
            """
            <style>
            .modebar {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.plotly_chart(fig, use_container_width=True, key="semicircles_plot_clean")
