import itertools
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp
from collections import deque

# --------------------------------------------------
# TEXTFORMATERING FÖR RADIOMENYN
# --------------------------------------------------

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    if isinstance(power, float) and not power.is_integer():
        return f"x**{power}"

    power_int = int(power)
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    try:
        return f"x{''.join(superscripts.get(c, c) for c in str(power_int))}"
    except Exception:
        return f"x^{power_int}"


# --------------------------------------------------
# GEOMETRI OCH STRUKTURLOGIK (Enbart för renderingen)
# --------------------------------------------------

def get_layer_geometry(combo, pool):
    starts = {}
    centers = []
    current_x = 0.0
    for k in combo:
        if k not in pool:
            continue
        diameter = pool[k]
        radius = diameter / 2.0
        starts[k] = round(current_x, 4)
        centers.append((k, round(current_x + radius, 4), diameter))
        current_x += diameter
    return starts, centers


# --- MATEMATISK MATCHNINGS-ALGORITM ---
def evaluate_global_layout(sorted_matches, pool):
    optimized_layouts = []

    for idx, combo_keys in enumerate(sorted_matches):
        best_score = -1000
        best_layout = tuple(sorted(list(combo_keys)))

        for perm in itertools.permutations(combo_keys):
            _, current_centers = get_layer_geometry(perm, pool)
            score = 0

            for k, x_center, _ in current_centers:
                for prev_layout in optimized_layouts:
                    _, prev_centers = get_layer_geometry(prev_layout, pool)
                    for pk, px_center, _ in prev_centers:
                        if pk == k and abs(px_center - x_center) < 1e-4:
                            score += 1

            if score > best_score:
                best_score = score
                best_layout = perm

        optimized_layouts.append(best_layout)

    return optimized_layouts


# --------------------------------------------------
# 100 % EXAKT VEKTORBASERAD SÖKMOTOR (INGA FLYTTAL)
# --------------------------------------------------
def find_math_structures_logical(n, minimal_poly):
    """
    Helt exakt algebraisk sökning via heltalsvektorer.
    Arbetar ENBART med exakta heltal och hoppar över SymPys ordboksbuggar.
    """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    P_x = sp.expand(minimal_poly)
    
    # Bestäm dynamiskt max-potens baserat på n
    MAX_POWER = max(15, n + 6)
    VECTOR_SIZE = MAX_POWER + 1
    
    # 1. Gör om huvudleden till en exakt heltalsvektor (1 för de första n potenserna)
    huvudled_vektor = [0] * VECTOR_SIZE
    for i in range(n):
        if i < VECTOR_SIZE:
            huvudled_vektor[i] = 1
            
    # 2. Översätt de symboliska reglerna (P(x) * x^k) till exakta heltalsvektorer
    regler_vektorer = []
    for k in range(VECTOR_SIZE):
        regel = sp.expand(P_x * x**k)
        vektor = [0] * VECTOR_SIZE
        giltig = True
        
        # Läs av koefficienterna helt exakt
        for p in range(VECTOR_SIZE):
            c = regel.coeff(x, p)
            if c != 0:
                try:
                    vektor[p] = int(c)
                except TypeError:
                    pass
                    
        # Kontrollera om regeln spillde över utanför vår vektorstorlek
        for p in range(VECTOR_SIZE, VECTOR_SIZE + 10):
            if regel.coeff(x, p) != 0:
                giltig = False
                break
                
        if giltig and any(v != 0 for v in vektor):
            regler_vektorer.append(vektor)

    giltiga_kombinationer = set()
    besökta_vektorer = set()
    
    # Kön håller vektorer som tuples (så att de kan hashas i set)
    start_tuple = tuple(huvudled_vektor)
    kö = deque([start_tuple])
    besökta_vektorer.add(start_tuple)
    
    # Lägg till huvudledens index
    giltiga_kombinationer.add(tuple(range(n)))
    
    while kö:
        aktuell_vektor = kö.popleft()
        
        for reg_vek in regler_vektorer:
            for tecken in [1, -1]:
                # Skapa ny heltalskombination via exakt vektoraddition
                ny_vektor = [a + tecken * b for a, b in zip(aktuell_vektor, reg_vek)]
                
                # Snabb-kontroll: Inga negativa koefficienter tillåtna i geometrin
                if any(v < 0 for v in ny_vektor):
                    continue
                    
                ny_tuple = tuple(ny_vektor)
                if ny_tuple in besökta_vektorer:
                    continue
                
                # Kontrollera om vi har hittat en vinnare (bara ettor och nollor)
                # Vi plockar ut de index (potenser) där koefficienten är exakt 1
                potenser = [idx for idx, v in enumerate(ny_vektor) if v == 1]
                
                # Om antalet ettor matchar alla nollställda element (dvs inga tvåor eller treor finns)
                if sum(ny_vektor) == len(potenser) and len(potenser) > 0:
                    giltiga_kombinationer.add(tuple(sorted(potenser)))
                
                # Låt trädet växa om max-koefficienten är 2 (tillfälliga överlapp)
                if max(ny_vektor) <= 2:
                    if len(besökta_vektorer) < 3000:  # Minnesskydd
                        besökta_vektorer.add(ny_tuple)
                        kö.append(ny_tuple)
                        
    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))


