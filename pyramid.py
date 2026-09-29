import plotly.graph_objects as go
import streamlit as st
import math

# --------------------------------------------------
# SANN ISOMETRISKA AXLAR (120 grader mellan alla axlar)
# --------------------------------------------------
VX = (-math.cos(math.radians(30)), math.sin(math.radians(30)))  # ca (-0.866, 0.5)
VY = (math.cos(math.radians(30)), math.sin(math.radians(30)))   # ca (0.866, 0.5)
VZ = (0.0, -1.0)                                                # Rakt ner

def iso_point(px, py, pz):
    return (
        px * VX[0] + py * VY[0] + pz * VZ[0],
        px * VX[1] + py * VY[1] + pz * VZ[1]
    )

# --------------------------------------------------
# HJÄLP (Rita en solid yta i en gemensam figur)
# --------------------------------------------------
def add_face(fig, corners, line_color, fill_color):
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]

    xs.append(corners[0][0])
    ys.append(corners[0][1])

    fig.add_trace(
        go.Scatter(
            x=xs, y=ys,
            mode="lines",
            fill="toself",
            fillcolor=fill_color,
            line=dict(color=line_color, width=0.6),
            hoverinfo="skip", showlegend=False
        )
    )

# --------------------------------------------------
# GENERELLT BLOCK (Rita solida rätblock och spara koordinater)
# --------------------------------------------------
def draw_block(fig, block_lengths, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, all_coords, dx=0.0, dy=0.0):
    x_size = block_lengths[a]
    y_size = block_lengths[b]
    z_size = block_lengths[z_power]

    xy = [
        (p[0] + dx, p[1] + dy) for p in [
            iso_point(offset_x, offset_y, offset_z),
            iso_point(offset_x + x_size, offset_y, offset_z),
            iso_point(offset_x + x_size, offset_y + y_size, offset_z),
            iso_point(offset_x, offset_y + y_size, offset_z)
        ]
    ]
    yz = [
        (p[0] + dx, p[1] + dy) for p in [
            iso_point(offset_x, offset_y, offset_z),
            iso_point(offset_x, offset_y + y_size, offset_z),
            iso_point(offset_x, offset_y + y_size, offset_z + z_size),
            iso_point(offset_x, offset_y, offset_z + z_size)
        ]
    ]
    xz = [
        (p[0] + dx, p[1] + dy) for p in [
            iso_point(offset_x, offset_y, offset_z),
            iso_point(offset_x + x_size, offset_y, offset_z),
            iso_point(offset_x + x_size, offset_y, offset_z + z_size),
            iso_point(offset_x, offset_y, offset_z + z_size)
        ]
    ]

    add_face(fig, xy, line_color, fill_color)
    add_face(fig, yz, line_color, fill_color)
    add_face(fig, xz, line_color, fill_color)
    
    # Spara alla hörn i vår lista för att kunna räkna ut bildrutans storlek senare
    all_coords.extend(xy)
    all_coords.extend(yz)
    all_coords.extend(xz)

