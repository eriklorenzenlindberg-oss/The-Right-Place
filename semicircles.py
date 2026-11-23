from collections import deque
from fractions import Fraction
from math import gcd

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp

X = sp.Symbol("x")

# Högsta antal element i en kombination för att pröva alla ordningar exakt (2^m steg).
# Längre kombinationer får en girig placering.
DP_LIMIT = 10
# Streckad linje för extracirklar efter ett hål i den geometriska följden
# (tunn respektive tjock markerad linje). Kommaseparerat: streck, mellanrum.
dashed_pattern = "3px,3px"
dashed_pattern_thick = "6px,4px"
# Övre gräns för antal tillstånd i sökningen efter kombinationer.
MAX_STATES = 3000


# ==================================================
# KRYSSRUTA SOM KOMMER IHÅG SITT VAL
# Streamlit glömmer en kryssrutas värde om den inte ritas i en körning
# (t.ex. när appen visar ett felmeddelande och stannar). Därför sparar vi
# valet under en egen nyckel och använder det som startvärde.
# ==================================================
def _remembering_checkbox(label, default, key):
    pref_key = f"pref_{label}"

    def remember():
        st.session_state[pref_key] = st.session_state[key]

    return st.checkbox(
        label,
        value=st.session_state.get(pref_key, default),
        key=key,
        on_change=remember,
    )


# ==================================================
# ETIKETTER
# ==================================================
def get_math_label(power):
    if power == 0:
        return "1"
    if power == 1:
        return "x"
    superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    return "x" + "".join(superscripts.get(c, c) for c in str(int(power)))


# ==================================================
# EXAKT MATEMATIK
# Allt i det här avsnittet räknar med heltal och bråk, aldrig med flyttal
# (förutom den övre gränsen max_k, som bara begränsar hur långt vi söker).
# ==================================================
def _integer_coeffs(minimal_poly):
    """Stigande heltalskoefficienter för minimalpolynomet, eller None om det inte
    är ett polynom i x med rationella koefficienter."""
    try:
        coeffs = sp.Poly(sp.expand(minimal_poly), X).all_coeffs()[::-1]
        if not coeffs or not all(c.is_Rational for c in coeffs):
            return None
        denominators = [int(sp.Rational(c).q) for c in coeffs]
        scale = sp.ilcm(*denominators) if denominators else 1
        ints = [int(c * scale) for c in coeffs]
        if len(ints) < 2 or ints[-1] == 0:
            return None
        return tuple(ints)
    except Exception:
        return None


def _poly_coeffs(expr):
    """Stigande rationella koefficienter (Fraction) för expr som polynom i x, eller None."""
    try:
        expr = sp.expand(expr)
        if not expr.free_symbols <= {X}:
            return None
        coeffs = sp.Poly(expr, X).all_coeffs()[::-1]
        if not all(c.is_Rational for c in coeffs):
            return None
        return [Fraction(int(sp.Rational(c).p), int(sp.Rational(c).q)) for c in coeffs]
    except Exception:
        return None


