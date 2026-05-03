from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Tuple


class TokenType(str, Enum):
    ID = "id"
    NUM = "num"
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    LPAREN = "("
    RPAREN = ")"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
    index: int  # absolute index in source string (0-based)


@dataclass(frozen=True)
class AnalysisError:
    kind: str  # "lex" | "syn" | "sem"
    line: int
    col: int
    message: str


@dataclass(frozen=True)
class Quad:
    op: str
    arg1: str
    arg2: str
    result: str


def _is_letter(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def tokenize(src: str) -> Tuple[List[Token], List[AnalysisError]]:
    tokens: List[Token] = []
    errors: List[AnalysisError] = []

    i = 0
    line = 1
    col = 1

    def advance(n: int = 1) -> None:
        nonlocal i, line, col
        for _ in range(n):
            if i >= len(src):
                return
            ch = src[i]
            i += 1
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1

    while i < len(src):
        ch = src[i]

        if ch.isspace():
            advance(1)
            continue

        start_i = i
        start_line = line
        start_col = col

        if _is_letter(ch):
            j = i + 1
            while j < len(src) and (_is_letter(src[j]) or _is_digit(src[j]) or src[j] == "_"):
                j += 1
            lex = src[i:j]
            tokens.append(Token(TokenType.ID, lex, start_line, start_col, start_i))
            advance(j - i)
            continue

        if ch == "_":
            errors.append(
                AnalysisError(
                    "lex",
                    start_line,
                    start_col,
                    "Идентификатор должен начинаться с буквы (найдено '_').",
                )
            )
            advance(1)
            continue

        if _is_digit(ch):
            j = i + 1
            while j < len(src) and _is_digit(src[j]):
                j += 1
            lex = src[i:j]
            tokens.append(Token(TokenType.NUM, lex, start_line, start_col, start_i))
            advance(j - i)
            continue

        single = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.MUL,
            "/": TokenType.DIV,
            "%": TokenType.MOD,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
        }.get(ch)
        if single is not None:
            tokens.append(Token(single, ch, start_line, start_col, start_i))
            advance(1)
            continue

        errors.append(AnalysisError("lex", start_line, start_col, f"Недопустимый символ: {ch!r}."))
        advance(1)

    tokens.append(Token(TokenType.EOF, "", line, col, len(src)))
    return tokens, errors


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[AnalysisError] = []
        self.quads: List[Quad] = []
        self._temp_counter = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def previous(self) -> Token:
        return self.tokens[max(0, self.pos - 1)]

    def at(self, t: TokenType) -> bool:
        return self.current().type == t

    def consume(self, t: TokenType, message: str) -> Optional[Token]:
        if self.at(t):
            tok = self.current()
            self.pos += 1
            return tok
        tok = self.current()
        self.errors.append(AnalysisError("syn", tok.line, tok.col, message))
        return None

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.current().type in types:
            tok = self.current()
            self.pos += 1
            return tok
        return None

    def new_temp(self) -> str:
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def emit(self, op: str, a1: str, a2: str) -> str:
        res = self.new_temp()
        self.quads.append(Quad(op, a1, a2, res))
        return res

    # Grammar:
    # E -> T A
    # A -> ε | + T A | - T A
    # T -> F B
    # B -> ε | * F B | / F B | % F B
    # F -> num | id | ( E )

    def parse(self) -> Optional[str]:
        expr_place = self.parse_E()
        if expr_place is None:
            return None
        if not self.at(TokenType.EOF):
            tok = self.current()
            self.errors.append(AnalysisError("syn", tok.line, tok.col, "Лишние символы после конца выражения."))
        return expr_place

    def parse_E(self) -> Optional[str]:
        left = self.parse_T()
        if left is None:
            return None
        return self.parse_A(left)

    def parse_A(self, inherited: str) -> Optional[str]:
        while True:
            op = self.match(TokenType.PLUS, TokenType.MINUS)
            if op is None:
                return inherited
            right = self.parse_T()
            if right is None:
                tok = self.current()
                self.errors.append(AnalysisError("syn", tok.line, tok.col, "Пропущен операнд после '+' или '-'."))
                return None
            inherited = self.emit(op.lexeme, inherited, right)

    def parse_T(self) -> Optional[str]:
        left = self.parse_F()
        if left is None:
            return None
        return self.parse_B(left)

    def parse_B(self, inherited: str) -> Optional[str]:
        while True:
            op = self.match(TokenType.MUL, TokenType.DIV, TokenType.MOD)
            if op is None:
                return inherited
            right = self.parse_F()
            if right is None:
                tok = self.current()
                self.errors.append(
                    AnalysisError("syn", tok.line, tok.col, "Пропущен операнд после '*', '/' или '%'.")
                )
                return None
            inherited = self.emit(op.lexeme, inherited, right)

    def parse_F(self) -> Optional[str]:
        tok = self.current()

        if self.match(TokenType.NUM):
            return tok.lexeme

        if self.match(TokenType.ID):
            return tok.lexeme

        if self.match(TokenType.LPAREN):
            inner = self.parse_E()
            if inner is None:
                return None
            if self.consume(TokenType.RPAREN, "Ожидалась ')' для закрытия скобки.") is None:
                return None
            return inner

        self.errors.append(
            AnalysisError(
                "syn",
                tok.line,
                tok.col,
                "Ожидалось число, идентификатор или '(' (пропущен операнд?).",
            )
        )
        return None


