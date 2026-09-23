import itertools
import numpy as np
import plotly.graph_objects as go
import streamlit as st

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
# GEOMETRI OCH STRUKTURLOGIK
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


# --- MATEMATISK MATCHNINGS-ALGORITM (DIN BEPRÖVADE FRÅN MATPLOTLIB) ---
def evaluate_global_layout(sorted_matches, pool):
    """
    Matchar cirklarnas mittpunkter (x_center) horisontellt på samma sätt som 
    Matplotlib-koden gjorde vertikalt. Körs supersnabbt per enskilt lager.
    """
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
# DIN URSPRUNGLIGA SÖKLOGIK (FLYTTAD HIT)
# --------------------------------------------------
import sympy as sp
from collections import deque

def find_math_structures_logical_EXAKT(n, minimal_poly):
    """
    Helt exakt algebraisk sökning. 
    Arbetar ENBART med symboler och exakta heltal. Inga flyttal, inga toleranser.
    """
    x = sp.Symbol("x")
    
    # Om det inte finns någon ekvation (minimal_poly är None), finns bara huvudleden
    if minimal_poly is None:
        return [tuple(range(n))]
        
    # Skapa den exakta symboliska huvudleden: 1 + x + x^2 + ... + x^(n-1)
    huvudled = sp.expand(sum(x**i for i in range(n)))
    
    # Vi sätter en övre exakt potensgräns baserad på n (t.ex. n + 10)
    MAX_POWER = n + 10
    
    # Skapa de exakta reglerna baserat på ditt minimala polynom: P(x) * x^k
    # Exempel: (x^3 - x - 1) * x^k
    regler = []
    for k in range(MAX_POWER):
        regel = sp.expand(minimal_poly * x**k)
        regler.append(regel)

    giltiga_kombinationer = set()
    besökta_uttryck = set()
    
    # Kön håller (aktuellt_exakt_symboliskt_uttryck, nästa_regel_index)
    kö = deque([(huvudled, 0)])
    besökta_uttryck.add(huvudled)
    
    # Huvudleden är alltid den första sanna kombinationen
    giltiga_kombinationer.add(tuple(range(n)))
    
    while kö:
        aktuellt = kö.popleft()[0]
        
        # Vi letar efter nya uttryck genom att kombinera våra exakta regler
        for i, regel in enumerate(regler):
            for tecken in [1, -1]:
                nytt_uttryck = sp.expand(aktuellt + tecken * regel)
                
                if nytt_uttryck in besökta_uttryck:
                    continue
                    
                # Hämta ut termerna exakt från SymPy
                termer_dict = nytt_uttryck.as_coefficients_dict()
                
                # REGLER FÖR EN GILTIG GEOMETRISK KOMBINATION:
                # 1. Inga negativa koefficienter (inga minustecken i polynomet)
                if any(koeff <= 0 for koeff in termer_dict.values()):
                    continue
                    
                # 2. Inga potenser får skjuta över vår maxgräns
                for term in termer_dict.keys():
                    p = term.exp if isinstance(term, sp.Pow) else (1 if term == x else 0)
                    if p > MAX_POWER:
                        continue
                
                # Om uttrycket bara består av rena ettor (koefficient == 1) 
                # då har vi hittat en perfekt, exakt algebraisk ersättning!
                if all(koeff == 1 for koeff in termer_dict.values()):
                    potenser = []
                    for term in termer_dict.keys():
                        p = term.exp if isinstance(term, sp.Pow) else (1 if term == x else 0)
                        potenser.append(p)
                    giltiga_kombinationer.add(tuple(sorted(potenser)))
                
                # Vi tillåter trädet att växa genom tillfälliga överlapp (t.ex. en tvåa),
                # men vi sätter en spärr så att koefficienterna inte drar iväg
                if max(termer_dict.values()) <= 2:
                    besökta_uttryck.add(nytt_uttryck)
                    # Vi skickar inte med i+1 här, utan låter den testa alla regler i nästa led
                    # för att inte missa kedje-substitutioner (som i 1+x^4=x^5)
                    if len(besökta_uttryck) < 2000:  # Säkerhetsspärr för minnet
                        kö.append((nytt_uttryck, 0))
                        
    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))



# --------------------------------------------------
# RENDER (Minimalistisk, ren och synkroniserad)
# --------------------------------------------------

