import itertools
import math

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from scipy.spatial import ConvexHull

# --------------------------------------------------
# TEXTFORMATERING FÖR MATEMATISKA TEXTER
# --------------------------------------------------

def format_label(power, is_fig2=False):
    """
    Genererar snygga matematiska strängar med HTML-sup-taggar.
    Om det är Figur 2 och exponenten är 0, märk kanten med '1 + v' istället för '1'.
    """
    if is_fig2 and power == 0:
        return "1 + v"

    if power == 0:
        return "1"
    elif power == 1:
        return "x"
    else:
        return f"x<sup>{power}</sup>"


# --------------------------------------------------
# ORDNING AV SIDORNA (modulo-matematiken)
# --------------------------------------------------
# Riktning k får sidan x^(u*k mod n). Bara steg u som är relativt prima med n
# ger ordningar där figur 2 kan bli identisk med figur 1 (när v = x^n - 1).
# u = 1 är storleksföljden.

def allowed_steps(n):
    """
    Steg u med gcd(u, n) = 1. Steg u och n - u ger spegelbilder av varandra,
    så vi behåller bara den mindre (u <= n/2). För n = 2 är det u = 1.
    """
    return [u for u in range(1, n) if math.gcd(u, n) == 1 and 2 * u <= n]


def side_order(n, u):
    """Exponenten för sidan i varje riktning: [u*k mod n for k in 0..n-1]."""
    return [(u * k) % n for k in range(n)]


def rotation_offset_deg(n, u):
    """
    Vinkel (grader) som figur 2 ska roteras för att bli figur 1 förstorad med x
    när v = x^n - 1. Det är s = -u^(-1) mod n steg om 180/n grader.
    För u = 1 blir det -180/n, precis som tidigare.
    """
    return -pow(u, -1, n) * 180.0 / n


# --------------------------------------------------
# GEOMETRI OCH HYPERKUB-LOGIK
# --------------------------------------------------

@st.cache_data
def generate_ncube_graph(n):
    """Noder och kanter för n-kuben. Varje kant skapas direkt genom att vända en bit."""
    nodes = list(itertools.product([0, 1], repeat=n))
    edges = []
    for node in nodes:
        for k in range(n):
            if node[k] == 0:
                edges.append((node, node[:k] + (1,) + node[k + 1:]))
    return nodes, edges


def generate_directions(n, offset_deg=0.0):
    directions = []
    for k in range(n):
        angle = k * (180.0 / n) + offset_deg
        directions.append(
            np.array([
                np.cos(np.deg2rad(angle)),
                np.sin(np.deg2rad(angle))
            ])
        )
    return directions


def generate_positions(nodes, lengths, directions):
    """
    Projekterar alla noder till planet, centrerat runt figurens mittpunkt
    (att dra av 0.5 flyttar hyperkubens centrum till (0,0)).
    """
    coords = np.array(nodes, dtype=float) - 0.5
    vectors = np.array([L * d for L, d in zip(lengths, directions)])
    points = coords @ vectors
    return {node: points[i] for i, node in enumerate(nodes)}


# --------------------------------------------------
# AXELGRÄNSER OCH RAMAR
# --------------------------------------------------

def calculate_bounds(*position_sets):
    all_pos = [p for positions in position_sets for p in positions.values()]
    xs = [p[0] for p in all_pos]
    ys = [p[1] for p in all_pos]

    # Hitta det maximala avståndet från origo för en perfekt kvadratisk vy
    max_val = max(max(abs(x) for x in xs), max(abs(y) for y in ys))
    margin = max_val * 1.3  # Väl tilltagen marginal för att rymma texterna på utsidan

    return -margin, margin, -margin, margin


# --------------------------------------------------
# RENDER (Subplots med Convex Hull-baserad märkning)
# --------------------------------------------------

