import itertools
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp
from collections import deque

def get_math_label(power):
    if power == 0: return "1"
    if power == 1: return "x"
    power_int = int(power)
    superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    return f"x{''.join(superscripts.get(c, c) for c in str(power_int))}"

def get_layer_geometry_symbolic(combo, pool_symbolic):
    """ Beräknar geometri och centrum med 100% symbolisk exakthet """
    starts = {}
    centers = []
    current_x = sp.Integer(0) # Startar på exakt 0

    for k in combo:
        if k not in pool_symbolic: continue
        diameter = pool_symbolic[k] # Detta är ett exakt uttryck, t.ex. x^2
        radius = diameter / 2
        starts[k] = current_x
        # Spara centrum och diameter som exakta symboliska uttryck
        centers.append((k, current_x + radius, diameter))
        current_x += diameter
    return starts, centers

def evaluate_global_layout(sorted_matches, pool_symbolic):
    """ Matchar layouter med exakt symbolisk algebra istället för flyttal """
    optimized_layouts = []
    for idx, combo_keys in enumerate(sorted_matches):
        best_score = -1000
        best_layout = tuple(sorted(list(combo_keys)))

        for perm in itertools.permutations(combo_keys):
            _, current_centers = get_layer_geometry_symbolic(perm, pool_symbolic)
            score = 0

            for k, x_center, _ in current_centers:
                for prev_layout in optimized_layouts:
                    _, prev_centers = get_layer_geometry_symbolic(prev_layout, pool_symbolic)
                    for pk, px_center, _ in prev_centers:
                        # Exakt symbolisk jämförelse: drar bort och förenklar till 0
                        if pk == k and sp.simplify(px_center - x_center) == 0:
                            score += 1

            if score > best_score:
                best_score = score
                best_layout = perm
        optimized_layouts.append(best_layout)
    return optimized_layouts

def find_math_structures_logical(n, minimal_poly):
    """ Exakt vektorsökning utan flyttal (behålls intakt eftersom den fungerar superbra) """
    """
    Helt generell och exakt vektorsökning utan flyttal.
    Skapar tvåvägsregler för att klara alla skrivsätt (t.ex. 1 + x^4 = x^5).
    """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]

    P_x = sp.expand(minimal_poly)
    MAX_POWER = max(15, n + 5)
    
    # Elegant strukturellt tak: vi tillåter som högst potensen n + 1
    MAX_POWER = n + 1
    VECTOR_SIZE = MAX_POWER + 1

    # Skapa huvudledens startvektor (t.ex. [1, 1, 1, 1, 1, 0, 0] för n=5)
    huvudled_vektor = [0] * VECTOR_SIZE
    for i in range(n):
        if i < VECTOR_SIZE:
            huvudled_vektor[i] = 1

    # GENERERA ALLA LOGISKA REGLER (BÅDE FRAMÅT OCH BAKÅT)
    regler_vektorer = []
    
    # Hitta vilka potenser som faktiskt ingår i polynomet P(x)
    poly_obj = sp.Poly(P_x, x)
    ingående_potenser = poly_obj.monoms() # Ger t.ex. [(5,), (4,), (0,)] för x^5 - x^4 - 1
    ingående_potenser = [m[0] for m in ingående_potenser]

    # För varje tänkbar förskjutning (k) av polynomet...
    for k in range(VECTOR_SIZE):
        regel = sp.expand(P_x * x**k)
        vektor = [0] * VECTOR_SIZE
        giltig = True
        
        for p in range(VECTOR_SIZE):
            c = regel.coeff(x, p)
            if c != 0:
                vektor[p] = int(c)
        # Generera regler för VARJE enskild term i polynomet (ger tvåvägs-logik)
        for term_potens in ingående_potenser:
            if k + term_potens < VECTOR_SIZE:
                # Isolera denna term på ena sidan: resten av polynomet blir regeln
                # Exempel: x^5 = x^4 + 1 -> Vektor: [-1 på pos 5, +1 på pos 4, +1 på pos 0]
                vektor = [0] * VECTOR_SIZE
                giltig = True

        for p in range(VECTOR_SIZE, VECTOR_SIZE + 10):
            if regel.coeff(x, p) != 0:
                giltig = False
                break
        if giltig and any(v != 0 for v in vektor):
            regler_vektorer.append(vektor)
                # Multiplicera hela polynomet P(x) med x^k
                regel_uttryck = sp.expand(P_x * x**k)
                
                for p in range(VECTOR_SIZE):
                    c = regel_uttryck.coeff(x, p)
                    if c != 0:
                        vektor[p] = int(c)
                
                # Kontrollera att regeln inte "spiller över" vårt tak
                for p in range(VECTOR_SIZE, VECTOR_SIZE + 10):
                    if regel_uttryck.coeff(x, p) != 0:
                        giltig = False
                        break
                        
                if giltig and any(v != 0 for v in vektor):
                    # Lägg till regeln om den är unik
                    if vektor not in regler_vektorer:
                        regler_vektorer.append(vektor)

    # BREDE-FÖRST-SÖKNING (BFS)
    giltiga_kombinationer = set()
    besökta = set()

    start_tuple = tuple(huvudled_vektor)
    kö = deque([start_tuple])
    besökta.add(start_tuple)
    giltiga_kombinationer.add(tuple(range(n)))

    while kö:
        aktuell = kö.popleft()
        for reg_vek in regler_vektorer:
            # Eftersom reglerna är balanserade (summan=0) testar vi att både addera och subtrahera dem
            for tecken in [1, -1]:
                ny_vektor = [a + tecken * b for a, b in zip(aktuell, reg_vek)]
                
                # En kombination kan aldrig ha ett negativt antal cirklar av en viss storlek
                if any(v < 0 for v in ny_vektor):
                    continue

                ny_tuple = tuple(ny_vektor)
                if ny_tuple in besökta:
                    continue

                # Kontrollera om detta är en ren kombination (bara ettor, dvs. x^k finns med max 1 gång)
                potenser = [idx for idx, v in enumerate(ny_vektor) if v == 1]
                if sum(ny_vektor) == len(potenser) and len(potenser) > 0:
                    giltiga_kombinationer.add(tuple(sorted(potenser)))

                # Begränsa sökrymden så att vi inte samlar på oss multikombinationer (t.ex. 3st x^2)
                if max(ny_vektor) <= 2:
                    if len(besökta) < 3000:
                    if len(besökta) < 3000: # Säkerhetsspärr för Streamlit-prestanda
                        besökta.add(ny_tuple)
                        kö.append(ny_tuple)

    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))

