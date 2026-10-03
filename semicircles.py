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
            line=dict(color=line_color, width=0.7), 
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

        # NYTT: Detta CSS-hack tvingar webbläsaren att dölja hela verktygsraden
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
