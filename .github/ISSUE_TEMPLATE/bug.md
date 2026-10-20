---
name: Bug
about: Reproduzierbare Abweichung mit begrenztem Reparaturumfang dokumentieren
title: ""
labels: []
---

## Beobachtung / Erwartung

Aktueller Default-Branch/Commit, Eingabeart und konkretes falsches Verhalten.
Bestehende Issues/PRs und frühere Fixes vor Neuanlage abgleichen.

## Sichere Reproduktion

Kleine synthetische Fixture oder berechtigte, ausdrücklich bezeichnete Quelle;
keine Secretwerte, Originaltexte, privaten Hostpfade oder produktiven Schreibzugriffe.

## Ursache und Grenzen

Nachgewiesene Ursache von Hypothesen trennen. Raw/Parsed/Derived-Bezug,
Hashes/Provenienz und unbekannte Positionen erhalten. Kein stilles Fallback,
keine künstlichen Zeiten und keine Migration als ungeprüfter Workaround.

## Parent / Priorität / Abhängigkeiten

Parent Issue, Target milestone, Blocker und vollständige Cross-Repository-Links.

## Akzeptanz

- [ ] Gezielter Test reproduziert den Fehler und prüft die Korrektur.
- [ ] Betroffene bestehende Verträge bleiben geprüft, keine abgeschwächten Assertions.
- [ ] Grenzen, Skips und nötige Operatorentscheidungen dokumentiert.
- [ ] Merge ist keine automatische fachliche oder produktive Freigabe.
