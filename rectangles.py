import plotly.graph_objects as go
import streamlit as st

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"x{''.join(superscripts.get(c, c) for c in str(power))}"

def render(math_data):
    n, v_num = math_data["n"], math_data["v_numeric"]
    powers = [math_data["numeric_powers"][k] for k in range(len(math_data["numeric_powers"]))]
    
    line_color = st.get_option("theme.primaryColor") or "#FFFFFF"
    
    # KORRIGERING: Här är raden som saknades i mitt förra block!
    bg_color = st.get_option("theme.backgroundColor") or "#0041BA"
    
    rotate = st.checkbox("Rotate", value=False)
    
    fig = go.Figure()
    x_lines, y_lines = [], []
    
    # Listor för att samla ALLA texter till ett enda blixtsnabbt Plotly-spår
    x_texts, y_texts, text_labels, text_positions = [], [], [], []
    
    unit = powers[0]
    left_col_width = unit + v_num  # 1+v: vänsterkolumnen på högra figuren utan rotate
    gap = unit * 5.0
    x_max_fig1 = 0.0

    # --------------------------------------------------
    # STRIKT LOOP FÖR BÅDA FIGURERNA
    # --------------------------------------------------
    for fig_idx in range(2):
        x_start = 0.0 if fig_idx == 0 else (x_max_fig1 + gap)
        x_offset = x_start
        y_row_bottom = 0.0

        # Vid rotate ligger kvarvarande kolumner till höger om 1+v-luckan
        if fig_idx == 1 and rotate:
            x_label_pos = x_start + left_col_width
        else:
            x_label_pos = x_start
        
        # 1. Samla höjdannotationer till vänster om figuren
        for i in range(n - 1):
            p = (n - 1) - i
            if fig_idx == 1 and rotate and p == 1: continue 
            
            x_texts.append(x_label_pos - (unit * 0.3))
            y_texts.append(y_row_bottom + (powers[p]/2))
            text_labels.append(get_math_label(p))
            text_positions.append("middle left")
            
            y_row_bottom += powers[p]

        # 2. Rita rektanglarna i trappan och samla bredd-texter
        for col in range(n - 1):
            if fig_idx == 1 and col == 0:
                if rotate:
                    # Hoppa över 1+v-kolumnen med dess verkliga bredd så övriga kolumner ligger kvar
                    x_offset += left_col_width
                    continue
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

        # 3. Om rotate är aktiv: samla bottenradens rektanglar och texter
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
    # BYGG PLOTLY-GRAFEN (Endast TVÅ traces totalt)
    # --------------------------------------------------
    fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode="lines", line=dict(color=line_color, width=1), hoverinfo="skip", showlegend=False))
    
    fig.add_trace(go.Scatter(
        x=x_texts, y=y_texts, text=text_labels, mode="text",
        textposition=text_positions, textfont=dict(color=line_color, size=12),
        hoverinfo="skip", showlegend=False
    ))

    # Fast kamera för båda rotate-lägena så vänster trappa och högra kolumner inte hoppar
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
        plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False, 
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=[x_min, x_max]),
        yaxis=dict(visible=False, range=[y_min, y_max], scaleanchor="x", scaleratio=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="rectangles_plot_short")
