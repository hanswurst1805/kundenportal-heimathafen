"""Manuelles End-to-End-Skript zur Verifikation des Kernworkflows (Schritt 4).

Nicht Teil der automatisierten Test-Suite - dient als einmalige Verifikation
waehrend der Implementierung. Setzt einen frisch initialisierten Admin-Benutzer
voraus (Bootstrap-Passwort aus INITIAL_ADMIN_PASSWORD)."""

from __future__ import annotations

import asyncio
import os

import httpx
import pyotp

BASE = "http://localhost:8000"
ADMIN_PW = os.environ.get("INITIAL_ADMIN_PASSWORD", "changeme123")


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE) as client:
        # 1. Admin-Login + 2FA-Setup
        r = await client.post("/auth/login", data={"username": "admin", "password": ADMIN_PW})
        r.raise_for_status()
        data = r.json()
        assert data["needs_2fa_setup"], data
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = await client.post("/auth/2fa/setup", headers=headers)
        r.raise_for_status()
        secret = r.json()["secret"]
        code = pyotp.TOTP(secret).now()

        r = await client.post("/auth/2fa/enable", headers=headers, json={"code": code})
        r.raise_for_status()
        print("2FA aktiviert fuer admin")

        # Re-Login mit 2FA
        r = await client.post("/auth/login", data={"username": "admin", "password": ADMIN_PW})
        r.raise_for_status()
        data = r.json()
        assert data["mfa_required"], data
        mfa_token = data["mfa_token"]

        code = pyotp.TOTP(secret).now()
        r = await client.post("/auth/2fa/verify", json={"mfa_token": mfa_token, "code": code})
        r.raise_for_status()
        admin_token = r.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("Admin-Login mit 2FA erfolgreich")

        # 2. Katalogleistung mit AVV-Pflicht anlegen
        r = await client.post(
            "/api/v1/intern/leistungen",
            headers=admin_headers,
            json={
                "leistungs_id": "MS-100",
                "name": "Managed Workplace",
                "preis": "49.90",
                "avv_erforderlich": True,
            },
        )
        r.raise_for_status()
        leistung = r.json()
        print("Leistung angelegt:", leistung["leistungs_id"])

        # 3. AVV-Vorlage anlegen
        r = await client.post(
            "/api/v1/intern/avv-vorlagen",
            headers=admin_headers,
            json={"name": "Standard-AVV", "version": "1.0", "inhalt": "AVV-Text"},
        )
        r.raise_for_status()
        print("AVV-Vorlage angelegt")

        # 4. Kunde + Kunden-User anlegen
        r = await client.post(
            "/api/v1/intern/kunden",
            headers=admin_headers,
            json={"kundennummer": "K-0001", "name": "Testkunde GmbH"},
        )
        r.raise_for_status()
        customer = r.json()
        print("Kunde angelegt:", customer["kundennummer"])

        r = await client.post(
            "/api/v1/intern/users",
            headers=admin_headers,
            json={
                "username": "kunde1",
                "password": "kundenpasswort123",
                "role": "kunde",
                "customer_id": customer["id"],
                "display_name": "Test Kunde",
            },
        )
        r.raise_for_status()
        print("Kunden-User angelegt")

        # 5. Kunde loggt sich ein (kein 2FA-Zwang)
        r = await client.post("/auth/login", data={"username": "kunde1", "password": "kundenpasswort123"})
        r.raise_for_status()
        kunde_token = r.json()["access_token"]
        kunde_headers = {"Authorization": f"Bearer {kunde_token}"}

        # 6. Kunde bestellt Standardleistung
        r = await client.get("/api/v1/portal/leistungen", headers=kunde_headers)
        r.raise_for_status()
        assert any(l["leistungs_id"] == "MS-100" for l in r.json())

        r = await client.post(
            "/api/v1/portal/bestellungen", headers=kunde_headers, json={"leistung_id": leistung["id"]}
        )
        r.raise_for_status()
        bestellung = r.json()
        assert bestellung["status"] == "warten_auf_signatur", bestellung
        print("Bestellung angelegt, Status:", bestellung["status"])

        # 7. Signaturvorgang finden + signieren
        r = await client.get("/api/v1/intern/signaturen", headers=admin_headers)
        r.raise_for_status()
        vorgaenge = [v for v in r.json() if v["bezugs_id"] == bestellung["id"]]
        assert vorgaenge, "kein Signaturvorgang fuer Bestellung gefunden"
        token = vorgaenge[0]["token"]

        r = await client.post(f"/api/v1/portal/signatur/{token}/signieren", headers=kunde_headers)
        r.raise_for_status()
        print("Bestellung signiert")

        # 8. AVV sollte jetzt ausstehend sein (Leistung hat avv_erforderlich=True)
        r = await client.get("/api/v1/portal/bestellungen", headers=kunde_headers)
        r.raise_for_status()
        bestellung = [b for b in r.json() if b["id"] == bestellung["id"]][0]
        assert bestellung["status"] == "avv_ausstehend", bestellung
        print("Bestellung-Status nach Signatur:", bestellung["status"])

        r = await client.get("/api/v1/portal/avv", headers=kunde_headers)
        r.raise_for_status()
        avv = [a for a in r.json() if a["bezugs_id"] == bestellung["id"]][0]
        assert avv["status"] == "ausstehend", avv

        r = await client.post(f"/api/v1/portal/avv/{avv['id']}/annehmen", headers=kunde_headers)
        r.raise_for_status()
        print("AVV angenommen")

        # 9. Auftrag + Leistungsschein sollten jetzt existieren, Status "beauftragt"
        r = await client.get("/api/v1/portal/bestellungen", headers=kunde_headers)
        r.raise_for_status()
        bestellung = [b for b in r.json() if b["id"] == bestellung["id"]][0]
        assert bestellung["status"] == "beauftragt", bestellung
        print("Bestellung-Status nach AVV:", bestellung["status"])

        r = await client.get("/api/v1/intern/leistungsscheine", headers=admin_headers)
        r.raise_for_status()
        ls = [l for l in r.json() if l["status_kunde"] == "beauftragt"][0]
        print("Leistungsschein angelegt:", ls["ls_nummer"], "Status:", ls["status_kunde"])

        # 10. Kick-Off-Workshop einplanen -> Status kickoff_gestartet
        r = await client.post(
            f"/api/v1/intern/leistungsscheine/{ls['id']}/workshops",
            headers=admin_headers,
            json={"typ": "kickoff"},
        )
        r.raise_for_status()

        r = await client.get(f"/api/v1/intern/leistungsscheine/{ls['id']}", headers=admin_headers)
        r.raise_for_status()
        ls = r.json()
        assert ls["status_kunde"] == "kickoff_gestartet", ls
        print("LS-Status nach Kick-Off-Planung:", ls["status_kunde"])

        # 11. Onboarding-Workshop einplanen -> onboarding_workshop, dann Protokoll freigeben -> in_bearbeitung
        r = await client.post(
            f"/api/v1/intern/leistungsscheine/{ls['id']}/workshops",
            headers=admin_headers,
            json={"typ": "onboarding"},
        )
        r.raise_for_status()
        onboarding = r.json()

        r = await client.get(f"/api/v1/intern/leistungsscheine/{ls['id']}", headers=admin_headers)
        ls = r.json()
        assert ls["status_kunde"] == "onboarding_workshop", ls
        print("LS-Status nach Onboarding-Planung:", ls["status_kunde"])

        r = await client.patch(
            f"/api/v1/intern/leistungsscheine/{ls['id']}/workshops/{onboarding['id']}",
            headers=admin_headers,
            json={"status": "protokoll_freigegeben"},
        )
        r.raise_for_status()

        r = await client.get(f"/api/v1/intern/leistungsscheine/{ls['id']}", headers=admin_headers)
        ls = r.json()
        assert ls["status_kunde"] == "in_bearbeitung", ls
        print("LS-Status nach Workshop-Protokoll:", ls["status_kunde"])

        # 12. Rueckfrage an Kunden -> warten_auf_kunde
        r = await client.post(
            f"/api/v1/intern/leistungsscheine/{ls['id']}/kundenrueckfrage", headers=admin_headers
        )
        r.raise_for_status()
        assert r.json()["status_kunde"] == "warten_auf_kunde"
        print("LS-Status nach Kundenrueckfrage:", r.json()["status_kunde"])

        # 13. Leistung abschliessen -> fertiggestellt, Umfrage wird angelegt + versendet
        r = await client.post(f"/api/v1/intern/leistungsscheine/{ls['id']}/abschliessen", headers=admin_headers)
        r.raise_for_status()
        ls = r.json()
        assert ls["status_kunde"] == "kundenzufriedenheitsabfrage", ls
        print("LS-Status nach Abschluss:", ls["status_kunde"])

        r = await client.get("/api/v1/portal/umfragen", headers=kunde_headers)
        r.raise_for_status()
        umfragen = r.json()
        assert umfragen and umfragen[0]["status"] == "versendet", umfragen
        umfrage = umfragen[0]
        print("Umfrage versendet:", umfrage["id"])

        # 14. Kunde beantwortet Umfrage
        r = await client.post(
            f"/api/v1/portal/umfragen/{umfrage['id']}/beantworten",
            headers=kunde_headers,
            json={"bewertung": 5, "kommentar": "Sehr gut!"},
        )
        r.raise_for_status()
        assert r.json()["status"] == "beantwortet"
        print("Umfrage beantwortet")

        # 15. Monitoring-Uebersicht
        r = await client.get("/api/v1/intern/monitoring/uebersicht", headers=admin_headers)
        r.raise_for_status()
        print("Monitoring-Uebersicht:", r.json())

        print("\nE2E-Check erfolgreich abgeschlossen.")


if __name__ == "__main__":
    asyncio.run(main())