def render(math_data):
    raw_matches = math_data.get("total_sum_matches", [])
    n = math_data["n"]
    pool = math_data["circle_pool"]
    minimal_poly = math_data["minimal_poly"]
    
    # KÖR SÖKNINGEN HÄR LOKALT ISTÄLLET
    raw_matches = find_math_structures_logical(n, pool, minimal_poly)

    if not raw_matches or len(raw_matches) == 0:
        st.info("The main line is missing from the data.")
        return

    n = math_data["n"]
    pool = math_data["circle_pool"]

    target_value = sum(pool[m] for m in range(n) if m in pool)
    if target_value == 0:
        target_value = 1.0

    # --- DIAGRAMSPECIFIK STRUKTURERING AV DATAN ---
    unique_combos = set(tuple(sorted(list(combo))) for combo in raw_matches)
    main_line = max(unique_combos, key=len)
    hidden_lines = sorted(list(unique_combos - {main_line}), key=lambda c: (len(c), c))
    sorted_matches = [main_line] + hidden_lines

    # --- BERÄKNA MATCHADE ORDNINGAR KORREKT ---
    # RÄTTNING: Vi skickar hela listan till matchningen på en gång, precis som förut!
    overlap_layouts = evaluate_global_layout(sorted_matches, pool)

    # Breddförhållande för kolumnerna
    col_plot, col_controls = st.columns([6, 3])

    with col_controls:
        max_overlap = st.checkbox("Overlap", value=False, key="circles_overlap")

        # Bestäm vilket set av layouter som ska ritas och visas i texten
        final_layouts = overlap_layouts if max_overlap else sorted_matches

        # Skapa etiketterna baserat på den ordning de faktiskt kommer att ritas i
        combo_labels = []
        for combo in final_layouts:
            label = " + ".join(get_math_label(k) for k in combo)
            combo_labels.append(label)

        combo_options = combo_labels

        selected_option = st.radio(
            "Select combination to highlight:",
            options=combo_options,
            index=0, # Alltid huvudleden tänd vid start
            key=f"circles_highlight_{n}_{max_overlap}"
        )

        selected_idx = combo_options.index(selected_option)

    with col_plot:
        line_color = "#000000"
        bg_color = "#FFFFFF"

        fig = go.Figure()
        x_lines, y_lines = [], []
        theta_upper = np.linspace(0, np.pi, 40)

        # --- STEG 1: MARKERING (ENBART TJOCKA KONTURLINJER, INGEN TEXT) ---
        if selected_idx >= 0 and selected_idx < len(final_layouts):
            chosen_combo = final_layouts[selected_idx]
            _, chosen_centers = get_layer_geometry(chosen_combo, pool)

            for k, x_center, diameter in chosen_centers:
                radius = diameter / 2.0
                cx = x_center + radius * np.cos(theta_upper)
                cy = 0.0 + radius * np.sin(theta_upper)

                # Osynlig fyllning sparad i bakgrunden för strukturen
                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="none", fill="toself",
                    fillcolor="rgba(0, 0, 0, 0.0)",
                    hoverinfo="skip", showlegend=False
                ))

                # Rita den tjocka markerade konturlinjen
                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="lines",
                    line=dict(color=line_color, width=1.4),
                    hoverinfo="skip", showlegend=False
                ))

        # --- STEG 2: RITA ALLA BAKGRUNDSLINJER (MED UNIK FILTERING) ---
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

        # Standardbakgrunden med tunn linjebredd
        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, mode="lines", 
            line=dict(color=line_color, width=0.2), 
            hoverinfo="skip", showlegend=False
        ))

        # --- DYNAMISK GLOBAL CENTRERING INUTI RAMEN ---
        max_actual_height = max(all_radii) if all_radii else (target_value * 0.5)
        base_x_margin = target_value * 0.05
        total_graph_width = target_value + (2 * base_x_margin)
        required_y_space = total_graph_width * 0.5

        if max_actual_height > (required_y_space * 0.85):
            required_y_space = max_actual_height / 0.80
            total_x_span = required_y_space * 2.0
            extra_x_margin = (total_x_span - target_value) / 2.0
            x_min = -extra_x_margin
            x_max = target_value + extra_x_margin
        else:
            x_min = -base_x_margin
            x_max = target_value + base_x_margin

        y_center_point = max_actual_height / 2.0
        y_min = y_center_point - (required_y_space / 2.0)
        y_max = y_center_point + (required_y_space / 2.0)

        # --- LAYOUT OCH ABSOLUT AXELLÅSNING ---
        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=400, 
            dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max]),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[y_min, y_max])
        )

        st.plotly_chart(
            fig, 
            use_container_width=True, 
            key="semicircles_plot_clean"
        )