# --------------------------------------------------
# RENDER
# --------------------------------------------------
def render(math_data, z_gap=0.0, x_gap=0.0):
    n = math_data["n"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]

    line_color = "#000000"
    fill_color = "#FFFFFF"
    bg_color = "#FFFFFF"

    # En tom lista som samlar alla beräknade punkter i 2D
    all_coords = []

    # 1. LAYOUT MED TVÅ KOLUMNER (80% för diagrammet, 20% för reglage till höger)
    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        rotate = st.checkbox("Rotate", value=False, key="pyramid_rotate")

    # 2. SKAPA EN ENSTAKA GEMENSAM FIGUR FÖR BÅDA PYRAMIDERNA
    fig = go.Figure()

    # RITA PYRAMID 1
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(lengths1[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(lengths1[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(lengths1[p] for p in range(a + 1)) - a * x_gap
                draw_block(fig, lengths1, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, all_coords)

    # 3. BERÄKNA GEOMETRISK PLACERING AV PYRAMID 2
    v_modified_value = lengths2[0]

    chosen_lengths = {}
    if rotate:
        for i in range(n + 5):
            if i == n - 1:
                chosen_lengths[i] = v_modified_value
            else:
                chosen_lengths[i] = lengths1[i + 1] if (i + 1) < len(lengths1) else (math_data["x_numeric"] ** (i + 1))
    else:
        for i in range(n + 5):
            if i < len(lengths2):
                chosen_lengths[i] = lengths2[i]
            else:
                chosen_lengths[i] = math_data["x_numeric"] ** i

    f1_z_power = n - 1
    f1_b = n - 2
    f1_a = n - 3

    f1_fix_z = sum(lengths1[p] for p in range(2, f1_z_power)) + (f1_z_power - 2) * z_gap
    f1_fix_y = -sum(lengths1[p] for p in range(1, f1_b + 1))
    f1_fix_x = -sum(lengths1[p] for p in range(f1_a + 1)) - f1_a * x_gap
    f1_fix_pt = iso_point(f1_fix_x, f1_fix_y, f1_fix_z)

    if not rotate:
        f2_z_power = n - 1
        f2_b = n - 2
        f2_a = n - 3
    else:
        f2_z_power = n - 2  
        f2_b = n - 3
        f2_a = n - 4

    f2_z_power = max(2, f2_z_power)
    f2_b = max(1, f2_b)
    f2_a = max(0, f2_a)

    f2_fix_z = sum(chosen_lengths[p] for p in range(2, f2_z_power)) + (f2_z_power - 2) * z_gap
    f2_fix_y = -sum(chosen_lengths[p] for p in range(1, f2_b + 1))
    f2_fix_x = -sum(chosen_lengths[p] for p in range(f2_a + 1)) - f2_a * x_gap
    f2_fix_pt = iso_point(f2_fix_x, f2_fix_y, f2_fix_z)

    # Dynamiskt mellanrum baserat på Pyramid 1:s bredd
    max_span = sum(lengths1[p] for p in range(1, len(lengths1))) * 1.5
    gap_between_pyramids = max_span * 1.5

    dx = f1_fix_pt[0] - f2_fix_pt[0] + gap_between_pyramids
    dy = f1_fix_pt[1] - f2_fix_pt[1]

    # RITA PYRAMID 2 (i samma fig-objekt)
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(chosen_lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(chosen_lengths[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(chosen_lengths[p] for p in range(a + 1)) - a * x_gap
                draw_block(fig, chosen_lengths, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, all_coords, dx=dx, dy=dy)
    
    # 4. BERÄKNA DYNAMISK BILDRUTA UTIFRÅN ALLA EXISTERANDE KOORDINATER
    if all_coords:
        xs = [p[0] for p in all_coords]
        ys = [p[1] for p in all_coords]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Skapa 5 % marginal (luft) runt det mest extrema hörnen
        span_x = x_max - x_min
        span_y = y_max - y_min
        
        margin_x = span_x * 0.05
        margin_y = span_y * 0.05
        
        fixed_range_x = [x_min - margin_x, x_max + margin_x]
        fixed_range_y = [y_min - margin_y, y_max + margin_y]
    else:
        # Fallback om listan mot förmodan skulle vara tom
        fixed_range_x = [-max_span, max_span / 2 + gap_between_pyramids]
        fixed_range_y = [-max_span, max_span / 2]

    # 5. APPLICERA LAYOUT MED FAST 1:1 SKALA OCH LÅST ZOOM
    fig.update_layout(
        height=290,  
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        showlegend=False,
        dragmode=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=fixed_range_x, fixedrange=True),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=fixed_range_y, fixedrange=True)
    )

    # 6. RENDERAS I EN GEMENSAM BEHÅLLARE UTAN VERKTYGSRAD
    with col_plot:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False}, key="pyramid_combined_plot")
