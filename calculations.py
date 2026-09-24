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

    for guess in [best_guess, 1.2, 1.0, 0.5, 2.0]:
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

    eq_input = eq_input.replace("^", "**")
    add_value_str = add_value_str.replace("^", "**")

    is_equation = "=" in eq_input
    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = is_equation and has_fraction_exponent and (n % 2 != 0)

    circle_pool = {}
    circle_pool_symbolic = {}  # NY: För exakta geometriska beräkningar

    if use_substitution:
        y_sym = sp.Symbol("y")
        eq_input_substituted = eq_input.replace("x**(n/2)", "y**n").replace("x**(n / 2)", "y**n").replace("x", "y**2")
        left_str, right_str = eq_input_substituted.split("=")
        raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
        expr_evaluated = raw_expr.subs(n_sym, n)
        
        y_numeric = find_numeric_root(sp.expand(expr_evaluated), y_sym)
        x_numeric = y_numeric ** 2
        
        # EXAKT: Skapa polynom direkt från uttrycket istället för minpoly på flyttal
        minimal_poly = sp.expand(expr_evaluated).subs(y_sym, sp.sqrt(x_sym))
            
    else:
        if is_equation:
            left_str, right_str = eq_input.split("=")
            raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
            expr_evaluated = raw_expr.subs(n_sym, n)
            x_numeric = find_numeric_root(expr_evaluated, x_sym)
            
            # EXAKT: Vi använder det utvärderade uttrycket direkt som vårt exakta polynom
            minimal_poly = sp.expand(expr_evaluated)
        else:
            try:
                explicit_expr = sp.sympify(eq_input)
                explicit_evaluated = explicit_expr.subs(n_sym, n)
                x_numeric = float(explicit_evaluated.evalf())
            except Exception:
                x_numeric = 1.2
            minimal_poly = None

    # Skapa både numeriska och symboliska pooler
    for k in range(40):
        circle_pool[k] = float(x_numeric**k)
        circle_pool_symbolic[k] = x_sym**k  # NY: Helt exakt x^k

    try:
        add_expr = sp.sympify(add_value_str)
    except Exception:
        add_expr = x_sym  

    add_expr_evaluated = add_expr.subs(n_sym, n)
    try:
        add_value_numeric = float(add_expr_evaluated.subs(x_sym, x_numeric).evalf())
    except Exception:
        add_value_numeric = float(x_numeric)

    # Exakt förenkling med polynomdivision (rem)
    simplified_v_expr = add_expr_evaluated
    if is_equation and minimal_poly is not None:
        try:
            simplified_v_expr = sp.rem(sp.expand(add_expr_evaluated), sp.expand(minimal_poly), x_sym)
        except Exception:
            pass

    lengths1_numeric = [float(x_numeric**k) for k in range(n)]
    lengths2_numeric = lengths1_numeric.copy()
    lengths2_numeric[0] = 1.0 + add_value_numeric   

    return {
        "n": n,
        "x_numeric": x_numeric,
        "x_symbolic": None if is_equation else x_numeric,
        "is_equation": is_equation,
        "minimal_poly": minimal_poly,  
        "v_simplified": simplified_v_expr,
        "circle_pool": circle_pool,
        "circle_pool_symbolic": circle_pool_symbolic,  # NY: Skickas med till semicircles
        "lengths1_numeric": lengths1_numeric,  
        "lengths2_numeric": lengths2_numeric   
    }

