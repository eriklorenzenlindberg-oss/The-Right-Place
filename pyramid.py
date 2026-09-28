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
# GE KORREKT STRUKTUR FÖR BLOCK (Insamling till single-trace)
# --------------------------------------------------
def collect_block_lines(x_list, y_list, block_lengths, a, b, z_power, offset_x, offset_y, offset_z, dx=0.0, dy=0.0):
    x_size = block_lengths[a]
    y_size = block_lengths[b]
    z_size = block_lengths[z_power]

    # De 8 hörnpunkterna i 3D-rymd för ett block
    p000 = iso_point(offset_x, offset_y, offset_z)
    p100 = iso_point(offset_x + x_size, offset_y, offset_z)
    p110 = iso_point(offset_x + x_size, offset_y + y_size, offset_z)
    p010 = iso_point(offset_x, offset_y + y_size, offset_z)
    
    p001 = iso_point(offset_x, offset_y, offset_z + z_size)
    p101 = iso_point(offset_x + x_size, offset_y, offset_z + z_size)
    p111 = iso_point(offset_x + x_size, offset_y + y_size, offset_z + z_size)
    p011 = iso_point(offset_x, offset_y + y_size, offset_z + z_size)

    # Skapa trådmodell (alla synliga linjer) för att undvika tung fyllningskod
    faces = [
        [p000, p100, p110, p010, p000], # Botten
        [p001, p101, p111, p011, p001], # Toppen
        [p000, p001], [p100, p101], [p110, p111], [p010, p011] # Vertikala pelare
    ]

    for face in faces:
        for p in face:
            x_list.append(p[0] + dx)
            y_list.append(p[1] + dy)
        x_list.append(None)
        y_list.append(None)

# --------------------------------------------------
# RENDER
# --------------------------------------------------
def render(math_data, z_gap=0.0, x_gap=0.0):
    n = math_data["n"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]

    # Sidomenysknappen behålls lokalt i filen
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Figur 2 Inställningar:**")
    rotate = st.sidebar.checkbox("Rotate (Mått: $x$ till $1+v$)", value=False)

    v_modified_value = lengths2[0]

    # Skapa subplots helt UTAN titlar ("") för att fimpas helt
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.05)

    # --------------------------------------------------
    # STRUKTURERA PYRAMID 1 (Samla koordinater blixtsnabbt)
    # --------------------------------------------------
    p1_x, p1_y = [], []
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(lengths1[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(lengths1[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(lengths1[p] for p in range(a + 1)) - a * x_gap
                collect_block_lines(p1_x, p1_y, lengths1, a, b, z_power, offset_x, offset_y, offset_z)

    # Lägg till Pyramid 1 som ETT ENNDA lättviktigt linjespår
    fig.add_trace(
        go.Scatter(
            x=p1_x, y=p1_y, 
            mode="lines", 
            line=dict(color="#000000", width=1.2), 
            connectgaps=False, hoverinfo="skip", showlegend=False
        ),
        row=1, col=1
    )

    # --------------------------------------------------
    # GEOMETRISK PLACERING AV FIGUR 2 (Dina fixpunkter)
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

    f1_z_power = n - 1
    f1_b = n - 2
    f1_a = n - 3

    f1_fix_z = sum(lengths1[p] for p in range(2, f1_z_power)) + (f1_z_power - 2) * z_gap
    f1_fix_y = -sum(lengths1[p] for p in range(1, f1_b + 1))
    f1_fix_x = -sum(lengths1[p] for p in range(f1_a + 1)) - f1_a * x_gap
    f1_fix_y_space = iso_point(f1_fix_x, f1_fix_y, f1_fix_z)[1]

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
    f2_fix_y_space = iso_point(f2_fix_x, f2_fix_y, f2_fix_z)[1]

    dx = 0.0
    dy = f1_fix_y_space - f2_fix_y_space

    # --------------------------------------------------
    # STRUKTURERA PYRAMID 2 (Samla koordinater blixtsnabbt)
    # --------------------------------------------------
    p2_x, p2_y = [], []
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(chosen_lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(chosen_lengths[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(chosen_lengths[p] for p in range(a + 1)) - a * x_gap
                collect_block_lines(p2_x, p2_y, chosen_lengths, a, b, z_power, offset_x, offset_y, offset_z, dx, dy)

    # Lägg till Pyramid 2 som ETT ENDA lättviktigt linjespår
    fig.add_trace(
        go.Scatter(
            x=p2_x, y=p2_y, 
            mode="lines", 
            line=dict(color="#000000", width=1.2), 
            connectgaps=False, hoverinfo="skip", showlegend=False
        ),
        row=1, col=2
    )
    
    # --------------------------------------------------
    # ABSOLUT SVART-VIT LAYOUT (Inga skuggor, inga rubriker)
    # --------------------------------------------------
    max_span = sum(lengths1[p] for p in range(1, len(lengths1))) * 1.5
    fixed_range_x = [-max_span, max_span / 2]
    fixed_range_y = [-max_span, max_span / 2]

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10), # Minimal marginal, inga rubriker tar plats
        xaxis=dict(visible=False, range=fixed_range_x),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=fixed_range_y),
        xaxis2=dict(visible=False, range=fixed_range_x),
        yaxis2=dict(visible=False, scaleanchor="x2", scaleratio=1, range=fixed_range_y)
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