def build_rpn_and_eval(tokens: Iterable[Token]) -> Tuple[Optional[List[str]], List[AnalysisError], Optional[int]]:
    toks = [t for t in tokens if t.type != TokenType.EOF]
    errors: List[AnalysisError] = []

    for t in toks:
        if t.type == TokenType.ID:
            errors.append(
                AnalysisError(
                    "sem",
                    t.line,
                    t.col,
                    "ПОЛИЗ/вычисление доступны только для выражений из целых чисел (найден id).",
                )
            )
            return None, errors, None

    prec = {
        TokenType.PLUS: 1,
        TokenType.MINUS: 1,
        TokenType.MUL: 2,
        TokenType.DIV: 2,
        TokenType.MOD: 2,
    }
    ops_stack: List[Token] = []
    out: List[str] = []

    def pop_ops_until_lower_than(p: int) -> None:
        while ops_stack:
            top = ops_stack[-1]
            if top.type in (TokenType.LPAREN, TokenType.RPAREN):
                break
            if prec.get(top.type, 0) >= p:
                out.append(top.lexeme)
                ops_stack.pop()
            else:
                break

    for t in toks:
        if t.type == TokenType.NUM:
            out.append(t.lexeme)
            continue

        if t.type in (TokenType.PLUS, TokenType.MINUS, TokenType.MUL, TokenType.DIV, TokenType.MOD):
            pop_ops_until_lower_than(prec[t.type])
            ops_stack.append(t)
            continue

        if t.type == TokenType.LPAREN:
            ops_stack.append(t)
            continue

        if t.type == TokenType.RPAREN:
            while ops_stack and ops_stack[-1].type != TokenType.LPAREN:
                out.append(ops_stack.pop().lexeme)
            if not ops_stack:
                errors.append(AnalysisError("syn", t.line, t.col, "Лишняя ')' (нет соответствующей '(')."))
                return None, errors, None
            ops_stack.pop()
            continue

        errors.append(AnalysisError("syn", t.line, t.col, f"Неожиданная лексема для ПОЛИЗ: {t.lexeme!r}."))
        return None, errors, None

    while ops_stack:
        top = ops_stack.pop()
        if top.type == TokenType.LPAREN:
            errors.append(AnalysisError("syn", top.line, top.col, "Пропущена ')' (незакрытая '(')."))
            return None, errors, None
        out.append(top.lexeme)

    # Evaluate RPN (integer arithmetic)
    stack: List[int] = []
    for item in out:
        if item.isdigit():
            stack.append(int(item))
            continue

        if len(stack) < 2:
            errors.append(AnalysisError("syn", 1, 1, "Ошибка вычисления ПОЛИЗ: недостаточно операндов."))
            return out, errors, None

        b = stack.pop()
        a = stack.pop()
        if item == "+":
            stack.append(a + b)
        elif item == "-":
            stack.append(a - b)
        elif item == "*":
            stack.append(a * b)
        elif item == "/":
            if b == 0:
                errors.append(AnalysisError("sem", 1, 1, "Деление на ноль при вычислении ПОЛИЗ."))
                return out, errors, None
            stack.append(int(a / b))  # trunc toward zero
        elif item == "%":
            if b == 0:
                errors.append(AnalysisError("sem", 1, 1, "Деление на ноль при вычислении ПОЛИЗ (операция %)."))
                return out, errors, None
            stack.append(a % b)
        else:
            errors.append(AnalysisError("syn", 1, 1, f"Неизвестный оператор в ПОЛИЗ: {item!r}."))
            return out, errors, None

    if len(stack) != 1:
        errors.append(AnalysisError("syn", 1, 1, "Ошибка вычисления ПОЛИЗ: лишние операнды."))
        return out, errors, None

    return out, errors, stack[0]