class NumberField:
    """
    Exakt räkning i Q(alpha), där alpha är en rot till heltalspolynomet P.
    Ett element är en tuple av d bråk (koefficienter för 1, alpha, ..., alpha^(d-1)).
    Två längder (eller positioner) är exakt lika om och bara om deras tupler är lika.

    För snabb jämförelse packas varje element till ett enda heltal (en "kod").
    Koderna adderas som vanliga heltal, och två koder är lika om och bara om
    elementen är exakt lika.
    """

    def __init__(self, p_coeffs, kmax):
        self.d = len(p_coeffs) - 1
        lead = Fraction(p_coeffs[-1])
        # alpha^d = sum(rel[i] * alpha^i)
        self.rel = [-Fraction(c) / lead for c in p_coeffs[:-1]]
        self.kmax = kmax
        self._powers = [self.reduce([1])]
        for _ in range(kmax):
            self._powers.append(self.reduce([Fraction(0)] + list(self._powers[-1])))
        self._D = None

    def reduce(self, coeffs):
        c = [Fraction(v) for v in coeffs]
        if len(c) < self.d:
            c += [Fraction(0)] * (self.d - len(c))
        for m in range(len(c) - 1, self.d - 1, -1):
            t = c[m]
            if t:
                c[m] = Fraction(0)
                for i, r in enumerate(self.rel):
                    c[m - self.d + i] += t * r
        return tuple(c[:self.d])

    def power(self, k):
        return self._powers[k]

    def finalize(self, extra_vectors=()):
        """Väljer nämnare och bas för koderna. Måste anropas innan code()/pcode()."""
        vectors = list(self._powers) + [v for v in extra_vectors if v is not None]
        D = 1
        for vec in vectors:
            for f in vec:
                D = D * f.denominator // gcd(D, f.denominator)
        max_abs = max([abs(int(f * D)) for vec in vectors for f in vec] + [1])
        # Basen är större än två gånger största möjliga summa, så koderna är entydiga
        bits = (2 * (self.kmax + 3) * max_abs).bit_length() + 1
        self._D = D
        self._base_powers = [1 << (bits * i) for i in range(self.d)]
        self._pcodes = [self.code(vec) for vec in self._powers]

    def code(self, vec):
        return sum(int(f * self._D) * bp for f, bp in zip(vec, self._base_powers))

    def pcode(self, k):
        return self._pcodes[k]


@st.cache_data
def _search_combinations(start_vector, p_coeffs, x_numeric):
    """
    Hittar alla kombinationer av olika potenser av x (varje potens högst en gång)
    vars summa exakt är lika med talet som start_vector beskriver.

    Metod: start_vector är koefficienterna för talet som ett polynom i x. Polynomet
    P * x^k är exakt noll, så vi får lägga till och dra ifrån det hur som helst. Varje
    vektor vi når med bara 0:or och 1:or är en giltig kombination.

    Returnerar (kombinationer, komplett). komplett = False om sökningen avbröts av
    tillståndsgränsen, så att det kan finnas fler kombinationer.
    """
    deg = len(p_coeffs) - 1
    target = sum(c * x_numeric ** k for k, c in enumerate(start_vector))

    # Ingen term kan vara större än summan. Detta är bara en sökgräns.
    max_k = 0
    while x_numeric ** max_k <= target * (1 + 1e-9) and max_k < 300:
        max_k += 1
    complete = max_k < 300

    size = max(max_k, len(start_vector) - 1) + deg + 1
    rules = []
    for k in range(size - deg):
        rule = [0] * size
        for i, c in enumerate(p_coeffs):
            rule[i + k] = c
        rules.append(rule)

    start = tuple(list(start_vector) + [0] * (size - len(start_vector)))

    def is_combination(vec):
        return any(vec) and all(v in (0, 1) for v in vec)

    def too_high(vec):
        return any(vec[i] for i in range(max_k + 1, size))

    combos = set()
    if is_combination(start):
        combos.add(tuple(i for i, v in enumerate(start) if v))

    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for rule in rules:
            for sign in (1, -1):
                new = tuple(a + sign * b for a, b in zip(current, rule))
                if new in seen or min(new) < 0 or too_high(new):
                    continue
                if is_combination(new):
                    combos.add(tuple(i for i, v in enumerate(new) if v))
                # Vi går bara vidare från vektorer med små poster (heuristik).
                if max(new) <= 2:
                    if len(seen) < MAX_STATES:
                        seen.add(new)
                        queue.append(new)
                    else:
                        complete = False

    return sorted(combos, key=lambda c: (len(c), c)), complete


def _continuous_limit(base, exponents):
    """
    Största K så att alla heltal från max(base) upp till K finns bland exponenterna.
    Cirklar med exponent <= K ingår i den obrutna geometriska följd som huvudledet
    börjar; cirklar med exponent > K ligger efter ett "hål" i följden.
    """
    have = set(base) | set(exponents)
    k = max(base)
    while k + 1 in have:
        k += 1
    return k