def render(math_data):
    n = math_data["n"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]

    # --- AUTOMATISKA DESIGNVAL ---
    # Linjetjockleken blir 0.4 upp till n=7, därefter 0.2
    linewidth = 0.4 if n <= 7 else 0.2
    node_size = linewidth * 7

    # --- PANEL-LAYOUT FÖR DIAGRAM OCH REGLAGE ---
    col_plot, col_controls = st.columns([9, 2])

    with col_controls:
        rotate_fig2 = st.checkbox("Rotate fig. 2", value=False, key="iso_rotate")
        show_nodes = st.checkbox("Nodes", value=False, key="iso_nodes")

        steps = allowed_steps(n)
        if len(steps) > 1:
            def step_label(u):
                return "1 (size order)" if u == 1 else str(u)

            step = st.selectbox(
                "Order of sides (step):",
                options=steps,
                index=0,
                format_func=step_label,
                key=f"iso_step_{n}",
                help=(
                    "Side x^e is placed on direction k when e = step·k mod n. "
                    "Step 1 is size order. Only steps that are coprime with n "
                    "can make fig. 2 identical to fig. 1 when v = x^n − 1; "
                    "Rotate then turns fig. 2 by the angle that matches the step. "
                    "Mirror-image orders are left out."
                ),
            )
        else:
            step = steps[0]

    with col_plot:
        nodes, edges = generate_ncube_graph(n)

        # Exponent för sidan i varje riktning, och motsvarande längder
        order = side_order(n, step)
        sides1 = [lengths1[e] for e in order]
        sides2 = [lengths2[e] for e in order]

        # 1. Positioner: figur 1, figur 2, och figur 2 roterad för valt steg.
        #    Gränserna räknas ut för alla tre, så att figur 1 ligger still
        #    när man slår av eller på "Rotate".
        base_directions = generate_directions(n, offset_deg=0.0)
        rotated_directions = generate_directions(n, offset_deg=rotation_offset_deg(n, step))

        pos1 = generate_positions(nodes, sides1, base_directions)
        pos2_plain = generate_positions(nodes, sides2, base_directions)
        pos2_rotated = generate_positions(nodes, sides2, rotated_directions)
        xmin, xmax, ymin, ymax = calculate_bounds(pos1, pos2_plain, pos2_rotated)

        pos2 = pos2_rotated if rotate_fig2 else pos2_plain

        # Fasta färg-inställningar (Kritvit bakgrund)
        line_color = "#FFFFFF"
        bg_color = "rgba(0,0,0,0)"

        # Skapa figuren med subplots
        fig = make_subplots(
            rows=1,
            cols=2,
            shared_yaxes=True,
            horizontal_spacing=0.05
        )

        # --- PANEL 1: FIGUR 1 (Vänster) och PANEL 2: FIGUR 2 (Höger) ---
        for positions, col in ((pos1, 1), (pos2, 2)):
            x_lines, y_lines = [], []
            for a, b in edges:
                pa, pb = positions[a], positions[b]
                x_lines.extend([pa[0], pb[0], None])
                y_lines.extend([pa[1], pb[1], None])

            fig.add_trace(
                go.Scatter(
                    x=x_lines, y=y_lines, mode="lines",
                    line=dict(color=line_color, width=linewidth),
                    hoverinfo="none"
                ),
                row=1, col=col
            )

            if show_nodes:
                fig.add_trace(
                    go.Scatter(
                        x=[positions[node][0] for node in nodes],
                        y=[positions[node][1] for node in nodes],
                        mode="markers", marker=dict(color=line_color, size=node_size),
                        hoverinfo="none"
                    ),
                    row=1, col=col
                )

        # --- FUNKTION FÖR ANNOTATIONER VIA CONVEX HULL ---
        def add_contour_annotations(positions, col_idx):
            node_list = list(positions.keys())
            points = np.array([positions[node] for node in node_list])

            try:
                hull = ConvexHull(points)
            except Exception:
                return

            hull_nodes = {node_list[i] for i in hull.vertices}
            hull_edges = {
                frozenset((node_list[s[0]], node_list[s[1]])) for s in hull.simplices
            }

            outer_edge_data = []
            for a, b in edges:
                if a not in hull_nodes or b not in hull_nodes:
                    continue
                if frozenset((a, b)) not in hull_edges:
                    continue

                dim_k = -1
                for k in range(n):
                    if a[k] != b[k]:
                        dim_k = k
                        break

                pa, pb = positions[a], positions[b]
                outer_edge_data.append({
                    'dim': dim_k,
                    'pa': pa,
                    'pb': pb,
                    'midpoint': (pa + pb) / 2.0
                })

            annotated_dimensions = set()
            x_ref_target = "x" if col_idx == 1 else "x2"
            y_ref_target = "y"
            is_fig2 = (col_idx == 2)

            for edge in outer_edge_data:
                dim_k = edge['dim']
                if dim_k in annotated_dimensions:
                    continue

                pa, pb = edge['pa'], edge['pb']
                midpoint = edge['midpoint']
                edge_vector = pb - pa
                edge_len = np.linalg.norm(edge_vector)

                if edge_len > 0:
                    T = edge_vector / edge_len
                    N = np.array([-T[1], T[0]])
                    if np.dot(midpoint, N) < 0:
                        N = -N

                    anno_pos = midpoint + N * 0.5

                    # Etiketten visar exponenten på sidan i den riktningen
                    fig.add_annotation(
                        x=anno_pos[0],
                        y=anno_pos[1],
                        text=format_label(order[dim_k], is_fig2=is_fig2),
                        showarrow=False,
                        font=dict(color=line_color, size=10),
                        xref=x_ref_target,
                        yref=y_ref_target
                    )
                    annotated_dimensions.add(dim_k)

        add_contour_annotations(pos1, col_idx=1)
        add_contour_annotations(pos2, col_idx=2)

        # --- LAYOUT OCH ABSOLUT AXELLÅSNING ---
        fig.update_layout(
            height=290,
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            showlegend=False,
            margin=dict(l=5, r=5, t=5, b=5),
            dragmode=False,

            xaxis=dict(visible=False, range=[xmin, xmax], scaleanchor="y", scaleratio=1),
            xaxis2=dict(visible=False, range=[xmin, xmax], scaleanchor="y2", scaleratio=1),

            yaxis=dict(visible=False, range=[ymin, ymax]),
            yaxis2=dict(visible=False, range=[ymin, ymax])
        )

        fig.update_xaxes(matches='x')

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={'displayModeBar': False},
            key="iso_subplots",
        )