def render(math_data):
    n = math_data["n"]
    minimal_poly = math_data["minimal_poly"]
    
    # Hämta den nya symboliska poolen och flyttalsvärdet för x för renderingen
    pool_symbolic = math_data["circle_pool_symbolic"]
    x_numeric = math_data["x_numeric"]
    x_sym = sp.Symbol("x")
    
    raw_matches = find_math_structures_logical(n, minimal_poly)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    # Beräkna målvärdet (total bredd) numeriskt baserat på x_numeric
    target_value = sum(float(x_numeric**m) for m in range(n))
    if target_value == 0: target_value = 1.0

    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # HÄR körs den exakta layout-sökningen symboliskt!
    overlap_layouts = evaluate_global_layout(sorted_matches, pool_symbolic)

    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")
        final_layouts = overlap_layouts if max_overlap else sorted_matches

        combo_labels = [" + ".join(get_math_label(k) for k in combo) for combo in final_layouts]
        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_labels,
            index=0,
            key=f"circles_highlight_{n}_{max_overlap}"
        )
        selected_idx = combo_labels.index(selected_option)

    with col_plot:
        line_color, bg_color = "#000000", "#FFFFFF"
        fig = go.Figure()
        x_lines, y_lines = [], []
        theta_upper = np.linspace(0, np.pi, 40)

        # Rita den markerade kombinationen (fylld)
        if 0 <= selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            # Hämta den exakta geometrin och utvärdera till float precis här med .subs() och .evalf()
            _, chosen_centers_sym = get_layer_geometry_symbolic(chosen_combo, pool_symbolic)
            
            for k, x_center_sym, diameter_sym in chosen_centers_sym:
                x_center = float(x_center_sym.subs(x_sym, x_numeric).evalf())
                diameter = float(diameter_sym.subs(x_sym, x_numeric).evalf())
                radius = diameter / 2.0
                
                cx = x_center + radius * np.cos(theta_upper)
                cy = radius * np.sin(theta_upper)
                fig.add_trace(go.Scatter(x=cx, y=cy, mode="none", fill="toself", fillcolor="rgba(0,0,0,0.00)", hoverinfo="skip", showlegend=False))
                fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", line=dict(color=line_color, width=1.4), hoverinfo="skip", showlegend=False))

        # Rita alla halvcirklar för basstrukturen
        all_radii, drawn_circles = [], set()
        for combo in final_layouts:
            _, final_centers_sym = get_layer_geometry_symbolic(combo, pool_symbolic)
            
            for k, x_center_sym, diameter_sym in final_centers_sym:
                # Gör om till flyttal som sista steg för Plotly
                x_center = float(x_center_sym.subs(x_sym, x_numeric).evalf())
                diameter = float(diameter_sym.subs(x_sym, x_numeric).evalf())
                radius = diameter / 2.0
                all_radii.append(radius)
                
                # Unikt ID baseras på den exakta symboliska positionen (omvandlad till sträng för set) för att undvika flyttalsduplisering
                circle_id = (k, str(x_center_sym))
                if circle_id not in drawn_circles:
                    drawn_circles.add(circle_id)
                    cx = x_center + radius * np.cos(theta_upper)
                    cy = radius * np.sin(theta_upper)
                    x_lines.extend(list(cx) + [None])
                    y_lines.extend(list(cy) + [None])

        # Lägg till baslinjen
        x_lines.extend([0.0, target_value, None])
        y_lines.extend([0.0, 0.0, None])

        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode="lines", line=dict(color=line_color, width=0.4), hoverinfo="skip", showlegend=False))

        # Beräkna grafens dimensioner (numeriskt)
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
        required_y_space = total_graph_width * 0.5

        if max_actual_height > (required_y_space * 0.85):
            required_y_space = max_actual_height / 0.80
            total_x_span = required_y_space * 2.0
            x_min = -(total_x_span - target_value) / 2.0
            x_max = target_value + (total_x_span - target_value) / 2.0
        else:
            x_min, x_max = -base_x_margin, target_value + base_x_margin

        y_center_point = max_actual_height / 2.0
        y_min = y_center_point - (required_y_space / 2.0)
        y_max = y_center_point + (required_y_space / 2.0)

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=400, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )
        st.plotly_chart(fig, use_container_width=True, key="semicircles_plot_clean")
