"""Integrations-/End-to-End-Tests gegen die laufende API.

Deckt die Verifikationspunkte aus dem Plan ab:
- Login je Rolle inkl. 2FA-Flow (Setup, mfa_required, Verify)
- 2FA-Pflicht-Gating fuer interne Rollen (kein Zugriff bis 2FA aktiv)
- Rollenpruefung interner Endpunkte (`user` vs. admin-only)
- Mandantentrennung (404 bei Fremdzugriff)
- Vollstaendiger Bestell-Workflow inkl. aller 9 Status-Trigger
- API-Abdeckung aller Teilbereiche via OpenAPI-Schema

Voraussetzung: frische DB + laufende API (siehe conftest.py).
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from tests.conftest import _enable_2fa, _login_with_2fa, unique

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def world(client, admin_token):
    """Legt zwei Mandanten mit je einem Kunden-User, einen internen `user`
    (ohne 2FA), eine AVV-pflichtige Leistung und eine AVV-Vorlage an."""
    ah = _auth(admin_token)

    # AVV-pflichtige Leistung
    r = await client.post(
        "/api/v1/intern/leistungen",
        headers=ah,
        json={"leistungs_id": unique("L"), "name": "Managed Workplace", "preis": "49.90", "avv_erforderlich": True},
    )
    r.raise_for_status()
    leistung = r.json()

    # AVV-Vorlage
    r = await client.post(
        "/api/v1/intern/avv-vorlagen", headers=ah, json={"name": unique("AVV"), "version": "1.0", "inhalt": "x"}
    )
    r.raise_for_status()

    # Zwei Kunden
    async def mk_customer():
        r = await client.post(
            "/api/v1/intern/kunden",
            headers=ah,
            json={"kundennummer": unique("K"), "name": unique("Kunde"), "contact_email": "demo@example.org"},
        )
        r.raise_for_status()
        return r.json()

    customer_a = await mk_customer()
    customer_b = await mk_customer()

    # Kunden-User
    async def mk_kunde(customer):
        username = unique("kunde")
        r = await client.post(
            "/api/v1/intern/users",
            headers=ah,
            json={"username": username, "password": "pw-kunde-123", "role": "kunde", "customer_id": customer["id"]},
        )
        r.raise_for_status()
        r = await client.post("/auth/login", data={"username": username, "password": "pw-kunde-123"})
        r.raise_for_status()
        return r.json()["access_token"]

    token_a = await mk_kunde(customer_a)
    token_b = await mk_kunde(customer_b)

    # Interner user (Rolle user) – zunaechst OHNE 2FA
    user_name = unique("user")
    r = await client.post(
        "/api/v1/intern/users",
        headers=ah,
        json={"username": user_name, "password": "pw-user-123", "role": "user", "display_name": "Innendienst"},
    )
    r.raise_for_status()
    r = await client.post("/auth/login", data={"username": user_name, "password": "pw-user-123"})
    r.raise_for_status()
    user_token_no2fa = r.json()["access_token"]

    return {
        "admin_token": admin_token,
        "leistung": leistung,
        "customer_a": customer_a,
        "customer_b": customer_b,
        "kunde_a_token": token_a,
        "kunde_b_token": token_b,
        "user_name": user_name,
        "user_token_no2fa": user_token_no2fa,
    }


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def user_token(client, world):
    """Interner `user` mit abgeschlossenem 2FA-Setup -> nutzbarer Token."""
    secret = await _enable_2fa(client, world["user_token_no2fa"])
    return await _login_with_2fa(client, world["user_name"], "pw-user-123", secret)


# ---------------------------------------------------------------------------
# 2FA / Login je Rolle
# ---------------------------------------------------------------------------


async def test_admin_login_mit_2fa(client, admin_token):
    r = await client.get("/auth/me", headers=_auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "admin"
    assert body["totp_enabled"] is True


async def test_kunde_login_ohne_2fa_zwang(client, world):
    r = await client.get("/auth/me", headers=_auth(world["kunde_a_token"]))
    assert r.status_code == 200
    assert r.json()["role"] == "kunde"


async def test_interner_user_ohne_2fa_wird_geblockt(client, world):
    # Trotz gueltigem Token: interne Endpunkte verlangen aktives 2FA.
    r = await client.get("/api/v1/intern/anfragen", headers=_auth(world["user_token_no2fa"]))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Rollenpruefung interner Endpunkte
# ---------------------------------------------------------------------------


async def test_user_darf_operative_endpunkte(client, user_token):
    r = await client.get("/api/v1/intern/anfragen", headers=_auth(user_token))
    assert r.status_code == 200
    r = await client.get("/api/v1/intern/monitoring/uebersicht", headers=_auth(user_token))
    assert r.status_code == 200


async def test_user_darf_keine_admin_endpunkte(client, user_token):
    for path in ("/api/v1/intern/statusregeln", "/api/v1/intern/users", "/api/v1/intern/avv-vorlagen"):
        r = await client.get(path, headers=_auth(user_token))
        assert r.status_code == 403, path


async def test_admin_darf_admin_endpunkte(client, admin_token):
    for path in ("/api/v1/intern/statusregeln", "/api/v1/intern/users", "/api/v1/intern/avv-vorlagen"):
        r = await client.get(path, headers=_auth(admin_token))
        assert r.status_code == 200, path


async def test_kunde_darf_keine_internen_endpunkte(client, world):
    r = await client.get("/api/v1/intern/anfragen", headers=_auth(world["kunde_a_token"]))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Mandantentrennung + vollstaendiger Workflow inkl. 9 Trigger
# ---------------------------------------------------------------------------


async def test_workflow_und_mandantentrennung(client, world, user_token):
    ka = _auth(world["kunde_a_token"])
    kb = _auth(world["kunde_b_token"])
    ut = _auth(user_token)
    leistung = world["leistung"]

    # Kunde A bestellt -> warten_auf_signatur
    r = await client.post("/api/v1/portal/bestellungen", headers=ka, json={"leistung_id": leistung["id"]})
    assert r.status_code == 201
    bestellung = r.json()
    assert bestellung["status"] == "warten_auf_signatur"

    # Mandantentrennung: Kunde B sieht Kunde A's Bestellung nicht (404)
    r = await client.get(f"/api/v1/portal/bestellungen/{bestellung['id']}", headers=kb)
    assert r.status_code == 404
    # Kunde A selbst sieht sie
    r = await client.get(f"/api/v1/portal/bestellungen/{bestellung['id']}", headers=ka)
    assert r.status_code == 200

    # Signaturvorgang ermitteln (intern) und signieren -> signature_completed
    r = await client.get("/api/v1/intern/signaturen", headers=ut)
    assert r.status_code == 200
    vorgang = next(v for v in r.json() if v["bezugs_id"] == bestellung["id"])
    r = await client.post(f"/api/v1/portal/signatur/{vorgang['token']}/signieren", headers=ka)
    assert r.status_code == 200

    # -> avv_required: AVV ausstehend
    r = await client.get("/api/v1/portal/avv", headers=ka)
    avv = next(a for a in r.json() if a["bezugs_id"] == bestellung["id"])
    assert avv["status"] == "ausstehend"

    # Mandantentrennung auf AVV-Annahme: Kunde B darf nicht (404)
    r = await client.post(f"/api/v1/portal/avv/{avv['id']}/annehmen", headers=kb)
    assert r.status_code == 404

    # Kunde A nimmt AVV an -> avv_completed -> Auftrag + Leistungsschein (beauftragt)
    r = await client.post(f"/api/v1/portal/avv/{avv['id']}/annehmen", headers=ka)
    assert r.status_code == 200

    r = await client.get(f"/api/v1/portal/bestellungen/{bestellung['id']}", headers=ka)
    assert r.json()["status"] == "beauftragt"

    # Frisch angelegten Leistungsschein finden (intern)
    r = await client.get("/api/v1/intern/leistungsscheine", headers=ut)
    ls = next(
        l for l in r.json()
        if l["customer_id"] == world["customer_a"]["id"] and l["status_kunde"] == "beauftragt"
    )
    ls_id = ls["id"]

    # kickoff_scheduled -> kickoff_gestartet
    r = await client.post(
        f"/api/v1/intern/leistungsscheine/{ls_id}/workshops", headers=ut, json={"typ": "kickoff"}
    )
    assert r.status_code == 201
    r = await client.get(f"/api/v1/intern/leistungsscheine/{ls_id}", headers=ut)
    assert r.json()["status_kunde"] == "kickoff_gestartet"

    # onboarding_workshop_scheduled -> onboarding_workshop
    r = await client.post(
        f"/api/v1/intern/leistungsscheine/{ls_id}/workshops", headers=ut, json={"typ": "onboarding"}
    )
    onboarding = r.json()
    r = await client.get(f"/api/v1/intern/leistungsscheine/{ls_id}", headers=ut)
    assert r.json()["status_kunde"] == "onboarding_workshop"

    # onboarding_workshop_finished (Protokoll freigeben) -> in_bearbeitung
    r = await client.patch(
        f"/api/v1/intern/leistungsscheine/{ls_id}/workshops/{onboarding['id']}",
        headers=ut,
        json={"status": "protokoll_freigegeben"},
    )
    assert r.status_code == 200
    r = await client.get(f"/api/v1/intern/leistungsscheine/{ls_id}", headers=ut)
    assert r.json()["status_kunde"] == "in_bearbeitung"

    # customer_input_required -> warten_auf_kunde
    r = await client.post(f"/api/v1/intern/leistungsscheine/{ls_id}/kundenrueckfrage", headers=ut)
    assert r.json()["status_kunde"] == "warten_auf_kunde"

    # delivery_completed -> fertiggestellt -> survey_sent -> kundenzufriedenheitsabfrage
    r = await client.post(f"/api/v1/intern/leistungsscheine/{ls_id}/abschliessen", headers=ut)
    assert r.json()["status_kunde"] == "kundenzufriedenheitsabfrage"

    # Umfrage wurde automatisch angelegt + versendet; Kunde A beantwortet
    r = await client.get("/api/v1/portal/umfragen", headers=ka)
    umfrage = next(u for u in r.json() if u["leistungsschein_id"] == ls_id)
    assert umfrage["status"] == "versendet"
    r = await client.post(
        f"/api/v1/portal/umfragen/{umfrage['id']}/beantworten", headers=ka, json={"bewertung": 5, "kommentar": "Top"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "beantwortet"


# ---------------------------------------------------------------------------
# API-Abdeckung aller Teilbereiche (OpenAPI)
# ---------------------------------------------------------------------------


async def test_openapi_deckt_alle_teilbereiche(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    paths = set(r.json()["paths"].keys())

    erwartet = [
        "/auth/login",
        "/auth/2fa/verify",
        # Kundensicht
        "/api/v1/portal/dashboard",
        "/api/v1/portal/leistungen",
        "/api/v1/portal/bestellungen",
        "/api/v1/portal/anfragen",
        "/api/v1/portal/angebote",
        "/api/v1/portal/avv",
        "/api/v1/portal/auftraege",
        "/api/v1/portal/leistungsscheine",
        "/api/v1/portal/dokumente",
        "/api/v1/portal/umfragen",
        # Interne Sicht
        "/api/v1/intern/anfragen",
        "/api/v1/intern/angebote",
        "/api/v1/intern/bestellungen",
        "/api/v1/intern/auftraege",
        "/api/v1/intern/leistungsscheine",
        "/api/v1/intern/avv",
        "/api/v1/intern/avv-vorlagen",
        "/api/v1/intern/signaturen",
        "/api/v1/intern/monitoring/uebersicht",
        "/api/v1/intern/kunden",
        "/api/v1/intern/dokumente",
        "/api/v1/intern/leistungen",
        "/api/v1/intern/umfragen",
        "/api/v1/intern/statusregeln",
        "/api/v1/intern/users",
    ]
    fehlend = [p for p in erwartet if p not in paths]
    assert not fehlend, f"Fehlende API-Pfade im OpenAPI-Schema: {fehlend}"