def _best_order(combo, field, drawn):
    """
    Ordnar potenserna i en kombination så att så många cirklar som möjligt
    sammanfaller exakt med redan ritade cirklar (samma diameter och samma startpunkt).
    """
    ks = sorted(combo)
    m = len(ks)
    vecs = [field.pcode(k) for k in ks]

    if m <= DP_LIMIT:
        size = 1 << m
        pos = [0] * size
        for mask in range(1, size):
            low = (mask & -mask).bit_length() - 1
            pos[mask] = pos[mask & (mask - 1)] + vecs[low]
        score = [-1] * size
        last = [0] * size
        prev = [0] * size
        score[0] = 0
        for mask in range(size):
            for j in range(m):
                if mask >> j & 1:
                    continue
                new_mask = mask | (1 << j)
                gain = 1 if (vecs[j], pos[mask]) in drawn else 0
                if score[mask] + gain > score[new_mask]:
                    score[new_mask] = score[mask] + gain
                    last[new_mask] = j
                    prev[new_mask] = mask
        order, mask = [], size - 1
        while mask:
            order.append(ks[last[mask]])
            mask = prev[mask]
        return tuple(reversed(order))

    # Giriga placeringen för långa kombinationer
    remaining = list(ks)
    order, pos = [], 0
    while remaining:
        choice = next((k for k in remaining if (field.pcode(k), pos) in drawn), remaining[0])
        order.append(choice)
        remaining.remove(choice)
        pos += field.pcode(choice)
    return tuple(order)


def _optimize_layouts(combos, field, seed_keys):
    """Ger en ordning för varje kombination så att cirklarna överlappar maximalt."""
    drawn = set(seed_keys)
    layouts = []
    for combo in combos:
        order = _best_order(combo, field, drawn)
        layouts.append(order)
        pos = 0
        for k in order:
            drawn.add((field.pcode(k), pos))
            pos += field.pcode(k)
    return layouts


# ==================================================
# CIRKLAR (nyckel för exakt jämförelse + siffror för ritning)
# ==================================================
def _pure_circles(order, field, x_numeric, tag):
    """Cirklar för en kombination av rena potenser av x."""
    circles, start = [], 0.0
    pos = 0
    for idx, k in enumerate(order):
        diameter = float(x_numeric ** k)
        if field:
            dv = field.pcode(k)
            key = (dv, pos)
            pos += dv
        else:
            key = (tag, "u", idx)
        circles.append((key, start, diameter))
        start += diameter
    return circles


def _main2_circles(n, lengths2, field, d1_code, rearranged=False):
    """
    Huvudledet i figur 2: första cirkeln har diametern 1 + v.
    Med rearranged=True ordnas cirklarna i storleksordning, som i figur 1.
    Returnerar (cirklar, startpunkt för cirkeln x, ordning av sidorna).
    """
    order = sorted(range(n), key=lambda i: lengths2[i]) if rearranged else list(range(n))
    circles, start, start_of_x = [], 0.0, 0.0
    pos = 0 if (field and d1_code is not None) else None
    for idx in order:
        diameter = float(lengths2[idx])
        dv = d1_code if idx == 0 else (field.pcode(idx) if field else None)
        if pos is not None and dv is not None:
            key = (dv, pos)
            pos += dv
        else:
            key = ("fig2", "u", idx)
            pos = None
        if idx == 1:
            start_of_x = start
        circles.append((key, start, diameter))
        start += diameter
    return circles, start_of_x, order


def _semicircle_xy(start, diameter, x_shift, y_shift, theta):
    radius = diameter / 2.0
    along = start + radius + radius * np.cos(theta)
    across = radius * np.sin(theta)
    return -across + x_shift, along + y_shift


def _t2_start_vector(v_exact, n):
    """Heltalskoefficienter för (1 + v) + x + ... + x^(n-1), eller None."""
    if v_exact is None:
        return None
    coeffs = _poly_coeffs(1 + v_exact + sum(X ** k for k in range(1, n)))
    if coeffs is None or any(c.denominator != 1 or c < 0 for c in coeffs):
        return None
    return tuple(int(c) for c in coeffs)


