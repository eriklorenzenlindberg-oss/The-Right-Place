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
# HUVUDDATA-FUNKTION (HÄMTAS AV APP.PY)
# --------------------------------------------------
@st.cache_data
def get_math_data(n, eq_input, add_value_str):
    x_sym = sp.Symbol("x")
    n_sym = sp.Symbol("n")

    eq_input = eq_input.replace("^", "**")
    add_value_str = add_value_str.replace("^", "**")

    is_equation = "=" in eq_input

    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = is_equation and has_fraction_exponent and (n % 2 != 0)

    # Förbered grundpoolen för cirklar (x**0 upp till x**n)
    circle_pool = {}

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
        
        # Bygg poolen för sökningen baserat på y-substitutionen (upp till x**50 numeriskt)
        for k in range(50):
            if k % 2 == 0:
                circle_pool[k // 2] = float((y_sym**k).subs(y_sym, y_numeric))
                
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

        # Bygg standardpoolen upp till x**50 numeriskt
        for k in range(50):
            circle_pool[k] = float(x_numeric**k)

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
    
    # Här korrigerar vi tilldelningen så att listan blir korrekt
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
        "circle_pool": circle_pool
    }
