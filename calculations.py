import sympy as sp
import streamlit as st

# --------------------------------------------------
# ROBUST DYNAMISK NUMERISK SÖKARE
# --------------------------------------------------
def find_numeric_root(expr, x_sym):
    try:
        f_num = sp.lambdify(x_sym, expr, "numpy")
    except Exception:
        f_num = lambda v: float(expr.subs(x_sym, v).evalf())
    
    steps = [0.001, 0.01, 0.1, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 25.0, 50.0, 100.0]
    best_guess = 1.2
    
    for i in range(len(steps) - 1):
        try:
            if f_num(steps[i]) * f_num(steps[i+1]) < 0:
                best_guess = (steps[i] + steps[i+1]) / 2
                break
        except Exception:
            pass

    for guess in [best_guess, 1.2, 1.0, 0.5, 2.0]:
        try:
            root = sp.nsolve(expr, x_sym, guess, verify=False)
            c = complex(root)
            if abs(c.imag) < 1e-7 and c.real > 0:
                return float(c.real)
        except Exception:
            continue
            
    try:
        roots = sp.solve(expr, x_sym)
        for r in roots:
            try:
                c = complex(r.evalf())
                if abs(c.imag) < 1e-7 and c.real > 0:
                    return float(c.real)
            except Exception:
                pass
    except Exception:
        pass
        
    return 1.2


# --------------------------------------------------
# ALLOMFATTANDE MATEMATISK STRUKTURSÖKARE (UPPGRADUR)
# --------------------------------------------------
def find_math_structures_logical(n, x_sym, x_numeric, minimal_poly):
    if minimal_poly is None:
        pool = {m: float(x_numeric**m) for m in range(n)}
        return pool, [tuple(range(n))]

    poly_expr = sp.expand(minimal_poly)
    pool = {m: float((x_sym**m).subs(x_sym, x_numeric)) for m in range(n)}
    hidden_potencies = {}
    
    # 1. Hitta alla enkla dolda högre potenser upp till x**100
    for k in range(n, 100):
        rest = sp.rem(x_sym**k, poly_expr, x_sym)
        expanded_rest = sp.expand(rest)
        
        if sp.degree(expanded_rest, x_sym) >= n:
            continue
            
        components = []
        base_indices = set()
        is_pure_sum = True
        
        for m in range(n):
            coeff = expanded_rest.coeff(x_sym, m) if m > 0 else expanded_rest.subs(x_sym, 0)
            if coeff == 1:
                val = float((x_sym**m).subs(x_sym, x_numeric))
                components.append(val)
                base_indices.add(m)
            elif coeff != 0:
                is_pure_sum = False
                break
                
        if is_pure_sum and len(base_indices) >= 2:
            hidden_potencies[k] = {
                "diameter": float((x_sym**k).subs(x_sym, x_numeric)),
                "base_indices": base_indices
            }
            pool[k] = hidden_potencies[k]["diameter"]

    # 2. SKAPA ALLA GILTIGA SUBSTITIONER (ÄVEN DUBBLA/NÄSTLADE ERSÄTTNINGAR)
    total_sum_matches = []
    total_sum_matches.append(tuple(range(n))) # Huvudleden är alltid basen
    
    hidden_keys = list(hidden_potencies.keys())
    num_hidden = len(hidden_keys)
    
    # Testa alla kombinationer av dolda potenser (en i taget, två i taget, tre i taget...)
    # Vi använder binär maskning för att testa alla delmängder av dolda potenser linjärt och snabbt
    for mask in range(1, 1 << num_hidden):
        active_hidden_potencies = [hidden_keys[i] for i in range(num_hidden) if (mask & (1 << i))]
        
        # Kontrollera om de aktiva dolda potenserna krockar algebraiskt
        combined_base_indices = set()
        overlap_detected = False
        
        for hk in active_hidden_potencies:
            b_indices = hidden_potencies[hk]["base_indices"]
            if combined_base_indices.intersection(b_indices):
                overlap_detected = True
                break
            combined_base_indices.update(b_indices)
            
        # Om de inte krockar, betyder det att de kan ersätta sina respektive bas-termer samtidigt!
        if not overlap_detected and combined_base_indices.issubset(set(range(n))):
            remaining_base = set(range(n)) - combined_base_indices
            # Bygg den nya kombinationen: Återstående bas-termer + alla aktiva dolda potenser
            combo = tuple(sorted(list(remaining_base) + active_hidden_potencies))
            if combo not in total_sum_matches:
                total_sum_matches.append(combo)

    return pool, total_sum_matches


