"""
Demo simplificada de integración de pasarela de pago con tarjeta (Python).

IMPORTANTE: es un SIMULADOR sin red ni credenciales. Muestra la estructura del
flujo (validar -> tokenizar -> cobrar -> manejar errores), no llama a Kushki.
En una integración real, SandboxGateway se reemplaza por una clase que haga
las llamadas HTTP a la API de la pasarela con las llaves del comercio.
"""
import uuid
from dataclasses import dataclass


class GatewayError(Exception):
    pass


def luhn_ok(numero: str) -> bool:
    d = [int(c) for c in numero if c.isdigit()]
    if len(d) < 13:
        return False
    s = 0
    for i, n in enumerate(reversed(d)):
        if i % 2 == 1:
            n *= 2
            n -= 9 if n > 9 else 0
        s += n
    return s % 10 == 0


@dataclass
class Cargo:
    subtotal: float
    iva_pct: float = 0.15
    moneda: str = "USD"

    @property
    def iva(self) -> float:
        return round(self.subtotal * self.iva_pct, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.iva, 2)


class SandboxGateway:
    """Simula tokenización y cobro. Tarjetas que terminan en 0002 se rechazan."""

    def tokenizar(self, numero: str, expira: str, cvv: str) -> str:
        numero = numero.replace(" ", "")
        if not luhn_ok(numero):
            raise GatewayError("Número de tarjeta inválido")
        if len(cvv) not in (3, 4):
            raise GatewayError("CVV inválido")
        # El número real nunca se guarda: solo se devuelve un token.
        return f"tok_{numero[-4:]}_{uuid.uuid4().hex[:8]}"

    def cobrar(self, token: str, cargo: Cargo) -> dict:
        if token.split("_")[1] == "0002":
            raise GatewayError("Tarjeta rechazada por el emisor")
        return {
            "estado": "aprobado",
            "ticket": uuid.uuid4().hex[:12],
            "total": cargo.total,
            "moneda": cargo.moneda,
        }


def pagar(gw, numero, expira, cvv, cargo):
    try:
        token = gw.tokenizar(numero, expira, cvv)
        return gw.cobrar(token, cargo)
    except GatewayError as e:
        return {"estado": "rechazado", "motivo": str(e)}


if __name__ == "__main__":
    gw = SandboxGateway()
    cargo = Cargo(subtotal=20.00)
    print(f"Subtotal {cargo.subtotal} + IVA {cargo.iva} = {cargo.total} {cargo.moneda}\n")
    for nombre, tarjeta in [("Tarjeta válida", "4242 4242 4242 4242"),
                            ("Rechazada por emisor", "4000 0000 0000 0002"),
                            ("Número inválido", "1234 5678 9012 3456")]:
        print(nombre, "->", pagar(gw, tarjeta, "12/28", "123", cargo))
