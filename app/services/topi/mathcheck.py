"""Kiểm toán bằng SymPy, không `exec`.

Mô hình viết đề và đáp án dưới dạng biểu thức SymPy (vd "7 - (2*x - 5)", "12 - 2*x");
code đọc bằng `parse_expr` với whitelist ký hiệu, rồi kiểm:
- biểu thức: simplify(đề - đáp án) == 0
- phương trình "lhs = rhs": đáp án dạng "x = 3" thoả phương trình
Không đọc được hoặc sai -> loại câu đó.
"""
import re
from typing import Optional

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
_SYMBOLS = {name: sp.Symbol(name) for name in "abcmnpqrstuvwxyz"}
_ALLOWED = {
    **_SYMBOLS,
    "sqrt": sp.sqrt, "Abs": sp.Abs, "Rational": sp.Rational, "pi": sp.pi,
}
# parse_expr sinh lời gọi Integer(...), Symbol(...), Float(...): chỉ cấp đúng các lớp lõi,
# không builtins, không cả namespace sympy.
_GLOBALS = {
    "__builtins__": {},
    "Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational, "Symbol": sp.Symbol,
    "Add": sp.Add, "Mul": sp.Mul, "Pow": sp.Pow, **_ALLOWED,
}
_SAFE_CHARS = re.compile(r"^[\w\s\+\-\*/\^\(\)\.,=|√]*$")
_MAX_LEN = 200


def _clean(expr: str) -> str:
    return (expr or "").replace("−", "-").replace("×", "*").replace("·", "*").replace("²", "^2").replace("³", "^3").strip()


def _parse(expr: str) -> Optional[sp.Expr]:
    e = _clean(expr)
    if not e or len(e) > _MAX_LEN or not _SAFE_CHARS.match(e) or "__" in e:
        return None
    e = e.replace("√", "sqrt").replace("|", "")
    try:
        return parse_expr(e, local_dict=dict(_ALLOWED), global_dict=dict(_GLOBALS),
                          transformations=_TRANSFORMS, evaluate=True)
    except Exception:
        return None


def identity_holds(text: Optional[str]) -> Optional[bool]:
    """"lhs = rhs" đúng với MỌI giá trị? Dùng để kiểm dòng "Đúng: ..." (phải True) và
    "Sai: ..." (phải False). None nếu không phải đẳng thức đọc được."""
    t = _clean(text or "")
    if t.count("=") != 1:
        return None
    lhs, rhs = t.split("=")
    L, R = _parse(lhs), _parse(rhs)
    if L is None or R is None:
        return None
    try:
        return sp.simplify(sp.expand(L) - sp.expand(R)) == 0
    except Exception:
        return None


def verify(problem: Optional[str], answer: Optional[str]) -> Optional[bool]:
    """True = đúng, False = sai/không đọc được, None = không có gì để kiểm."""
    if not problem or not answer:
        return None
    p, a = _clean(problem), _clean(answer)
    try:
        if "=" in p:
            lhs, rhs = p.split("=", 1)
            L, R = _parse(lhs), _parse(rhs)
            if L is None or R is None:
                return False
            eq = sp.simplify(L - R)
            subs = {}
            for part in a.split(","):
                if "=" not in part:
                    return False
                var, val = part.split("=", 1)
                v, x = _parse(var), _parse(val)
                if v is None or x is None or not isinstance(v, sp.Symbol):
                    return False
                subs[v] = x
            return sp.simplify(eq.subs(subs)) == 0
        P, A = _parse(p), _parse(a)
        if P is None or A is None:
            return False
        return sp.simplify(sp.expand(P) - sp.expand(A)) == 0
    except Exception:
        return False
