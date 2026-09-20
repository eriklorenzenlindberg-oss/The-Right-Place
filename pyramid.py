import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# --------------------------------------------------
# ISOMETRISKA AXLAR
# --------------------------------------------------
import math

# --------------------------------------------------
# SANN ISOMETRISKA AXLAR (120 grader mellan alla axlar)
# --------------------------------------------------
# Z pekar rakt upp (eller rakt ner beroende på preferens, här behålls riktningen)
# Med Z rakt upp/ner blir X och Y snett uppåt/åt sidorna för 120° separation.
VX = (-math.cos(math.radians(30)), math.sin(math.radians(30)))  # ca (-0.866, 0.5)
VY = (math.cos(math.radians(30)), math.sin(math.radians(30)))   # ca (0.866, 0.5)
VZ = (0.0, -1.0)                                                # Rakt ner



def iso_point(px, py, pz):
    return (
        px * VX[0] + py * VY[0] + pz * VZ[0],
        px * VX[1] + py * VY[1] + pz * VZ[1]
    )


# --------------------------------------------------
# HJÄLP (Anpassad för att hantera rader/kolumner i subplots)
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
            line=dict(color=line_color, width=1),
            hoverinfo="skip", showlegend=False
        ),
        row=row, col=col
    )


# --------------------------------------------------
# GENERELLT BLOCK
# --------------------------------------------------
def draw_block(fig, block_lengths, a, b, z_power, offset_x, offset_y, offset_z, line_color, fill_color, row, col):
    x_size = block_lengths[a]
    y_size = block_lengths[b]
    z_size = block_lengths[z_power]

    # xy-face
    xy = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y + y_size, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z)
    ]
    # yz-face
    yz = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z),
        iso_point(offset_x, offset_y + y_size, offset_z + z_size),
        iso_point(offset_x, offset_y, offset_z + z_size)
    ]
    # xz-face
    xz = [
        iso_point(offset_x, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z),
        iso_point(offset_x + x_size, offset_y, offset_z + z_size),
        iso_point(offset_x, offset_y, offset_z + z_size)
    ]

    add_face(fig, xy, line_color, fill_color, row, col)
    add_face(fig, yz, line_color, fill_color, row, col)
    add_face(fig, xz, line_color, fill_color, row, col)


