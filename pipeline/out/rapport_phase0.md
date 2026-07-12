# Rapport phase 0 - Recensement Wikidata

Genere le 2026-07-11 20:13.

## Volumes par categorie et palier d'importance

Palier = nombre minimal de versions linguistiques (sitelinks) de l'article Wikipedia. T1 : visible des le globe entier ; T3 : visible en zoom rapproche.

| Categorie | T1 (>=100) | T2 (>=40) | T3 (palier bas) |
|---|---|---|---|
| Batailles et sieges | 0 | 101 | 1 112 |
| Guerres et conflits | 22 | 216 | 743 |
| Personnages (lieu et date de naissance) | timeout/erreur | timeout/erreur | timeout/erreur (>= 25) |
| Inventions et decouvertes (P575) | 206 | 1 849 | 23 663 |
| Oeuvres majeures (litterature, peinture, musique, cinema) | 44 | 2 277 | 17 009 |
| Traites et accords | 3 | 138 | 660 |
| Naissances d'Etats et d'entites politiques | 241 | 701 | 1 606 |
| Catastrophes (naturelles et humaines) | 4 | 140 | 988 |

**Total estime au palier bas : ~45 781 evenements** (hors categories en erreur).

Notes :
- *Personnages (lieu et date de naissance)* : palier bas releve a 25 sitelinks : ~12 M d'humains dans Wikidata, un seuil plus bas ferait exploser volume et temps de requete.
- *Inventions et decouvertes (P575)* : tout item portant une 'date de decouverte ou d'invention'.
- *Oeuvres majeures (litterature, peinture, musique, cinema)* : pas de coordonnees propres : seront rattachees au lieu de creation ou de naissance de l'auteur en phase 1.

## Echantillons (top sitelinks par categorie)

### Batailles et sieges

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| bataille de Waterloo (Q48314) | 1815 | oui | 93 |
| attaque de Pearl Harbor (Q52418) | 1941 | oui | 88 |
| bataille des Thermopyles (Q131969) | -479 | oui | 83 |
| bataille des Thermopyles (Q131969) | -479 | oui | 83 |
| bataille d'Hastings (Q83224) | 1066 | oui | 80 |
| bataille de Badr (Q486124) | 624 | oui | 80 |
| bataille de Trafalgar (Q171416) | 1805 | oui | 78 |
| bataille d'Angleterre (Q154720) | 1940 | oui | 77 |
| bataille de Marathon (Q31900) | -489 | oui | 75 |
| bataille d'Austerlitz (Q134114) | 1805 | oui | 75 |
| bataille de Koursk (Q130861) | 1943 | oui | 74 |
| bataille de Lépante (Q165425) | 1571 | oui | 71 |
| bataille de Grunwald (Q33570) | 1410 | oui | 68 |
| bataille de Poitiers (Q173077) | 732 | oui | 68 |
| bataille de Mohács (Q178510) | 1526 | oui | 67 |

Qualite sur l'echantillon : 25/25 geolocalises, 25/25 avec label lisible.

### Guerres et conflits

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| Seconde Guerre mondiale (Q362) | 1939 | - | 291 |
| Première Guerre mondiale (Q361) | 1914 | - | 263 |
| guerre froide (Q8683) | 1945 | - | 209 |
| invasion de l'Ukraine par la Russie (Q110999040) | 2022 | - | 173 |
| invasion de l'Ukraine par la Russie (Q110999040) | 2022 | - | 173 |
| invasion de l'Ukraine par la Russie (Q110999040) | 2022 | - | 173 |
| guerre de Sécession (Q8676) | 1865 | - | 168 |
| guerre de Sécession (Q8676) | 1861 | - | 168 |
| croisade (Q12546) | 1095 | - | 168 |
| croisade (Q12546) | 1095 | - | 168 |
| guerre du Viêt Nam (Q8740) | 1955 | - | 167 |
| guerre de Corée (Q8663) | 1950 | - | 142 |
| guerre de Trente Ans (Q2487) | 1618 | - | 133 |
| guerre d'Espagne (Q10859) | 1936 | - | 128 |
| guerre de Cent Ans (Q12551) | 1337 | - | 127 |

