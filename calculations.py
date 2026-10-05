@st.cache_data
def get_math_data(n, eq_input, add_value_str):
    x_sym = sp.Symbol("x")
    n_sym = sp.Symbol("n")

    # 1. Standardisera syntax (ersätt ^ med **)
    eq_input = eq_input.replace("^", "**").strip()
    add_value_str = add_value_str.replace("^", "**").strip()

    # Ta bort eventuella "x =" eller "x=" om användaren skrivit det explicit
    if eq_input.startswith("x"):
        eq_input = eq_input.lstrip("x").lstrip("=").strip()
    if add_value_str.startswith("v"):
        add_value_str = add_value_str.lstrip("v").lstrip("=").strip()

    # Avgör om det är en implicit definition (uttryck) eller explicit (ekvation)
    # Om det saknas "=" antar vi att användaren menar "x = uttryck" vilket blir "x - uttryck = 0"
    if "=" in eq_input:
        left_str, right_str = eq_input.split("=")
        raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
    else:
        raw_expr = x_sym - sp.sympify(eq_input)

    # Hantera n/2 substitutionen om den behövs
    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = has_fraction_exponent and (n % 2 != 0)

    if use_substitution:
        y_sym = sp.Symbol("y")
        # Gör substitutionen på det sammanslagna råa uttrycket
        raw_expr_subs = raw_expr.subs(x_sym, y_sym**2).subs(x_sym**(n_sym/2), y_sym**n)
        num, denom = sp.together(raw_expr_subs).as_numer_denom()
        var_sym = y_sym
    else:
        num, denom = sp.together(raw_expr).as_numer_denom()
        var_sym = x_sym

    # STRUKTURPOLYNOM: Det ursprungliga polynomet med n insatt (t.ex. x^5 - x^4 - 1)
    structure_poly = sp.expand(num).subs(n_sym, n)

    # Hitta den stabila numeriska roten
    approx_root = find_numeric_root(structure_poly, var_sym)
    x_numeric = approx_root if not use_substitution else approx_root ** 2

    # MINIMALPOLYNOM: Det sanna irreducibla polynomet för semicircles.py
    try:
        all_exact_roots = sp.real_roots(structure_poly)
        exact_root = min(all_exact_roots, key=lambda r: abs(float(r.evalf()) - approx_root))
        raw_min_poly = sp.minpoly(exact_root, var_sym)
        
        if use_substitution:
            minimal_poly = sp.expand(raw_min_poly).subs(y_sym, sp.sqrt(x_sym))
        else:
            minimal_poly = sp.expand(raw_min_poly)
    except Exception:
        # Fallback om exakt sökning misslyckas
        if use_substitution:
            minimal_poly = sp.expand(structure_poly).subs(y_sym, sp.sqrt(x_sym))
        else:
            minimal_poly = sp.expand(structure_poly)

    if minimal_poly is not None:
        minimal_poly = sp.expand(minimal_poly)

    # Skapa numeriska pooler för geometrin
    circle_pool = {}
    circle_pool_symbolic = {}
    for k in range(40):
        circle_pool[k] = float(x_numeric**k)
        circle_pool_symbolic[k] = x_sym**k

    # Tolka v-uttrycket
    try:
        add_expr = sp.sympify(add_value_str)
    except Exception:
        add_expr = x_sym  

    add_expr_evaluated = add_expr.subs(n_sym, n)
    try:
        add_value_numeric = float(add_expr_evaluated.subs(x_sym, x_numeric).evalf())
    except Exception:
        add_value_numeric = float(x_numeric)

    # FÖRENKLING AV V: Vi använder structure_poly (användarens struktur) istället för minpoly
    # Detta gör att x^5 - 1 blir x^4 istället för x^2 + x
    simplified_v_expr = add_expr_evaluated
    try:
        # Om vi använde substitution måste vi anpassa divisionen, annars kör vi på structure_poly
        poly_for_division = structure_poly
        if use_substitution:
            # Gör om v till y-världen för divisionen
            v_in_y = sp.expand(add_expr_evaluated).subs(x_sym, y_sym**2)
            rem_in_y = sp.rem(v_in_y, poly_for_division, y_sym)
            simplified_v_expr = sp.expand(rem_in_y).subs(y_sym, sp.sqrt(x_sym))
        else:
            simplified_v_expr = sp.rem(sp.expand(add_expr_evaluated), sp.expand(poly_for_division), x_sym)
    except Exception:
        pass

    # EXTRA SÄKERHET: Tvinga till heltal om uttrycket numeriskt är ett heltal
    try:
        v_num_eval = float(simplified_v_expr.subs(x_sym, x_numeric).evalf())
        if abs(v_num_eval - round(v_num_eval)) < 1e-7:
            simplified_v_expr = sp.Integer(round(v_num_eval))
    except Exception:
        pass

    lengths1_numeric = [float(x_numeric**k) for k in range(n)]
    lengths2_numeric = lengths1_numeric.copy()
    lengths2_numeric[0] = 1.0 + add_value_numeric   

    return {
        "n": n,
        "x_numeric": x_numeric,
        "x_symbolic": None,
        "is_equation": "=" in eq_input or not eq_input.replace(".","").isdigit(),
        "minimal_poly": minimal_poly,       # Skickas till semicircles.py (bevarar dolda mönster)
        "structure_poly": structure_poly,   # Det ursprungliga polynomet
        "v_simplified": simplified_v_expr,  # Den snygga förenklingen (t.ex. x^4 eller rent heltal)
        "circle_pool": circle_pool,
        "circle_pool_symbolic": circle_pool_symbolic,
        "lengths1_numeric": lengths1_numeric,  
        "lengths2_numeric": lengths2_numeric   
    }
