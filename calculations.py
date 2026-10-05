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

    # 1. Standardisera syntax (ersätt ^ med **)
    eq_input = eq_input.replace("^", "**").strip()
    add_value_str = add_value_str.replace("^", "**").strip()

    # Ta bort eventuella "x =" eller "x=" om användaren råkat skriva det explicit i rutan
    if eq_input.startswith("x"):
        eq_input = eq_input.lstrip("x").lstrip("=").strip()
    if add_value_str.startswith("v"):
        add_value_str = add_value_str.lstrip("v").lstrip("=").strip()

    is_equation = "=" in eq_input
    has_fraction_exponent = "n/2" in eq_input or "n / 2" in eq_input
    use_substitution = is_equation and has_fraction_exponent and (n % 2 != 0)

    circle_pool = {}
    circle_pool_symbolic = {}

    if is_equation:
        # Skapa det råa uttrycket baserat på inmatningen
        if use_substitution:
            y_sym = sp.Symbol("y")
            eq_input_substituted = eq_input.replace("x**(n/2)", "y**n").replace("x**(n / 2)", "y**n").replace("x", "y**2")
            left_str, right_str = eq_input_substituted.split("=")
            raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
            var_sym = y_sym
        else:
            left_str, right_str = eq_input.split("=")
            raw_expr = sp.sympify(left_str) - sp.sympify(right_str)
            var_sym = x_sym

        # Multiplicera bort eventuella nämnare (t.ex. x-1) så att det blir ett rent polynom
        num, denom = sp.together(raw_expr).as_numer_denom()
        
        # STRUKTURPOLYNOM: Det ursprungliga polynomet med n insatt (t.ex. x^5 - x^4 - 1)
        structure_poly = sp.expand(num).subs(n_sym, n)

        # Hitta den numeriska gissningen som vi vet fungerar stabilt
        approx_root = find_numeric_root(structure_poly, var_sym)
        
        # MINIMALPOLYNOM: Hitta det sanna minimalpolynomet HELT UTAN flyttalsavrundningar
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

        # Sätt det stabila flyttalsvärdet för x
        x_numeric = approx_root if not use_substitution else approx_root ** 2

    else:
        # Implicit spår (om likhetstecken saknas, t.ex. x = 2**(1/2))
        try:
            explicit_expr = sp.sympify(eq_input)
            explicit_evaluated = explicit_expr.subs(n_sym, n)
            x_numeric = float(explicit_evaluated.evalf())
        except Exception:
            x_numeric = 1.2
        
        # Skapa ett låtsas-strukturpolynom baserat på värdet för att undvika krascher i resten av logiken
        structure_poly = x_sym - x_numeric
        minimal_poly = None

    if minimal_poly is not None:
        minimal_poly = sp.expand(minimal_poly)

    # Skapa pooler för geometrin
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

    # FÖRENKLING AV V: Använder structure_poly om det är en ekvation för att få x^4 istället för x^2 + x
    simplified_v_expr = add_expr_evaluated
    if is_equation and structure_poly is not None:
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

    # AGGRESSIV HELTALSREDUCERING: Tvinga till heltal om uttrycket numeriskt är ett heltal
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
        "x_symbolic": None if is_equation else x_numeric,
        "is_equation": is_equation,
        "minimal_poly": minimal_poly,       # Skickas till semicircles.py (bevarar dolda mönster)
        "structure_poly": structure_poly,   # Det ursprungliga polynomet
        "v_simplified": simplified_v_expr,  # Den rena förenklingen (t.ex. x^4)
        "circle_pool": circle_pool,
        "circle_pool_symbolic": circle_pool_symbolic,
        "lengths1_numeric": lengths1_numeric,  
        "lengths2_numeric": lengths2_numeric   
    }