Qualite sur l'echantillon : 2/25 geolocalises, 25/25 avec label lisible.

### Personnages (lieu et date de naissance)

_ERREUR: echec apres 4 tentatives : 504 Server Error: Gateway Timeout for url: https://query.wikidata.org/sparql?query=%0ASELECT+%3Fitem+%3FitemLabel+%3Fdate+%3Fcoord+%3Fsl+WHERE+%7B%0A++%3Fitem+wdt%3AP31+wd%3AQ5+.%0A++%3Fitem+wdt%3AP569+%3Fdate+.%0A++FILTER%28%3Fdate+%3E%3D+%22-3000-01-01T00%3A00%3A00Z%22%5E%5Exsd%3AdateTime%29%0A++OPTIONAL+%7B+%3Fitem+wdt%3AP19+%3Flieu+.+%3Flieu+wdt%3AP625+%3Fcoord+.+%7D%0A++%3Fitem+wikibase%3Asitelinks+%3Fsl+.%0A++FILTER%28%3Fsl+%3E%3D+40%29%0A++SERVICE+wikibase%3Alabel+%7B+bd%3AserviceParam+wikibase%3Alanguage+%22fr%2Cen%22.+%7D%0A%7D%0AORDER+BY+DESC%28%3Fsl%29%0ALIMIT+25&format=json_

### Inventions et decouvertes (P575)

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| Brésil (Q155) | 1500 | - | 385 |
| Antarctique (Q51) | 1820 | - | 314 |
| football (Q2736) | 1863 | - | 296 |
| ordinateur (Q68) | 1945 | - | 295 |
| Amérique (Q828) | 1492 | - | 266 |
| Uranus (Q324) | 1781 | - | 259 |
| Groenland (Q223) | 875 | - | 254 |
| Neptune (Q332) | 1846 | - | 250 |
| Grenade (Q769) | 1498 | - | 249 |
| automobile (Q1420) | 1884 | - | 245 |
| hydrogène (Q556) | 1766 | oui | 236 |
| oxygène (Q629) | 1774 | oui | 233 |
| Covid-19 (Q84263196) | 2019 | oui | 226 |
| Pluton (Q339) | 1930 | - | 221 |
| carbone (Q623) | 1789 | - | 217 |

Qualite sur l'echantillon : 6/25 geolocalises, 25/25 avec label lisible.

### Oeuvres majeures (litterature, peinture, musique, cinema)

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| Coran (Q428) | 631 | - | 280 |
| Iliade (Q8275) | -800 | - | 178 |
| Évangile selon Luc (Q39939) | 85 | - | 148 |
| Le Petit Prince (Q25338) | 1943 | - | 148 |
| Le Petit Prince (Q25338) | 1943 | - | 148 |
| Don Quichotte (Q480) | 1605 | - | 147 |
| Don Quichotte (Q480) | 1615 | - | 147 |
| La Joconde (Q12418) | 1503 | - | 146 |
| Le Seigneur des anneaux (Q15228) | 1954 | - | 146 |
| Manifeste du Parti communiste (Q40591) | 1848 | - | 143 |
| Titanic (Q44578) | 1997 | - | 138 |
| 1984 (Q208460) | 1949 | - | 137 |
| 1984 (Q208460) | 1948 | - | 137 |
| Q134773 (Q134773) | 1994 | - | 136 |
| Q134773 (Q134773) | 1994 | - | 136 |

Qualite sur l'echantillon : 0/25 geolocalises, 20/25 avec label lisible.