# --------------------------------------------------
# RENDER
# --------------------------------------------------
def render(math_data, z_gap, x_gap):
    n = math_data["n"]
    numeric_powers = math_data["numeric_powers"]
    lengths2 = math_data["lengths2_numeric"]

    line_color = st.get_option("theme.primaryColor") or "#FFFFFF"
    bg_color = st.get_option("theme.backgroundColor") or "#0041BA"

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Figur 2 Inställningar:**")
    rotate = st.sidebar.checkbox("Rotate (Mått: $x$ till $1+v$)", value=False)

    v_modified_value = lengths2[0]

    # Skapa två deldiagram bredvid varandra
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=("Standard bas (1)", "Modifierad bas (1 + v)"),
        horizontal_spacing=0.05
    )

    # --------------------------------------------------
    # RITA PYRAMID 1 (Vänster kolumn: row=1, col=1)
    # --------------------------------------------------
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(numeric_powers[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(numeric_powers[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(numeric_powers[p] for p in range(a + 1)) - a * x_gap
                draw_block(fig, numeric_powers, a, b, z_power, offset_x, offset_y, offset_z, line_color, "#0041BA", row=1, col=1)

    # --------------------------------------------------
    # GEOMETRISK PLACERING AV FIGUR 2 (Förskjutningslogik)
    # --------------------------------------------------
    # Förbered chosen_lengths för Figur 2
    chosen_lengths = {}
    if rotate:
        for i in range(n + 5):
            if i == n - 1:
                chosen_lengths[i] = v_modified_value
            else:
                chosen_lengths[i] = numeric_powers[i + 1]
        fill_color = "#0041BA"
    else:
        for i in range(n + 5):
            if i == 0:
                chosen_lengths[i] = v_modified_value
            else:
                chosen_lengths[i] = numeric_powers[i]
        fill_color = "#0041BA"

    # --------------------------------------------------
    # FIXPUNKT: Underkanten på det fysiska blocket x^(n-3), x^(n-2), x^(n-1)
    # --------------------------------------------------
    # I Figur 1 (standardbasen) ritas detta block vid dessa loop-index:
    f1_z_power = n - 1
    f1_b = n - 2
    f1_a = n - 3

    # Beräkna 3D-positionen för blocket i Figur 1
    f1_fix_z = sum(numeric_powers[p] for p in range(2, f1_z_power)) + (f1_z_power - 2) * z_gap
    f1_fix_y = -sum(numeric_powers[p] for p in range(1, f1_b + 1))
    f1_fix_x = -sum(numeric_powers[p] for p in range(f1_a + 1)) - f1_a * x_gap
    f1_fix_y_space = iso_point(f1_fix_x, f1_fix_y, f1_fix_z)[1]

    # I Figur 2 (modifierad bas) flyttas det fysiska blocket beroende på rotationen:
    if not rotate:
        # Om inte roterad är det samma index som i Figur 1
        f2_z_power = n - 1
        f2_b = n - 2
        f2_a = n - 3
    else:
        # När rotate är aktiv skiftas de matematiska rollerna i din val-logik.
        # Vi måste matcha de index där måtten för x^(n-3), x^(n-2), x^(n-1) faktiskt hamnar i chosen_lengths.
        f2_z_power = n - 2  # Blocket flyttas en nivå ner i z-ledet i strukturen
        f2_b = n - 3
        f2_a = n - 4

    # Säkerställ att indexen inte blir negativa för mycket små pyramider
    f2_z_power = max(2, f2_z_power)
    f2_b = max(1, f2_b)
    f2_a = max(0, f2_a)

    # Beräkna 3D-positionen för samma fysiska block i Figur 2
    f2_fix_z = sum(chosen_lengths[p] for p in range(2, f2_z_power)) + (f2_z_power - 2) * z_gap
    f2_fix_y = -sum(chosen_lengths[p] for p in range(1, f2_b + 1))
    f2_fix_x = -sum(chosen_lengths[p] for p in range(f2_a + 1)) - f2_a * x_gap
    f2_fix_y_space = iso_point(f2_fix_x, f2_fix_y, f2_fix_z)[1]

    # Justera Figur 2 så att detta specifika blocks underkant matchar exakt i höjdled
    dx = 0.0
    dy = f1_fix_y_space - f2_fix_y_space






    # --------------------------------------------------
    # RITA PYRAMID 2 (Höger kolumn: row=1, col=2)
    # --------------------------------------------------
    for z_power in range(n - 1, 1, -1):
        offset_z = sum(chosen_lengths[p] for p in range(2, z_power)) + (z_power - 2) * z_gap
        for b in range(1, z_power):
            offset_y = -sum(chosen_lengths[p] for p in range(1, b + 1))
            for a in range(0, b):
                offset_x = -sum(chosen_lengths[p] for p in range(a + 1)) - a * x_gap
                
                # Här applicerar vi dx och dy direkt på de isometriska 2D-koordinaterna
                # Genom att modifiera draw_block-logiken lokalt skapar vi ett eget anrop eller justerar ytorna:
                x_size = chosen_lengths[a]
                y_size = chosen_lengths[b]
                z_size = chosen_lengths[z_power]

                # Generera hörn och lägg till den globala förskjutningen (dx, dy) i bildrummet
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

                add_face(fig, xy, line_color, fill_color, row=1, col=2)
                add_face(fig, yz, line_color, fill_color, row=1, col=2)
                add_face(fig, xz, line_color, fill_color, row=1, col=2)
    
    # --------------------------------------------------
    # FASTA RAMAR OCH SKALA (Gör att Figur 1 står helt still)
    # --------------------------------------------------
    # Vi beräknar en rimlig marginal baserat på storleken på Figur 1.
    # Vi kollar ungefär hur bred/hög pyramid 1 blir i bildkoordinater.
    max_span = sum(numeric_powers[p] for p in range(1, n)) * 1.5
    
    # Sätt en fast, generös ram runt origo i bildrummet
    # Detta förhindrar att Plotly hoppar eller autoskalar om när Figur 2 ändras.
    fixed_range_x = [-max_span, max_span / 2]
    fixed_range_y = [-max_span, max_span / 2]

    fig.update_layout(
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        
        # Kolumn 1 får en låst ram och låst aspektförhållande (1:1)
        xaxis=dict(visible=False, range=fixed_range_x),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=fixed_range_y),
        
        # Kolumn 2 delar exakt samma skala och ram, vilket gör att de matchar 100%
        xaxis2=dict(visible=False, range=fixed_range_x),
        yaxis2=dict(visible=False, scaleanchor="x2", scaleratio=1, range=fixed_range_y)
    )

    st.plotly_chart(fig, use_container_width=True)
