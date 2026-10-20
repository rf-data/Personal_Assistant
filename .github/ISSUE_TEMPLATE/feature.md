---
name: Feature / technische Schulden
about: Überprüfbare Funktion oder begrenzte technische Verbesserung planen
title: ""
labels: []
---

## Ziel und Typ

Typ: feature oder debt. Welcher konkrete Nutzen / welche technische Lücke?
Bestehende Issues und PRs vor Neuanlage prüfen; keine parallele Implementierung.

## Scope und Wiederverwendung

Betroffenes Repository, vorhandene Modelle/Schnittstellen und begrenzter Umfang.
Raw / Parsed / optional Derived Knowledge unterscheiden. Keine Technologie als
beschlossen behandeln, bevor ein begründeter ADR vorliegt.

## Parent und Abhängigkeiten

Parent Issue, Target milestone und vollständige Cross-Repository-URLs.
Blocker, benötigte Entscheidungen und zuständige Person; keine erfundenen Nummern.

## Akzeptanz und Nachweise

- [ ] Beobachtbares Ergebnis und Fehlerfälle festgelegt.
- [ ] Technische Tests mit Daten-/Umgebungsbezug und Grenzen dokumentiert.
- [ ] Falls fachliche Aussagen: unabhängige Referenzen und Review festgelegt.
- [ ] Falls Betrieb: konkrete Operatorfreigabe separat, nicht durch Merge ersetzt.

## Grenzen und Pflege

Nichtziele, Daten-/Nutzungsrechte und nötige Freigaben. Keine Secrets oder
Originaltranskripte ins Issue. PRs als Nachweis verlinken; Parent nicht automatisch
schließen. Produktionsstatus bleibt getrennt vom Arbeitsstatus.
