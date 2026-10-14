# Kontrollierter Abruf der fehlenden Wochen-Fixtures

29 konkrete, zuvor aus den lokalen Indizes entdeckte URLs; höchstens drei Abrufe gleichzeitig,
je Abruf 25 Sekunden Timeout, keine automatischen Retries, keine rekursive Linkverfolgung.
Alle Abrufe lieferten HTTP 200; effektive und angeforderte URL waren identisch.
Nur HTML wurde gespeichert. SHA-256 der unveränderten Antwortdateien steht im Manifest
und in `six_course_fixture_provenance.md`. Keine Aussage zur Erreichbarkeit verlinkter CDN-Ressourcen.

| Fixture | Effektive offizielle URL | HTTP |
| --- | --- | --- |
| cs50x/week_2.html | https://cs50.harvard.edu/x/weeks/2/ | 200 |
| cs50x/week_3.html | https://cs50.harvard.edu/x/weeks/3/ | 200 |
| cs50x/week_4.html | https://cs50.harvard.edu/x/weeks/4/ | 200 |
| cs50x/week_5.html | https://cs50.harvard.edu/x/weeks/5/ | 200 |
| cs50x/week_6.html | https://cs50.harvard.edu/x/weeks/6/ | 200 |
| cs50x/week_7.html | https://cs50.harvard.edu/x/weeks/7/ | 200 |
| cs50x/week_ai.html | https://cs50.harvard.edu/x/weeks/ai/ | 200 |
| cs50x/week_8.html | https://cs50.harvard.edu/x/weeks/8/ | 200 |
| cs50x/week_9.html | https://cs50.harvard.edu/x/weeks/9/ | 200 |
| cs50x/week_10.html | https://cs50.harvard.edu/x/weeks/10/ | 200 |
| cs50_python/week_1.html | https://cs50.harvard.edu/python/weeks/1/ | 200 |
| cs50_python/week_2.html | https://cs50.harvard.edu/python/weeks/2/ | 200 |
| cs50_python/week_3.html | https://cs50.harvard.edu/python/weeks/3/ | 200 |
| cs50_python/week_4.html | https://cs50.harvard.edu/python/weeks/4/ | 200 |
| cs50_python/week_6.html | https://cs50.harvard.edu/python/weeks/6/ | 200 |
| cs50_python/week_7.html | https://cs50.harvard.edu/python/weeks/7/ | 200 |
| cs50_python/week_8.html | https://cs50.harvard.edu/python/weeks/8/ | 200 |
| cs50_python/week_9.html | https://cs50.harvard.edu/python/weeks/9/ | 200 |
| cs50_sql/week_1.html | https://cs50.harvard.edu/sql/weeks/1/ | 200 |
| cs50_sql/week_2.html | https://cs50.harvard.edu/sql/weeks/2/ | 200 |
| cs50_sql/week_3.html | https://cs50.harvard.edu/sql/weeks/3/ | 200 |
| cs50_sql/week_4.html | https://cs50.harvard.edu/sql/weeks/4/ | 200 |
| cs50_sql/week_5.html | https://cs50.harvard.edu/sql/weeks/5/ | 200 |
| cs50_ai/week_0.html | https://cs50.harvard.edu/ai/weeks/0/ | 200 |
| cs50_ai/week_2.html | https://cs50.harvard.edu/ai/weeks/2/ | 200 |
| cs50_ai/week_3.html | https://cs50.harvard.edu/ai/weeks/3/ | 200 |
| cs50_ai/week_4.html | https://cs50.harvard.edu/ai/weeks/4/ | 200 |
| cs50_ai/week_5.html | https://cs50.harvard.edu/ai/weeks/5/ | 200 |
| cs50_ai/week_6.html | https://cs50.harvard.edu/ai/weeks/6/ | 200 |