# --------------------------------------------------
# HUVUDDATA-FUNKTION (HÄMTAS AV APP.PY)
# --------------------------------------------------
@st.cache_data # Skyddar prestandan centralt
def get_math_data(n, eq_input, add_value_str):
    x_sym = sp.Symbol("x")
    n_sym = sp.Symbol("n")

    eq_input = eq_input.replace("^", "**")
    add_value_str = add_value_str.replace("^", "**")

    is_equation = "=" in eq_input

    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = is_equation and has_fraction_exponent and (n % 2 != 0)

    if use_substitution:
        y_sym = sp.Symbol("y")
        eq_input_substituted = eq_input.replace("x**(n/2)", "y**n").replace("x**(n / 2)", "y**n").replace("x", "y**2")
        
        is_equation = "=" in eq_input_substituted
        left_str, right_str = eq_input_substituted.split("=")
        raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
        expr_evaluated = raw_expr.subs(n_sym, n)
        minimal_poly = sp.expand(expr_evaluated)
        
        y_numeric = find_numeric_root(minimal_poly, y_sym)
        x_numeric = y_numeric ** 2
        
        circle_pool_y, total_sum_matches_y = find_math_structures_logical(
            n * 2, y_sym, y_numeric, minimal_poly
        )
        
        circle_pool = {m: float((x_sym**m).subs(x_sym, x_numeric)) for m in range(n)}
        total_sum_matches = [tuple(range(n))]
        
        for combo in total_sum_matches_y:
            if all(k % 2 == 0 for k in combo):
                translated_combo = tuple(k // 2 for k in combo)
                if translated_combo != tuple(range(n)) and translated_combo not in total_sum_matches:
                    total_sum_matches.append(translated_combo)
                
        for k, v in circle_pool_y.items():
            if k % 2 == 0:
                circle_pool[k // 2] = v
                
    else:
        if is_equation:
            left_str, right_str = eq_input.split("=")
            raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
            expr_evaluated = raw_expr.subs(n_sym, n)
            minimal_poly = sp.expand(expr_evaluated)
            x_numeric = find_numeric_root(expr_evaluated, x_sym)
        else:
            try:
                explicit_expr = sp.sympify(eq_input)
                explicit_evaluated = explicit_expr.subs(n_sym, n)
                x_numeric = float(explicit_evaluated.evalf())
            except Exception:
                x_numeric = 1.2
            minimal_poly = None

        circle_pool, total_sum_matches = find_math_structures_logical(
            n, x_sym, x_numeric, minimal_poly
        )

    try:
        add_expr = sp.sympify(add_value_str)
    except Exception:
        add_expr = x_sym  

    add_expr_evaluated = add_expr.subs(n_sym, n)
    
    try:
        add_value_numeric = float(add_expr_evaluated.subs(x_sym, x_numeric).evalf())
    except Exception:
        add_value_numeric = float(x_numeric)

    simplified_v_expr = add_expr_evaluated
    if is_equation and minimal_poly is not None and not use_substitution:
        try:
            simplified_v_expr = sp.rem(sp.expand(add_expr_evaluated), sp.expand(minimal_poly), x_sym)
        except Exception:
            pass

    max_terms = max(50, n + 20)
    symbolic_powers = {k: x_sym**k for k in range(max_terms)}
    numeric_powers = {k: float(x_numeric**k) for k in range(max_terms)}
    
    lengths1_symbolic = [x_sym**k for k in range(n)]
    lengths1_numeric = [float(x_numeric**k) for k in range(n)]

    lengths2_symbolic = lengths1_symbolic.copy()
    lengths2_numeric = lengths1_numeric.copy()
    
    lengths2_symbolic[0] = 1 + add_expr_evaluated  
    lengths2_numeric[0] = 1.0 + add_value_numeric   

    return {
        "n": n,
        "x_numeric": x_numeric,
        "x_symbolic": None if is_equation else x_numeric,
        "is_equation": is_equation,
        "input_mode": "equation" if is_equation else "explicit",
        "minimal_poly": minimal_poly,  
        "symbolic_powers": symbolic_powers,
        "numeric_powers": numeric_powers,
        "lengths1_symbolic": lengths1_symbolic,
        "lengths1_numeric": lengths1_numeric,
        "lengths2_symbolic": lengths2_symbolic,
        "lengths2_numeric": lengths2_numeric,
        "v_symbolic": add_expr_evaluated,
        "v_numeric": add_value_numeric,
        "v_simplified": simplified_v_expr,
        "circle_pool": circle_pool,
        "total_sum_matches": total_sum_matches
    }
