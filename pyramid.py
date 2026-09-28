import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# HJÄLP (Rita en solid yta)
# --------------------------------------------------
def add_face(fig, corners, line_color, fill_color, row, col):
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
            line=dict(color=line_color, width=1.2),
            hoverinfo="skip", showlegend=False
        ),
        row=row, col=col
    )

# --------------------------------------------------
# GENERELLT BLOCK (Rita solida rätblock)
# --------------------------------------------------
def draw_block(fig, block_lengths, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, row, col, dx=0.0, dy=0.0):
    x_size = block_lengths[a]
    y_size = block_lengths[b]
    z_size = block_lengths[z_power]

    # Beräkna hörn med eventuell förskjutning (dx, dy) inlagd direkt
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

    add_face(fig, xy, line_color, fill_color, row, col)
    add_face(fig, yz, line_color, fill_color, row, col)
    add_face(fig, xz, line_color, fill_color, row, col)

# --------------------------------------------------
# RENDER
# --------------------------------------------------
def render(math_data, z_gap=0.0, x_gap=0.0):
    n = math_data["n"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]

    # Strikt svartvita inställningar
    line_color = "#000000"
    fill_color = "#FFFFFF"
    bg_color = "#FFFFFF"

    # FLYTTAD KNAPP: Ligger nu i huvudfönstret ovanför diagrammet istället för i sidomenyn
    rotate = st.checkbox("Rotate Figure 2 (Align orientation with Figure 1)", value=False)

    v_modified_value = lengths2[0]

    # Skapa två deldiagram bredvid varandra UTAN rubriker
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.05)

    # --------------------------------------------------
    # RITA PYRAMID 1 (Vänster kolumn: row=1, col=1)
    # --------------------------------------------------
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(lengths1[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(lengths1[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(lengths1[p] for p in range(a + 1)) - a * x_gap
                draw_block(fig, lengths1, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, row=1, col=1)

    # --------------------------------------------------
    # GEOMETRISK PLACERING AV FIGUR 2 (Förskjutningslogik)
    # --------------------------------------------------
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

    # FIXPUNKT: Underkanten på det fysiska blocket x^(n-3), x^(n-2), x^(n-1)
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

    dx = f1_fix_pt[0] - f2_fix_pt[0]
    dy = f1_fix_pt[1] - f2_fix_pt[1]

    # --------------------------------------------------
    # RITA PYRAMID 2 (Höger kolumn: row=1, col=2)
    # --------------------------------------------------
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(chosen_lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(chosen_lengths[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(chosen_lengths[p] for p in range(a + 1)) - a * x_gap
                draw_block(fig, chosen_lengths, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, row=1, col=2, dx=dx, dy=dy)
    
    # --------------------------------------------------
    # FASTA RAMAR OCH SKALA (Svartvita inställningar)
    # --------------------------------------------------
    max_span = sum(lengths1[p] for p in range(1, len(lengths1))) * 1.5
    fixed_range_x = [-max_span, max_span / 2]
    fixed_range_y = [-max_span, max_span / 2]

    fig.update_layout(
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=fixed_range_x),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=fixed_range_y),
        xaxis2=dict(visible=False, range=fixed_range_x),
        yaxis2=dict(visible=False, scaleanchor="x2", scaleratio=1, range=fixed_range_y)
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