### Traites et accords

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| traité de Versailles (Q8736) | 1919 | - | 135 |
| traité de Versailles (Q8736) | 1919 | - | 135 |
| Charte des Nations unies (Q171328) | 1945 | oui | 111 |
| Charte des Nations unies (Q171328) | 1945 | oui | 111 |
| Pacte germano-soviétique (Q130796) | 1939 | - | 105 |
| Pacte germano-soviétique (Q130796) | 1939 | - | 105 |
| Pacte germano-soviétique (Q130796) | 1939 | - | 105 |
| Pacte germano-soviétique (Q130796) | 1939 | - | 105 |
| congrès de Vienne (Q46362) | 1815 | oui | 98 |
| protocole de Kyoto (Q47359) | 1997 | - | 93 |
| Convention relative aux droits de l'enfant (Q466087) | 1989 | - | 92 |
| Convention relative aux droits de l'enfant (Q466087) | 1989 | - | 92 |
| Convention relative aux droits de l'enfant (Q466087) | 1989 | - | 92 |
| Convention relative aux droits de l'enfant (Q466087) | 1989 | - | 92 |
| Convention relative aux droits de l'enfant (Q466087) | 1989 | - | 92 |

Qualite sur l'echantillon : 8/25 geolocalises, 25/25 avec label lisible.

### Naissances d'Etats et d'entites politiques

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| États-Unis (Q30) | 1784 | oui | 424 |
| États-Unis (Q30) | 1784 | oui | 424 |
| Turquie (Q43) | 1923 | oui | 419 |
| Turquie (Q43) | 1923 | oui | 419 |
| Russie (Q159) | 1263 | oui | 418 |
| Russie (Q159) | 1263 | oui | 418 |
| France (Q142) | 481 | oui | 416 |
| France (Q142) | 843 | oui | 416 |
| France (Q142) | 1804 | oui | 416 |
| France (Q142) | 481 | oui | 416 |
| France (Q142) | 843 | oui | 416 |
| France (Q142) | 1804 | oui | 416 |
| Japon (Q17) | 1947 | oui | 415 |
| Japon (Q17) | 1947 | oui | 415 |
| Italie (Q38) | 476 | oui | 406 |

Qualite sur l'echantillon : 25/25 geolocalises, 25/25 avec label lisible.

### Catastrophes (naturelles et humaines)

| Item | Annee | Coordonnees | Sitelinks |
|---|---|---|---|
| attentats du 11 septembre 2001 (Q10806) | 2001 | - | 167 |
| attentats du 11 septembre 2001 (Q10806) | 2001 | - | 167 |
| attentats du 11 septembre 2001 (Q10806) | 2001 | - | 167 |
| génocide arménien (Q80034) | 1915 | - | 125 |
| catastrophe nucléaire de Tchernobyl (Q486) | 1986 | oui | 125 |
| catastrophe nucléaire de Tchernobyl (Q486) | 1986 | oui | 125 |
| attentats du 13 novembre 2015 en Île-de-France (Q21479779) | 2015 | oui | 101 |
| séisme de 2011 de la côte Pacifique du Tōhoku (Q36204) | 2011 | oui | 92 |
| séisme de 2011 de la côte Pacifique du Tōhoku (Q36204) | 2011 | oui | 92 |
| séisme de 2011 de la côte Pacifique du Tōhoku (Q36204) | 2011 | oui | 92 |
| séisme de 2011 de la côte Pacifique du Tōhoku (Q36204) | 2011 | oui | 92 |
| séisme de 2011 de la côte Pacifique du Tōhoku (Q36204) | 2011 | oui | 92 |
| séismes de 2023 en Turquie et Syrie (Q116691303) | 2023 | oui | 90 |
| manifestations de la place Tian'anmen (Q99717) | 1989 | oui | 89 |
| attentats de 2011 en Norvège (Q79967) | 2011 | - | 87 |

Qualite sur l'echantillon : 18/25 geolocalises, 25/25 avec label lisible.
