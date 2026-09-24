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
    """
    Helt generell och exakt vektorsökning utan flyttal.
    Skapar tvåvägsregler för att klara alla skrivsätt (t.ex. 1 + x^4 = x^5).
    """
    x = sp.Symbol("x")
    if minimal_poly is None:
        return [tuple(range(n))]
        
    P_x = sp.expand(minimal_poly)
    
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
        # Generera regler för VARJE enskild term i polynomet (ger tvåvägs-logik)
        for term_potens in ingående_potenser:
            if k + term_potens < VECTOR_SIZE:
                # Isolera denna term på ena sidan: resten av polynomet blir regeln
                # Exempel: x^5 = x^4 + 1 -> Vektor: [-1 på pos 5, +1 på pos 4, +1 på pos 0]
                vektor = [0] * VECTOR_SIZE
                giltig = True
                
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
                    if len(besökta) < 3000: # Säkerhetsspärr för Streamlit-prestanda
                        besökta.add(ny_tuple)
                        kö.append(ny_tuple)
                        
    return sorted(list(giltiga_kombinationer), key=lambda c: (len(c), c))
