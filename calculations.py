import re
from math import lcm

import sympy as sp
import streamlit as st

# --------------------------------------------------
# GRUNDSYMBOLER
# --------------------------------------------------
x_sym = sp.Symbol("x")
n_sym = sp.Symbol("n")
# y används när x måste skrivas som y**d för att få heltalsexponenter
# (t.ex. x^(n/2) med udda n). "positive" gör att sympy förenklar (y**2)**(5/2) till y**5.
y_sym = sp.Symbol("y", positive=True)

# --------------------------------------------------
# INMATNINGSSKYDD
# sympify() kör eval() på texten. Eftersom appen kan ligga publikt släpper vi
# därför bara igenom tecken och namn som faktiskt behövs.
# --------------------------------------------------
ALLOWED_NAMES = {"x", "n", "sqrt", "cbrt", "root", "pi", "exp", "log"}
ALLOWED_CHARS = re.compile(r"^[0-9A-Za-z+\-*/().,\s]*$")
MAX_INPUT_LENGTH = 120
MAX_NUMBER = 1000  # skyddar mot t.ex. x^99999999


class InputError(ValueError):
    """Ogiltig inmatning från användaren. Texten visas som felmeddelande i appen."""


def _parse(text, what):
    """Tolkar en textsträng till ett sympy-uttryck, med validering."""
    text = text.replace("^", "**").strip()
    if not text:
        raise InputError(f"The field for {what} is empty.")
    if len(text) > MAX_INPUT_LENGTH:
        raise InputError(f"The expression for {what} is too long.")
    if not ALLOWED_CHARS.match(text):
        raise InputError(
            f"The expression for {what} contains characters that are not allowed."
        )
    for name in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", text):
        if name not in ALLOWED_NAMES:
            raise InputError(
                f"Unknown name '{name}' in the expression for {what}. "
                "Use only x, n, numbers, + - * / ^ ( ) and sqrt, root, pi, exp, log."
            )
    for number in re.findall(r"\d+", text):
        if int(number) > MAX_NUMBER:
            raise InputError(
                f"Numbers larger than {MAX_NUMBER} are not allowed (in {what})."
            )
    try:
        expr = sp.sympify(text, locals={"x": x_sym, "n": n_sym})
    except Exception:
        raise InputError(
            f"Could not interpret the expression for {what}: '{text}'. "
            "Check parentheses and use * for multiplication (2*x, not 2x)."
        ) from None
    if not isinstance(expr, sp.Expr):
        raise InputError(f"The expression for {what} is not a valid formula.")
    return expr


def _build_raw_expr(eq_input):
    """
    Gör om inmatningen till ett uttryck som ska vara = 0.
      "1+x=x^n"   ->  1 + x - x**n
      "x^n-x-1"   ->  uttrycket självt (innehåller x)
      "2^(1/2)"   ->  x - 2**(1/2)      (saknar x: tolkas som x = uttryck)
      "x=2^(1/2)" ->  x - 2**(1/2)
    """
    text = eq_input.strip()
    if text.count("=") > 1:
        raise InputError("Use at most one '=' sign in the equation for x.")
    if "=" in text:
        left, right = text.split("=")
        return _parse(left, "the left side of the equation") - _parse(
            right, "the right side of the equation"
        )
    parsed = _parse(text, "x")
    return parsed if parsed.has(x_sym) else x_sym - parsed


def _root_power(expr):
    """
    Om x förekommer med bråkexponenter (t.ex. x**(5/2) när n = 5) returneras
    nämnaren d så att x = y**d ger heltalsexponenter. Annars 1.
    """
    denominators = [
        sp.Rational(p.exp).q
        for p in expr.atoms(sp.Pow)
        if p.base == x_sym and p.exp.is_Rational
    ]
    return lcm(*denominators) if denominators else 1


# --------------------------------------------------
# NUMERISK ROT (approximation, används bara för ritning)
# --------------------------------------------------
def find_numeric_root(expr, var):
    try:
        f_num = sp.lambdify(var, expr, "numpy")
    except Exception:
        f_num = lambda v: float(expr.subs(var, v).evalf())

    steps = [0.001, 0.01, 0.1, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0,
             3.0, 5.0, 10.0, 25.0, 50.0, 100.0]
    best_guess = 1.2

    for i in range(len(steps) - 1):
        try:
            if f_num(steps[i]) * f_num(steps[i + 1]) < 0:
                best_guess = (steps[i] + steps[i + 1]) / 2
                break
        except Exception:
            pass

    for guess in [best_guess, 1.2, 1.0, 0.5, 2.0]:
        try:
            root = sp.nsolve(expr, var, guess, verify=False)
            c = complex(root)
            # Kontrollera att vi verkligen hittat en rot (nsolve med verify=False
            # kan annars returnera ett värde som inte konvergerat)
            if abs(c.imag) < 1e-7 and c.real > 0 and abs(f_num(c.real)) < 1e-6:
                return float(c.real)
        except Exception:
            continue

    raise InputError(
        "Could not find a positive real solution for x with these settings."
    )


