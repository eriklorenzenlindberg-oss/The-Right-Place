import sympy as sp
import streamlit as st

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

    for guess in [best_guess, 1.0, 1.2, 0.5, 2.0]:
        try:
            root = sp.nsolve(expr, x_sym, guess, verify=False)
            c = complex(root)
            if abs(c.imag) < 1e-7 and c.real > 0:
                return float(c.real)
        except Exception:
            continue
    return 1.2

@st.cache_data
def get_math_data(n, eq_input, add_value_str):
    x_sym = sp.Symbol("x")
    n_sym = sp.Symbol("n")

    # 1. Standardisera syntax
    eq_input = eq_input.replace("^", "**").strip()
    add_value_str = add_value_str.replace("^", "**").strip()

    # Ta enbart bort explicit "v =" från v-rutan
    if add_value_str.startswith("v"):
        add_value_str = add_value_str.lstrip("v").lstrip("=").strip()

    # 2. STENSÄKER INMATNINGSKOLL
    if "=" in eq_input:
        # Om det finns ett likhetstecken (t.ex. 1+x=x^n eller x=x^n-1) tar vi alltid Vänsterled - Högerled
        left_str, right_str = eq_input.split("=")
        raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
    else:
        # Om likhetstecken saknas helt
        parsed_expr = sp.sympify(eq_input)
        if parsed_expr.has(x_sym):
            # T.ex. "x^n - x - 1" -> Detta är redan ett polynom som ska vara lika med 0
            raw_expr = parsed_expr
        else:
            # T.ex. "2**(1/2)" -> Detta saknar x, så det betyder implicit x = 2**(1/2) -> x - 2**(1/2) = 0
            raw_expr = x_sym - parsed_expr

    # 3. Kontrollera om n/2-substitution krävs
    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = ("=" in eq_input) and has_fraction_exponent and (n % 2 != 0)

    if use_substitution:
        y_sym = sp.Symbol("y")
        raw_expr_subs = raw_expr.subs(x_sym, y_sym**2).subs(x_sym**(n_sym/2), y_sym**n)
        num, denom = sp.together(raw_expr_subs).as_numer_denom()
        var_sym = y_sym
    else:
        num, denom = sp.together(raw_expr).as_numer_denom()
        var_sym = x_sym

    # STRUKTURPOLYNOM: Det polynom som användaren faktiskt menat, med n insatt
    structure_poly = sp.expand(num).subs(n_sym, n)

    # 4. Hitta den stabila numeriska roten
    approx_root = find_numeric_root(structure_poly, var_sym)
    x_numeric = approx_root if not use_substitution else approx_root ** 2

    # 5. MINIMALPOLYNOM: Det sanna irreducibla polynomet för semicircles.py
    try:
        all_exact_roots = sp.real_roots(structure_poly)
        exact_root = min(all_exact_roots, key=lambda r: abs(float(r.evalf()) - approx_root))
        raw_min_poly = sp.minpoly(exact_root, var_sym)
        
        if use_substitution:
            minimal_poly = sp.expand(raw_min_poly).subs(y_sym, sp.sqrt(x_sym))
        else:
            minimal_poly = sp.expand(raw_min_poly)
    except Exception:
        if use_substitution:
            minimal_poly = sp.expand(structure_poly).subs(y_sym, sp.sqrt(x_sym))
        else:
            minimal_poly = sp.expand(structure_poly)

    if minimal_poly is not None:
        minimal_poly = sp.expand(minimal_poly)

    # 6. Skapa pooler för geometrin
    circle_pool = {}
    circle_pool_symbolic = {}
    for k in range(40):
        circle_pool[k] = float(x_numeric**k)
        circle_pool_symbolic[k] = x_sym**k

    # 7. Tolka v-uttrycket
    try:
        add_expr = sp.sympify(add_value_str)
    except Exception:
        add_expr = x_sym  

    add_expr_evaluated = add_expr.subs(n_sym, n)
    try:
        add_value_numeric = float(add_expr_evaluated.subs(x_sym, x_numeric).evalf())
    except Exception:
        add_value_numeric = float(x_numeric)

    # 8. FÖRENKLING AV V: Vi använder structure_poly istället för minimal_poly
    simplified_v_expr = add_expr_evaluated
    if structure_poly is not None:
        try:
            if use_substitution:
                y_sym = sp.Symbol("y")
                v_in_y = sp.expand(add_expr_evaluated).subs(x_sym, y_sym**2)
                rem_in_y = sp.rem(v_in_y, structure_poly, y_sym)
                simplified_v_expr = sp.expand(rem_in_y).subs(y_sym, sp.sqrt(x_sym))
            else:
                simplified_v_expr = sp.rem(sp.expand(add_expr_evaluated), sp.expand(structure_poly), x_sym)
        except Exception:
            pass

    # 9. HELTALSREDUCERING: Tvinga till rent heltal om uttrycket numeriskt är ett heltal
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
        "is_equation": True,
        "minimal_poly": minimal_poly,
        "structure_poly": structure_poly,
        "v_simplified": simplified_v_expr,
        "circle_pool": circle_pool,
        "circle_pool_symbolic": circle_pool_symbolic,
        "lengths1_numeric": lengths1_numeric,  
        "lengths2_numeric": lengths2_numeric   
    }