# ==================================================
# RENDER
# ==================================================
def render(math_data):
    n = math_data["n"]
    x_numeric = math_data["x_numeric"]
    lengths1 = math_data["lengths1_numeric"]
    lengths2 = math_data["lengths2_numeric"]
    v_exact = math_data.get("v_exact")

    # --- EXAKT DEL: vilka kombinationer finns? ---
    p_coeffs = _integer_coeffs(math_data["minimal_poly"])
    can_search = p_coeffs is not None and x_numeric > 1.0

    main1 = tuple(range(n))
    combos1, complete1 = [main1], True
    if can_search:
        combos1, complete1 = _search_combinations(tuple([1] * n), p_coeffs, x_numeric)
        if main1 not in combos1:
            combos1 = [main1] + list(combos1)
    hidden1 = [c for c in combos1 if c != main1]

    # Figur 2: samma sökning, men från (1 + v) + x + ... + x^(n-1)
    combos2, complete2 = [], True
    t2 = _t2_start_vector(v_exact, n)
    if can_search and t2 is not None:
        combos2, complete2 = _search_combinations(t2, p_coeffs, x_numeric)

    # Exakt talkropp för jämförelse av längder och positioner
    field, d1_vec, d1_code = None, None, None
    if p_coeffs is not None:
        biggest = max([k for c in list(combos1) + list(combos2) for k in c] + [n, 80])
        field = NumberField(p_coeffs, kmax=biggest + 1)
        one_plus_v = _poly_coeffs(1 + v_exact) if v_exact is not None else None
        if one_plus_v is not None:
            d1_vec = field.reduce(one_plus_v)
        field.finalize([d1_vec])
        if d1_vec is not None:
            d1_code = field.code(d1_vec)

    # Är huvudledet i figur 2 (med 1 + v) bara en annan ordning av rena potenser?
    main2_equiv = None
    if field is not None and d1_vec is not None:
        for j in range(0, 80):
            if field.power(j) == d1_vec:
                if j not in range(1, n):
                    main2_equiv = tuple(sorted([j] + list(range(1, n))))
                break
    # Är hela figur 2 exakt figur 1 multiplicerad med x^m? (Kontrolleras exakt.)
    # Då är varje kombination i figur 1, med alla exponenter ökade med m, också en
    # giltig kombination i figur 2.
    shift = None
    if field is not None and can_search and v_exact is not None:
        t2_coeffs = _poly_coeffs(1 + v_exact + sum(X ** k for k in range(1, n)))
        if t2_coeffs is not None:
            t2_vec = field.reduce(t2_coeffs)
            for m in range(1, 50):
                if field.reduce([0] * m + [1] * n) == t2_vec:
                    shift = m
                    break
    if shift is not None:
        combos2 = sorted(
            set(combos2) | {tuple(k + shift for k in c) for c in combos1},
            key=lambda c: (len(c), c),
        )
    # Extracirklar ritas bara om huvudledet i figur 2 är en geometrisk följd med kvoten x,
    # dvs. om 1 + v exakt är x^0 eller x^n (sidorna är då på varandra följande potenser).
    is_geometric = main2_equiv is not None and main2_equiv[-1] - main2_equiv[0] == n - 1
    if not is_geometric:
        combos2 = []
    elif main2_equiv[0] != 0:
        # 1 är utbytt mot 1 + v, så det finns ingen cirkel med diametern 1 (x^0)
        combos2 = [c for c in combos2 if 0 not in c]
    hidden2 = [c for c in combos2 if c != main2_equiv]

    # Extracirklar som ligger efter ett hål i den geometriska följden ritas streckade
    exps1 = {k for c in combos1 for k in c}
    dashed_codes1 = set()
    dashed_codes2 = set()
    if field is not None:
        limit1 = _continuous_limit(main1, exps1)
        dashed_codes1 = {field.pcode(k) for k in exps1 if k > limit1}
        if main2_equiv is not None:
            exps2 = {k for c in combos2 for k in c}
            limit2 = _continuous_limit(main2_equiv, exps2)
            dashed_codes2 = {field.pcode(k) for k in exps2 if k > limit2}

    # --- KONTROLLER ---
    col_plot, col_controls = st.columns([8, 2])
    with col_controls:
        max_overlap = _remembering_checkbox("Overlap", True, f"circles_overlap_{n}")
        rearrange2 = st.checkbox("Rearrange fig. 2", value=False, key=f"circles_rearrange_{n}")

    # --- ORDNING OCH CIRKLAR ---
    main1_circles = _pure_circles(main1, field, x_numeric, "fig1")
    main2_circles, x_start2, main2_order = _main2_circles(n, lengths2, field, d1_code, rearrange2)

    if max_overlap and field is not None:
        order1 = _optimize_layouts(hidden1, field, [c[0] for c in main1_circles])
        order2 = _optimize_layouts(hidden2, field, [c[0] for c in main2_circles])
    else:
        order1, order2 = list(hidden1), list(hidden2)

    circles1_by_layout = [main1_circles] + [
        _pure_circles(o, field, x_numeric, "fig1") for o in order1
    ]
    circles2_by_layout = [main2_circles] + [
        _pure_circles(o, field, x_numeric, "fig2") for o in order2
    ]
    def label_of(order):
        return " + ".join(get_math_label(k) for k in order)

    # Motsvarighet i figur 2 för varje alternativ i listan (när huvudledet är geometriskt
    # är figur 2 figur 1 förstorad med x, eller identisk med figur 1 om v = 0).
    layouts1 = [main1] + order1
    circles2_by_combo = {
        tuple(sorted(o)): (circ, o) for o, circ in zip(order2, circles2_by_layout[1:])
    }
    main2_label = " + ".join("(1 + v)" if i == 0 else get_math_label(i) for i in main2_order)
    counter_shift = 0 if (is_geometric and main2_equiv[0] == 0) else 1
    counterparts = []  # (cirklar i figur 2, etikett) eller (None, None)
    for i, order in enumerate(layouts1):
        match = (None, None)
        if i == 0:
            match = (main2_circles, main2_label)
        elif is_geometric:
            wanted = tuple(sorted(k + counter_shift for k in order))
            if wanted == main2_equiv:
                match = (main2_circles, main2_label)
            elif wanted in circles2_by_combo:
                circ, o = circles2_by_combo[wanted]
                match = (circ, label_of(o))
        counterparts.append(match)

    with col_controls:
        highlight_target = st.radio(
            "Highlight in:", ["Fig. 1", "Fig. 2"], index=0,
            horizontal=True, key=f"circles_hl_target_{n}",
        )
        highlight_fig1 = highlight_target == "Fig. 1"
        highlight_fig2 = highlight_target == "Fig. 2"

        # Etiketterna beskriver figuren man markerar i
        if highlight_fig2:
            combo_labels = [
                cp[1] if cp[1] else f"{label_of(o)} (not in fig. 2)"
                for o, cp in zip(layouts1, counterparts)
            ]
        else:
            combo_labels = [label_of(o) for o in layouts1]

        chooser = st.radio if len(combo_labels) <= 15 else st.selectbox
        selected_idx = chooser(
            "Select combination:",
            options=list(range(len(combo_labels))),
            index=0,
            format_func=lambda i: combo_labels[i],
            key=f"circles_highlight_{n}_{max_overlap}_{highlight_target}",
        )

        if not (complete1 and complete2):
            st.caption("The search was limited, so more combinations may exist.")

    with col_plot:
        line_color, bg_color = "#FFFFFF", "rgba(0,0,0,0)"
        theta = np.linspace(0, np.pi, 40)

        total1 = float(sum(lengths1))
        total2 = float(sum(lengths2))

        max_r1 = max(d for layout in circles1_by_layout for _, _, d in layout) / 2.0
        max_r2 = max(d for layout in circles2_by_layout for _, _, d in layout) / 2.0
        gap = 0.4 * max(max_r1, max_r2)
        fig2_x_offset = max_r2 + gap

        # Höjdjustering: cirkeln x ska ligga på samma höjd i båda figurerna
        y_offset2 = float(lengths1[0]) - x_start2

        def trace_coords(layouts, x_shift, y_shift, baseline_len, dashed_codes, with_baseline=True):
            xs, ys, dxs, dys, drawn = [], [], [], [], set()
            for layout in layouts:
                for key, start, diameter in layout:
                    if key in drawn:
                        continue
                    drawn.add(key)
                    cx, cy = _semicircle_xy(start, diameter, x_shift, y_shift, theta)
                    if key[0] in dashed_codes:
                        dxs.extend(list(cx) + [None])
                        dys.extend(list(cy) + [None])
                    else:
                        xs.extend(list(cx) + [None])
                        ys.extend(list(cy) + [None])
            if with_baseline:
                xs.extend([x_shift, x_shift, None])
                ys.extend([y_shift, y_shift + baseline_len, None])
            return xs, ys, dxs, dys

        fig = go.Figure()

        # Underliggande (tunna) cirklar. Extracirklar efter ett hål i den geometriska
        # följden ritas streckade.
        for layouts, x_shift, y_shift, total, with_baseline, dashed_codes in (
            (circles1_by_layout, 0.0, 0.0, total1, True, dashed_codes1),
            (circles2_by_layout, fig2_x_offset, y_offset2, total2, True, dashed_codes2),
        ):
            xs, ys, dxs, dys = trace_coords(layouts, x_shift, y_shift, total, dashed_codes, with_baseline)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines",
                                     line=dict(color=line_color, width=0.7),
                                     hoverinfo="skip", showlegend=False))
            if dxs:
                fig.add_trace(go.Scatter(x=dxs, y=dys, mode="lines",
                                         line=dict(color=line_color, width=0.7, dash=dashed_pattern),
                                         hoverinfo="skip", showlegend=False))

        # Tjocka linjer: bara i de figurer som är ibockade under "Highlight in"
        highlight2 = counterparts[selected_idx][0] if highlight_fig2 else None
        thick = []
        if highlight_fig1:
            thick.append((circles1_by_layout[selected_idx], 0.0, 0.0, dashed_codes1))
        if highlight2 is not None:
            thick.append((highlight2, fig2_x_offset, y_offset2, dashed_codes2))
        for circles, x_shift, y_shift, dashed_codes in thick:
            for key, start, diameter in circles:
                cx, cy = _semicircle_xy(start, diameter, x_shift, y_shift, theta)
                is_dashed = key[0] in dashed_codes
                fig.add_trace(go.Scatter(
                    x=cx, y=cy, mode="lines",
                    line=dict(color=line_color, width=2.5,
                              **({"dash": dashed_pattern_thick} if is_dashed else {})),
                    hoverinfo="skip", showlegend=False))

        # --- GEMENSAM SKALNING ---
        # Gränserna räknas ut för båda lägena av figur 2 (med och utan "Rearrange"),
        # så att figur 1 ligger exakt still när kryssrutan ändras.
        offsets2 = [
            float(lengths1[0]) - _main2_circles(n, lengths2, field, d1_code, flag)[1]
            for flag in (False, True)
        ]
        y_max_bound = max(total1, max(o + total2 for o in offsets2))
        y_min_bound = min(0.0, min(offsets2))
        pad = (y_max_bound - y_min_bound) * 0.05
        y_min, y_max = y_min_bound - pad, y_max_bound + pad

        x_min = -max_r1 * 1.1
        x_max = fig2_x_offset + max_r1 * 0.1

        y_span, x_span = y_max - y_min, x_max - x_min
        if y_span > x_span:
            diff = (y_span - x_span) / 2.0
            x_min -= diff
            x_max += diff
        else:
            diff = (x_span - y_span) / 2.0
            y_min -= diff
            y_max += diff

        fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=bg_color, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=290, dragmode=False,
            xaxis=dict(visible=False, range=[x_min, x_max], fixedrange=True),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1,
                       range=[y_min, y_max], fixedrange=True),
        )

        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': False, 'scrollZoom': False},
                        key=f"semicircles_combined_{n}")