# --------------------------------------------------
# RENDER (Minimalistisk, ren och synkroniserad)
# --------------------------------------------------

def render(math_data):
    n = math_data["n"]
    pool = math_data["circle_pool"]
    minimal_poly = math_data["minimal_poly"]
    
    # Kör den exakta vektorbaserade sökningen helt symboliskt utan flyttal
    raw_matches = find_math_structures_logical(n, minimal_poly)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    target_value = sum(pool[m] for m in range(n) if m in pool)
    if target_value == 0:
        target_value = 1.0

    # --- DIAGRAMSPECIFIK STRUKTURERING AV DATAN ---
    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # --- BERÄKNA MATCHADE ORDNINGAR KORREKT ---
    overlap_layouts = evaluate_global_layout(sorted_matches, pool)

    # Breddförhållande för kolumnerna
    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")

        final_layouts = overlap_layouts if max_overlap else sorted_matches

        combo_labels = []
        for combo in final_layouts:
            label = " + ".join(get_math_label(k) for k in combo)
            combo_labels.append(label)

        combo_options = combo_labels

        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_options,
            index=0,
            key=f"circles_highlight_{n}_{max_overlap}"
        )

        selected_idx = combo_options.index(selected_option)

    with col_plot:
        line_color = "#000000"
        bg_color = "#FFFFFF"

        fig = go.Figure()
        x_lines, y_lines = [], []
        theta_upper = np.linspace(0, np.pi, 40)

        # --- STEG 1: MARKERING (ENBART TJOCKA KONTURLINJER) ---
        if selected_idx >= 0 and selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            _, chosen_centers = get_layer_geometry(chosen_combo, pool)

            for k, x_center, diameter in chosen_centers:
                radius = diameter / 2.0
                cx = x_center + radius * np.cos(theta_upper)
                cy = 0.0 + radius * np.sin(theta_upper)

                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="none", fill="toself",
                    fillcolor="rgba(0, 0, 0, 0.0)",
                    hoverinfo="skip", showlegend=False
                ))

                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="lines",
                    line=dict(color=line_color, width=1.4),
                    hoverinfo="skip", showlegend=False
                ))

        # --- STEG 2: RITA ALLA BAKGRUNDSLINJER ---
        all_radii = []
        drawn_circles = set()

        for combo in final_layouts:
            _, final_centers = get_layer_geometry(combo, pool)

            for k, x_center, diameter in final_centers:
                radius = diameter / 2.0
                all_radii.append(radius)

                circle_id = (k, round(x_center, 4))

                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)

                    cx = x_center + radius * np.cos(theta_upper)
                    cy = 0.0 + radius * np.sin(theta_upper)

                    x_lines.extend(list(cx) + [None])
                    y_lines.extend(list(cy) + [None])

        # Central horisontell baslinje
        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, mode="lines", 
            line=dict(color=line_color, width=0.2), 
            hoverinfo="skip", showlegend=False
        ))

        # --- DYNAMISK GLOBAL CENTRERING INUTI RAMEN ---
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
