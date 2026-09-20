import itertools
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
    Om det är Figur 2 och indexet är 0, märk kanten med '1 + v' istället för '1'.
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
# GEOMETRI OCH HYPERKUB-LOGIK
# --------------------------------------------------

def generate_ncube_graph(n):
    nodes = list(itertools.product([0, 1], repeat=n))
    edges = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if sum(abs(a[k] - b[k]) for k in range(n)) == 1:
                edges.append((a, b))
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


def project_node(node, lengths, directions):
    """
    Projekterar en nod till planet, centrerad runt figurens mittpunkt.
    Dra av 0.5 flyttar hyperkubens centrum till (0,0).
    """
    pos = np.zeros(2)
    for xi, Li, di in zip(node, lengths, directions):
        pos += (xi - 0.5) * Li * di
    return pos


def generate_positions(nodes, lengths, directions):
    return {
        node: project_node(node, lengths, directions)
        for node in nodes
    }


# --------------------------------------------------
# AXELGRÄNSER OCH RAMAR
# --------------------------------------------------

def calculate_bounds(pos1, pos2):
    all_pos = list(pos1.values()) + list(pos2.values())
    xs = [p[0] for p in all_pos]
    ys = [p[1] for p in all_pos]

    # Hitta det maximala avståndet från origo för en perfekt kvadratisk vy
    max_val = max(max(abs(x) for x in xs), max(abs(y) for y in ys))
    margin = max_val * 1.35  # Väl tilltagen marginal för att rymma texterna på utsidan
    
    return -margin, margin, -margin, margin


# --------------------------------------------------
# RENDER (Subplots med Convex Hull-baserad märkning)
# --------------------------------------------------

def render(
    math_data,
    linewidth,
    node_size,
    show_nodes,
    rotate_fig2,
):
    n = math_data["n"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]

    nodes, edges = generate_ncube_graph(n)

    # 1. Beräkna kameragränser baserat på omaroterat utgångsläge
    base_directions = generate_directions(n, offset_deg=0.0)
    pos1_base = generate_positions(nodes, lengths1, base_directions)
    pos2_base = generate_positions(nodes, lengths2, base_directions)
    xmin, xmax, ymin, ymax = calculate_bounds(pos1_base, pos2_base)

    # 2. Beräkna de faktiska positionerna för ritningen
    directions1 = generate_directions(n, offset_deg=0.0)
    
    # Rotera endast om checkboxen är aktiv
    rotation_offset = (-180.0 / n) if rotate_fig2 else 0.0
    directions2 = generate_directions(n, offset_deg=rotation_offset)

    pos1 = generate_positions(nodes, lengths1, directions1)
    pos2 = generate_positions(nodes, lengths2, directions2)

    # Tema-inställningar från Streamlit
    line_color = #000000
    bg_color = #FFFFFF 

    # Skapa figuren med subplots
    fig = make_subplots(
        rows=1, 
        cols=2, 
        shared_yaxes=True, 
        horizontal_spacing=0.05
    )

    # --- PANEL 1: FIGUR 1 (Vänster) ---
    x1_lines, y1_lines = [], []
    for a, b in edges:
        pa, pb = pos1[a], pos1[b]
        x1_lines.extend([pa[0], pb[0], None])
        y1_lines.extend([pa[1], pb[1], None])

    fig.add_trace(
        go.Scatter(
            x=x1_lines, y=y1_lines, mode="lines",
            line=dict(color=line_color, width=linewidth),
            hoverinfo="none"
        ),
        row=1, col=1
    )

    if show_nodes:
        fig.add_trace(
            go.Scatter(
                x=[pos1[node][0] for node in nodes], y=[pos1[node][1] for node in nodes],
                mode="markers", marker=dict(color=line_color, size=node_size),
                hoverinfo="none"
            ),
            row=1, col=1
        )

    # --- PANEL 2: FIGUR 2 (Höger) ---
    x2_lines, y2_lines = [], []
    for a, b in edges:
        pa, pb = pos2[a], pos2[b]
        x2_lines.extend([pa[0], pb[0], None])
        y2_lines.extend([pa[1], pb[1], None])

    fig.add_trace(
        go.Scatter(
            x=x2_lines, y=y2_lines, mode="lines",
            line=dict(color=line_color, width=linewidth),
            hoverinfo="none"
        ),
        row=1, col=2
    )

    if show_nodes:
        fig.add_trace(
            go.Scatter(
                x=[pos2[node][0] for node in nodes], y=[pos2[node][1] for node in nodes],
                mode="markers", marker=dict(color=line_color, size=node_size),
                hoverinfo="none"
            ),
            row=1, col=2
        )

    # --- FUNKTION FÖR ANNOTATIONER VIA CONVEX HULL ---
    def add_contour_annotations(positions, col_idx):
        # Extrahera alla 2D-punkter till en numpy-matris för ConvexHull
        node_list = list(positions.keys())
        points = np.array([positions[node] for node in node_list])
        
        try:
            # Beräkna det konvexa höljet (silhuetten) runt alla punkter
            hull = ConvexHull(points)
            
            # Identifiera de yttre linjesegmenten
            hull_edges = set()
            for simplex in hull.simplices:
                node_a = node_list[simplex[0]]
                node_b = node_list[simplex[1]]
                hull_edges.add(tuple(sorted([node_a, node_b])))
        except Exception:
            return

        # Samla giltiga ytterkanter som existerar i vår hyperkubs-graf
        outer_edge_data = []
        for a, b in edges:
            edge_key = tuple(sorted([a, b]))
            if edge_key in hull_edges:
                # Identifiera dimensionen (k)
                dim_k = -1
                for k in range(n):
                    if a[k] != b[k]:
                        dim_k = k
                        break
                
                pa, pb = positions[a], positions[b]
                midpoint = (pa + pb) / 2.0
                
                outer_edge_data.append({
                    'dim': dim_k,
                    'pa': pa,
                    'pb': pb,
                    'midpoint': midpoint
                })

        # Annotera exakt en ytterkant per dimension
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
                # Vinkelrät normalvektor utåt
                T = edge_vector / edge_len
                N = np.array([-T[1], T[0]])
                
                # Eftersom figuren är centrerad runt (0,0) pekar vi bort från origo
                if np.dot(midpoint, N) < 0:
                    N = -N
                
                # Applicera offset på 0.5 vinkelrätt utåt
                anno_pos = midpoint + N * 0.5
                
                fig.add_annotation(
                    x=anno_pos[0],
                    y=anno_pos[1],
                    text=format_label(dim_k, is_fig2=is_fig2),  # Skickar med flagga för Figur 2
                    showarrow=False,
                    font=dict(color=line_color, size=10),
                    xref=x_ref_target,
                    yref=y_ref_target
                )
                
                annotated_dimensions.add(dim_k)

    # Kör Convex Hull-märkningen för båda panelerna separat
    add_contour_annotations(pos1, col_idx=1)
    add_contour_annotations(pos2, col_idx=2)

    # --- LAYOUT OCH ABSOLUT AXELLÅSNING ---
    fig.update_layout(
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        
        xaxis=dict(visible=False, range=[xmin, xmax], scaleanchor="y", scaleratio=1),
        xaxis2=dict(visible=False, range=[xmin, xmax], scaleanchor="y2", scaleratio=1),
        
        yaxis=dict(visible=False, range=[ymin, ymax]),
        yaxis2=dict(visible=False, range=[ymin, ymax])
    )

    fig.update_xaxes(matches='x')

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="iso_subplots"
    )
