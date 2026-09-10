"""
Zentraler Test-Runner für die Testumgebung des Datenübertragungs-Agenten.
Führt Pipeline und 100%-Verifikation aus.
"""
import os
import sys

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_test_env import setup_test_database
from transmission_agent.pipeline import TransmissionPipeline
from audit.verifier import run_verification_audit

def main():
    print("=" * 60)
    print("🚀 STARTE TESTUMGEBUNG FÜR DATENÜBERTRAGUNGS-AGENT")
    print("=" * 60)
    
    # Schritt 1: Isolierte Test-DB initialisieren
    print("\n[Schritt 1/3] Initialisiere isolierte Test-Datenbank...")
    setup_test_database()
    
    # Schritt 2: Agenten-Pipeline auf Spieltage_Pics ausführen
    print("\n[Schritt 2/3] Führe Übertragungs-Agenten auf 'Spieltage_Pics' aus...")
    pics_dir = os.path.join(BASE_DIR, "..", "Spieltage_Pics", "Spieltag 2 A Team")
    agent = TransmissionPipeline(pics_dir)
    ingest_res = agent.run_ingestion()
    print(f"✅ Ingestion erfolgreich: {ingest_res['matches_processed']} Matches verarbeitet.")
    print(f"   - {ingest_res['created_counts']['singles']} Einzel in 'matches'")
    print(f"   - {ingest_res['created_counts']['doubles']} Doppel in 'doubles_matches'")
    print(f"   - {ingest_res['created_counts']['analytics']} Spiele in 'analytics_matches'")
    
    # Schritt 3: 100%-Verifikations-Audit gegen Ground Truth ausführen
    print("\n[Schritt 3/3] Starte 100%-Feld-Audit gegen Ground-Truth-Referenz...")
    audit_res = run_verification_audit()
    
    print("\n" + "=" * 60)
    print("📋 AUDIT-ERGEBNIS:")
    print(f"   Geprüfte Datenfelder: {audit_res['total_checks']}")
    print(f"   Exakte Treffer:       {audit_res['passed_checks']}")
    print(f"   Abweichungen:         {audit_res['failed_checks']}")
    print(f"   Übereinstimmung:      {audit_res['accuracy_rate']:.2f}%")
    print("=" * 60)
    
    if audit_res['failed_checks'] == 0:
        print("\n🎉 TEST BESTANDEN: 100.00% NACHWEIS ERBRACHT!")
    else:
        print(f"\n⚠️ TEST FEHLGESCHLAGEN: {audit_res['failed_checks']} Differenzen gefunden.")
        sys.exit(1)

if __name__ == "__main__":
    main()
