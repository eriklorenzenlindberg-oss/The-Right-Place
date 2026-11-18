import math

import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------
# SANN ISOMETRISKA AXLAR (120 grader mellan alla axlar)
# --------------------------------------------------
VX = (-math.cos(math.radians(30)), math.sin(math.radians(30)))  # ca (-0.866, 0.5)
VY = (math.cos(math.radians(30)), math.sin(math.radians(30)))   # ca (0.866, 0.5)
VZ = (0.0, -1.0)                                                # Rakt ner

LINE_COLOR = "#FFFFFF"
FILL_COLOR = "#0041BA"
SHADE_COLOR = "#003699"
BG_COLOR = "#0041BA"


def iso_point(px, py, pz):
    return (
        px * VX[0] + py * VY[0] + pz * VZ[0],
        px * VX[1] + py * VY[1] + pz * VZ[1]
    )


# --------------------------------------------------
# GEOMETRI (ritas senare; här räknas bara hörnen ut)
# --------------------------------------------------
def block_faces(lengths, a, b, z_power, offset_x, offset_y, offset_z):
    """De tre synliga ytorna i ett rätblock, som (hörn, fyllnadsfärg)."""
    x_size = lengths[a]
    y_size = lengths[b]
    z_size = lengths[z_power]

    xy = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y + y_size, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z),
    ]
    yz = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z + z_size),
        iso_point(offset_x, offset_y, offset_z + z_size),
    ]
    xz = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z + z_size),
        iso_point(offset_x, offset_y, offset_z + z_size),
    ]
    return [(xy, FILL_COLOR), (yz, SHADE_COLOR), (xz, FILL_COLOR)]


def pyramid_faces(n, lengths, z_gap, x_gap, dx=0.0, dy=0.0):
    """Alla ytor i pyramiden i ritordning (bakre först), förskjutna med (dx, dy)."""
    faces = []
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(lengths[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(lengths[p] for p in range(a + 1)) - a * x_gap
                for corners, fill in block_faces(
                    lengths, a, b, z_power, offset_x, offset_y, offset_z
                ):
                    faces.append(([(px + dx, py + dy) for px, py in corners], fill))
    return faces


def fix_point(lengths, z_power, b, a, z_gap, x_gap):
    """Hörnpunkt som pyramiderna linjeras upp efter (i höjdled)."""
    fz = sum(lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
    fy = -sum(lengths[p] for p in range(1, b + 1))
    fx = -sum(lengths[p] for p in range(a + 1)) - a * x_gap
    return iso_point(fx, fy, fz)


def bounding_box(faces):
    xs = [p[0] for corners, _ in faces for p in corners]
    ys = [p[1] for corners, _ in faces for p in corners]
    return min(xs), max(xs), min(ys), max(ys)


def face_xy(corners):
    xs = [p[0] for p in corners] + [corners[0][0]]
    ys = [p[1] for p in corners] + [corners[0][1]]
    return xs, ys


# --------------------------------------------------
# RENDER
# --------------------------------------------------
def render(math_data, z_gap=0.0, x_gap=0.0):
    n = math_data["n"]
    if n < 3:
        st.info("3-faces need at least n = 3 dimensions.")
        return

    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]
    x_numeric = math_data["x_numeric"]

    # 1. LAYOUT MED TVÅ KOLUMNER (80% för diagrammet, 20% för reglage till höger)
    col_plot, col_controls = st.columns([8, 2])

    with col_controls:
        rotate = st.checkbox("Rearrange fig. 2", value=False, key="pyramid_rotate")

    # 2. LÄNGDER FÖR FIGUR 2 (med och utan omordning)
    def lengths_for_fig2(rearranged):
        chosen = {}
        for i in range(n + 5):
            if rearranged:
                if i == n - 1:
                    chosen[i] = lengths2[0]
                else:
                    chosen[i] = lengths1[i + 1] if (i + 1) < len(lengths1) else x_numeric ** (i + 1)
            else:
                chosen[i] = lengths2[i] if i < len(lengths2) else x_numeric ** i
        return chosen

    # 3. FIGUR 1 OCH FIGUR 2. Figur 2 flyttas så att ett hörn (som tillhör ett block utan
    #    bredden 1 + v) hamnar på samma ställe i förhållande till figur 1 oavsett om
    #    Rearrange är ibockad. Då ligger alla block utan 1 + v exakt still när man växlar.
    #    Mellanrummet mellan pyramiderna är ett enda gemensamt värde för båda lägena,
    #    så att det inte ändrar något i sidled.
    faces1 = pyramid_faces(n, lengths1, z_gap, x_gap)
    box1 = bounding_box(faces1)
    f1_fix = fix_point(lengths1, n - 1, n - 2, n - 3, z_gap, x_gap)

    variants = {}
    for rearranged in (False, True):
        chosen = lengths_for_fig2(rearranged)
        if not rearranged:
            z, b, a = n - 1, n - 2, n - 3
        else:
            z, b, a = n - 2, n - 3, n - 4
        z, b, a = max(2, z), max(1, b), max(0, a)
        f2_fix = fix_point(chosen, z, b, a, z_gap, x_gap)
        dx_align = f1_fix[0] - f2_fix[0]
        dy = f1_fix[1] - f2_fix[1]
        box0 = bounding_box(pyramid_faces(n, chosen, z_gap, x_gap, dx_align, dy))
        variants[rearranged] = (chosen, dx_align, dy, box0)

    widest = max(
        [box1[1] - box1[0]] + [v[3][1] - v[3][0] for v in variants.values()]
    )
    spacing = 0.1 * widest
    # Gemensamt mellanrum: tillräckligt stort för att ingen av varianterna ska nå figur 1
    gap = max(box1[1] + spacing - v[3][0] for v in variants.values())

    placed = {}
    for rearranged, (chosen, dx_align, dy, _) in variants.items():
        faces = pyramid_faces(n, chosen, z_gap, x_gap, dx_align + gap, dy)
        placed[rearranged] = (faces, bounding_box(faces))

    # 4. AXELGRÄNSER: räknas ut från alla hörn i figur 1 och figur 2 i BÅDA lägena, så att
    #    inget hamnar utanför, och så att figur 1 ligger still när man växlar Rearrange.
    boxes = [box1] + [box for _, box in placed.values()]
    x_min = min(b[0] for b in boxes)
    x_max = max(b[1] for b in boxes)
    y_min = min(b[2] for b in boxes)
    y_max = max(b[3] for b in boxes)
    pad = 0.04 * max(x_max - x_min, y_max - y_min)
    x_range = [x_min - pad, x_max + pad]
    y_range = [y_min - pad, y_max + pad]

    # 5. RITA
    fig = go.Figure()
    for faces in (faces1, placed[rotate][0]):
        for corners, fill in faces:
            xs, ys = face_xy(corners)
            fig.add_trace(
                go.Scatter(
                    x=xs, y=ys,
                    mode="lines",
                    fill="toself",
                    fillcolor=fill,
                    line=dict(color=LINE_COLOR, width=0.8),
                    hoverinfo="skip", showlegend=False
                )
            )

    fig.update_layout(
        height=290,  # Matchar höjden på de andra diagrammen
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        showlegend=False,
        dragmode=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=x_range, fixedrange=True, constrain="domain"),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1,
                   range=y_range, fixedrange=True, constrain="domain"),
    )

    with col_plot:
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': False, 'scrollZoom': False},
                        key="pyramid_combined_plot")