# --------------------------------------------------
# EXAKT MINIMALPOLYNOM (ren matematik)
# --------------------------------------------------
def _minimal_poly(structure_poly, var, approx_root, d):
    """
    Returnerar ett polynom i x (heltalskoefficienter) som x är rot till.
    Försöker först det sanna minimalpolynomet. Om det misslyckas returneras
    ett (inte nödvändigtvis irreducibelt) polynom som x garanterat är rot till.
    """
    try:
        poly = sp.Poly(structure_poly, var)
        if poly.domain.is_QQ or poly.domain.is_ZZ:
            roots = sp.real_roots(structure_poly)
        else:
            # Koefficienter som t.ex. sqrt(2): real_roots stöder inte detta
            roots = sp.solve(structure_poly, var)
        root = min(roots, key=lambda r: abs(complex(sp.N(r)) - approx_root))
        # Minimalpolynomet för x självt (x = root**d), inte för y
        return sp.expand(sp.minpoly(root ** d, x_sym))
    except Exception:
        pass

    if d == 1:
        return sp.expand(structure_poly)
    # x = y**d: resultanten eliminerar y och ger ett polynom i x
    return sp.expand(sp.resultant(structure_poly, x_sym - var ** d, var))


# --------------------------------------------------
# HUVUDFUNKTION
# --------------------------------------------------
@st.cache_data
def get_math_data(n, eq_input, add_value_str):
    n = int(n)

    # 1. Tolka ekvationen, sätt in n
    raw_expr = _build_raw_expr(eq_input).subs(n_sym, n)

    # 2. Bråkexponenter (t.ex. x^(n/2) med udda n) -> substituera x = y**d
    d = _root_power(raw_expr)
    if d > 1:
        var = y_sym
        raw_expr = raw_expr.subs(x_sym, y_sym ** d)
    else:
        var = x_sym

    # 3. STRUKTURPOLYNOM: polynomet användaren faktiskt menat, med n insatt
    num, _ = sp.together(raw_expr).as_numer_denom()
    structure_poly = sp.expand(num)
    if not structure_poly.has(var):
        raise InputError("The equation must contain x.")
    try:
        sp.Poly(structure_poly, var)
    except sp.PolynomialError:
        raise InputError(
            "With this n, the equation is not a polynomial in x. "
            "Use only integer powers of x, or exponents like n/2."
        ) from None

    # 4. NUMERISK ROT (approximation, bara för ritning)
    approx_root = find_numeric_root(structure_poly, var)
    x_numeric = approx_root ** d

    # 5. MINIMALPOLYNOM (exakt, används av semicircles.py)
    minimal_poly = _minimal_poly(structure_poly, var, approx_root, d)

    # 6. Pooler för geometrin
    circle_pool = {k: float(x_numeric ** k) for k in range(40)}
    circle_pool_symbolic = {k: x_sym ** k for k in range(40)}

    # 7. Tolka v
    add_text = re.sub(r"^\s*v\s*=", "", add_value_str)  # tillåt "v = ..."
    add_expr = _parse(add_text, "v").subs(n_sym, n)
    try:
        add_value_numeric = float(add_expr.subs(x_sym, x_numeric).evalf())
    except (TypeError, ValueError):
        raise InputError(
            "v must be a real number once x and n are filled in."
        ) from None
    if add_value_numeric <= -1:
        raise InputError("v must be greater than -1, so that the side 1 + v stays positive.")

    # 8. FÖRENKLING AV V (exakt)
    # a) Reducera mot structure_poly, så att t.ex. x^5 - 1 blir x^4 (inte x^2 + x)
    simplified_v_expr = add_expr
    try:
        v_expanded = sp.expand(add_expr)
        if d > 1:
            v_in_y = v_expanded.subs(x_sym, y_sym ** d)
            rem_in_y = sp.rem(v_in_y, structure_poly, y_sym)
            simplified_v_expr = sp.expand(rem_in_y).subs(
                y_sym, x_sym ** sp.Rational(1, d)
            )
        else:
            simplified_v_expr = sp.rem(v_expanded, structure_poly, x_sym)
    except Exception:
        pass

    # b) Exakt kontroll: är v en konstant modulo polynomet? Då är det ett exakt tal,
    #    utan någon numerisk tolerans.
    try:
        v_mod_min = sp.rem(sp.expand(add_expr), minimal_poly, x_sym)
        if not v_mod_min.has(x_sym):
            simplified_v_expr = sp.nsimplify(v_mod_min) if v_mod_min.is_Float else v_mod_min
    except Exception:
        pass

    # 9. Numeriska längder för ritning
    lengths1_numeric = [float(x_numeric ** k) for k in range(n)]
    lengths2_numeric = lengths1_numeric.copy()
    lengths2_numeric[0] = 1.0 + add_value_numeric

    return {
        "n": n,
        "x_numeric": x_numeric,
        "minimal_poly": minimal_poly,
        "structure_poly": structure_poly,
        "v_simplified": simplified_v_expr,
        "circle_pool": circle_pool,
        "circle_pool_symbolic": circle_pool_symbolic,
        "lengths1_numeric": lengths1_numeric,
        "lengths2_numeric": lengths2_numeric,
    }
