import plotly.graph_objects as go
import streamlit as st

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"x{''.join(superscripts.get(c, c) for c in str(power))}"

def render(math_data):
    n = math_data["n"]
    
    # EXAKT SAMMA STRUKTUR SOM ISO: Hämtar listorna direkt
    powers = math_data["lengths1_numeric"]  # [x⁰, x¹, x², ..., xⁿ⁻¹]
    lengths2 = math_data["lengths2_numeric"]
    
    # Plockar ut det numeriska v på ett säkert sätt via index 0
    v_num = lengths2[0] - powers[0]
    
    line_color = "#000000"
    bg_color = "#FFFFFF"
    
    # --- NYA INSTÄLLNINGAR FÖR DEN STRECKADE KOLUMNEN ---
    dashed_line_color = "#666666"  # Grå nyans så den upplevs som sekundär
    dashed_line_width = 1.0        # Tunn linje
    dashed_pattern = "4px 4px"     # Förhållande mellan streck och mellanrum (t.ex. "5px 3px")
    
    # --- PANEL-LAYOUT (Exakt som i iso.py) ---
    col_plot, col_controls = st.columns([8, 2])
    
    with col_controls:
        # Sätter en unik nyckel så den inte krockar med iso
        rotate = st.checkbox("Rearrange fig. 2", value=False, key="rectangles_rotate")
    
    with col_plot:
        fig = go.Figure()
        x_lines, y_lines = [], []
        x_texts, y_texts, text_labels, text_positions = [], [], [], []
        
        # Separata listor för de streckade linjerna i Fig 2
        x_dashed, y_dashed = [], []
        
        unit = powers[0]  # Detta är alltid 1.0
        left_col_width = unit + v_num  
        gap = unit * 5.0
        x_max_fig1 = 0.0

        # --------------------------------------------------
        # STRIKT LOOP FÖR BÅDA FIGURERNA
        # --------------------------------------------------
        for fig_idx in range(2):
            x_start = 0.0 if fig_idx == 0 else (x_max_fig1 + gap)
            x_offset = x_start
            y_row_bottom = 0.0

            if fig_idx == 1 and rotate:
                x_label_pos = x_start + left_col_width
            else:
                x_label_pos = x_start
            
            # 1. Höjdannotationer
            for i in range(n - 1):
                p = (n - 1) - i
                if fig_idx == 1 and rotate and p == 1: continue 
                
                x_texts.append(x_label_pos - (unit * 0.3))
                y_texts.append(y_row_bottom + (powers[p]/2))
                text_labels.append(get_math_label(p))
                text_positions.append("middle left")
                
                y_row_bottom += powers[p]

            # 2. Rektanglar och bredd-texter
            for col in range(n - 1):
                # --- NYTT: Generera den streckade kolumnen 1 i Figur 2 ---
                if fig_idx == 1 and col == 0:
                    dash_col_width = unit 
                    
                    # Den streckade kolumnen ritas ALLTID upp vertikalt längst till vänster i Fig 2
                    x_dash_offset = x_start
                    y_dash_offset = 0.0
                    for power in range(n - 1, 0, -1):
                        x0, y0 = x_dash_offset, y_dash_offset
                        x1, y1 = x0 + dash_col_width, y0 + powers[power]
                        x_dashed.extend([x0, x1, x1, x0, x0, None])
                        y_dashed.extend([y0, y0, y1, y1, y0, None])
                        y_dash_offset += powers[power]
                    
                    if rotate:
                        x_offset += left_col_width
                        continue
                    else:
                        width = left_col_width
                else:
                    width = powers[col]

                if not (fig_idx == 1 and rotate):
                    x_texts.append(x_offset + (width/2))
                    y_texts.append(-(unit * 0.3))
                    text_labels.append("1+v" if (fig_idx == 1 and col == 0) else get_math_label(col))
                    text_positions.append("bottom center")

                y_offset = 0.0
                for power in range(n - 1, col, -1):
                    x0, y0 = x_offset, y_offset
                    x1, y1 = x0 + width, y0 + powers[power]
                    x_lines.extend([x0, x1, x1, x0, x0, None])
                    y_lines.extend([y0, y0, y1, y1, y0, None])
                    y_offset += powers[power]
                x_offset += width

            if fig_idx == 0:
                x_max_fig1 = x_offset 

            # 3. Vid rotation
            if fig_idx == 1 and rotate:
                y_bottom = -left_col_width
                
                x_texts.append(x_label_pos - (unit * 0.3))
                y_texts.append(y_bottom + (left_col_width / 2))
                text_labels.append("1+v")
                text_positions.append("middle left")
                
                x_row_offset = x_start + left_col_width
                for col in range(1, n):
                    x0, y0 = x_row_offset, y_bottom
                    x1, y1 = x0 + powers[col], 0
                    x_lines.extend([x0, x1, x1, x0, x0, None])
                    y_lines.extend([y0, y0, y1, y1, y0, None])
                    
                    x_texts.append(x_row_offset + (powers[col]/2))
                    y_texts.append(y_bottom - (unit * 0.3))
                    text_labels.append(get_math_label(col))
                    text_positions.append("bottom center")
                    
                    x_row_offset += powers[col]
                x_offset = max(x_offset, x_row_offset)

        # --------------------------------------------------
        # TRACES & LAYOUT (Matchad höjd och hastighet med iso)
        # --------------------------------------------------
        # Huvudlinjer (Solida)
        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode="lines", line=dict(color=line_color, width=1.0), hoverinfo="skip", showlegend=False))
        
        # --- NYTT: Lägg till den streckade kolumnen som ett eget lager ---
        if x_dashed:
            fig.add_trace(go.Scatter(
                x=x_dashed, y=y_dashed, mode="lines", 
                line=dict(color=dashed_line_color, width=dashed_line_width, dash=dashed_pattern), 
                hoverinfo="skip", showlegend=False
            ))
        
        # Textetiketter
        fig.add_trace(go.Scatter(
            x=x_texts, y=y_texts, text=text_labels, mode="text",
            textposition=text_positions, textfont=dict(color=line_color, size=11),
            hoverinfo="skip", showlegend=False
        ))

        x_start_fig2 = x_max_fig1 + gap
        y_top = sum(powers[p] for p in range(1, n))
        x_right = x_start_fig2 + left_col_width + sum(powers[k] for k in range(1, n))
        span = max(x_right - (-unit * 0.5), y_top - (-left_col_width))
        margin = span * 0.05
        x_min = -unit * 0.5 - margin
        x_max = x_right + margin
        y_min = -left_col_width - margin
        y_max = y_top + margin

        fig.update_layout(
            height=290,  # Samma höjd som iso för visuell symmetri!
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False, 
            margin=dict(l=5, r=5, t=5, b=5),
            dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[y_min, y_max])
        )
        
        # Gömmer verktygsraden precis som i iso.py
        st.markdown(
            """
            <style>
            .modebar { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.plotly_chart(fig, use_container_width=True, key="rectangles_plot_short")
