# RAPPORT DE PROJET DE FIN D'ÉTUDES

**École Nationale d'Électronique et des Télécommunications de Sfax**  
**Diplôme National d'Ingénieur en Génie Systèmes Électroniques et Communication**  
**Option : Systèmes Embarqués**

---

## TITRE DU PROJET

# SmartMaintain : Plateforme IoT de Maintenance Prédictive Temps Réel Basée sur l'Intelligence Artificielle

---

**Présenté par** : Mohamed Sadok  
**Encadrant académique** : [Nom de l'encadrant]  
**Encadrant entreprise** : [Nom si applicable]  
**Année universitaire** : 2025-2026

---

## DÉDICACE

À mes chers parents,  
Pour leur soutien inconditionnel et leurs encouragements tout au long de mon parcours académique.

À mes professeurs,  
Pour leur dévouement et leurs précieux enseignements.

À tous ceux qui ont contribué de près ou de loin à la réalisation de ce projet.

Je dédie ce travail.

Mohamed Sadok

---

## REMERCIEMENTS

Je tiens à exprimer ma profonde gratitude à toutes les personnes qui ont contribué à la réalisation de ce projet de fin d'études.

Je remercie particulièrement **[Nom de l'encadrant académique]**, mon encadrant académique, pour son soutien constant, ses conseils avisés et sa disponibilité tout au long de ce projet. Ses orientations m'ont permis de surmonter les difficultés rencontrées et d'approfondir mes compétences techniques.

Mes remerciements vont également aux membres du jury pour avoir accepté d'évaluer ce travail et pour le temps qu'ils ont consacré à l'examen de ce rapport.

Je remercie l'ensemble du corps professoral de l'ENET'COM pour la qualité de la formation dispensée durant ces années d'études, qui m'a permis d'acquérir les connaissances nécessaires pour mener à bien ce projet.

Enfin, je remercie ma famille et mes amis pour leur patience, leur soutien moral et leurs encouragements durant toute la période de réalisation de ce projet.

---

## RÉSUMÉ

La maintenance industrielle représente un enjeu majeur pour les entreprises modernes, avec des coûts de maintenance imprévue pouvant atteindre jusqu'à 50% du budget opérationnel. Les approches traditionnelles de maintenance corrective et préventive ne permettent pas d'optimiser efficacement les interventions ni de minimiser les temps d'arrêt non planifiés.

Ce projet présente **SmartMaintain**, une plateforme innovante de maintenance prédictive temps réel basée sur l'intelligence artificielle et l'Internet des Objets (IoT). Le système intègre des capteurs IoT pour collecter en temps réel les données vibratoires, thermiques et électriques de quatre types d'équipements industriels critiques : moteurs électriques, pompes centrifuges, compresseurs d'air et échangeurs thermiques.

Notre solution repose sur une architecture microservices moderne comprenant huit services spécialisés : ingestion IoT, traitement ML, gestion des alertes, authentification, API Gateway et interfaces utilisateur. Les modèles d'apprentissage automatique développés (Random Forest et Extra Trees) permettent de détecter huit types de défauts différents avec une précision globale de 98-100% sur les données d'entraînement et 92-100% sur données bruitées.

Le système a été entièrement refactorisé vers une architecture V7 simplifiée, éliminant 35% du code legacy tout en maintenant toutes les fonctionnalités. La plateforme offre une interface web intuitive permettant la surveillance temps réel, la visualisation des tendances, la gestion des alertes et la maintenance basée sur les prédictions.

Les tests d'intégration complets (5/5 réussis) démontrent la fiabilité du système. SmartMaintain représente une solution complète et opérationnelle pour transformer la maintenance réactive en maintenance prédictive intelligente, réduisant les coûts et optimisant la disponibilité des équipements industriels.

**Mots clés** : Maintenance prédictive, Intelligence artificielle, IoT, Machine Learning, Industrie 4.0, Microservices, Temps réel, Random Forest, Détection d'anomalies

---

## ABSTRACT

Industrial maintenance represents a major challenge for modern companies, with unplanned maintenance costs reaching up to 50% of the operational budget. Traditional corrective and preventive maintenance approaches fail to optimize interventions effectively or minimize unplanned downtime.

This project presents **SmartMaintain**, an innovative real-time predictive maintenance platform based on artificial intelligence and the Internet of Things (IoT). The system integrates IoT sensors to collect real-time vibratory, thermal, and electrical data from four types of critical industrial equipment: electric motors, centrifugal pumps, air compressors, and heat exchangers.

Our solution relies on a modern microservices architecture comprising eight specialized services: IoT ingestion, ML processing, alert management, authentication, API Gateway, and user interfaces. The developed machine learning models (Random Forest and Extra Trees) detect eight different fault types with an overall accuracy of 98-100% on training data and 92-100% on noisy data.

The system has been completely refactored to a simplified V7 architecture, eliminating 35% of legacy code while maintaining all functionalities. The platform offers an intuitive web interface enabling real-time monitoring, trend visualization, alert management, and prediction-based maintenance.

Comprehensive integration tests (5/5 passed) demonstrate system reliability. SmartMaintain represents a complete and operational solution to transform reactive maintenance into intelligent predictive maintenance, reducing costs and optimizing industrial equipment availability.

**Keywords**: Predictive maintenance, Artificial intelligence, IoT, Machine Learning, Industry 4.0, Microservices, Real-time, Random Forest, Anomaly detection

---

## TABLE DES MATIÈRES

**LISTE DES FIGURES** ................................................ viii  
**LISTE DES TABLEAUX** .............................................. ix  
**LISTE DES ABRÉVIATIONS** .......................................... x

**INTRODUCTION GÉNÉRALE** ........................................... 1

---

## LISTE DES FIGURES

**Figure 1.1** : Évolution des stratégies de maintenance ................. 7  
**Figure 1.2** : Architecture IoT pour la maintenance prédictive ........ 9  
**Figure 1.3** : Comparaison des techniques ML pour la prédiction ....... 11  
**Figure 2.1** : Architecture microservices SmartMaintain ............... 18  
**Figure 2.2** : Diagramme de cas d'utilisation ......................... 25  
**Figure 2.3** : Diagramme de séquence - Prédiction temps réel .......... 27  
**Figure 2.4** : Diagramme de classes - Modèles ML ...................... 28  
**Figure 3.1** : Distribution des classes par équipement ................ 32  
**Figure 3.2** : Matrice de confusion - Moteur électrique ............... 39  
**Figure 3.3** : Matrice de confusion - Pompe centrifuge ................ 41  
**Figure 3.4** : Matrice de confusion - Compresseur d'air ............... 43  
**Figure 3.5** : Matrice de confusion - Échangeur thermique ............. 45  
**Figure 3.6** : Courbes ROC pour les 4 équipements ..................... 47  
**Figure 4.1** : Pipeline de traitement des données ..................... 58  
**Figure 4.2** : Dashboard de surveillance temps réel ................... 62  
**Figure 4.3** : Interface de gestion des alertes ....................... 63  
**Figure 5.1** : Résultats des tests d'intégration ...................... 75  
**Figure 5.2** : Graphique de performance - Latence ..................... 77  
**Figure 6.1** : Architecture avant/après refactorisation V7 ............ 88  
**Figure 6.2** : Réduction de la complexité cyclomatique ................ 90

---

## LISTE DES TABLEAUX

**Tableau 1.1** : Comparaison des types de maintenance .................. 8  
**Tableau 1.2** : Solutions commerciales de maintenance prédictive ...... 10  
**Tableau 2.1** : Besoins fonctionnels du système ....................... 15  
**Tableau 2.2** : Technologies utilisées par service .................... 24  
**Tableau 3.1** : Caractéristiques des datasets par équipement .......... 31  
**Tableau 3.2** : Hyperparamètres optimaux Random Forest ................ 36  
**Tableau 3.3** : Performances des modèles V7 ........................... 46  
**Tableau 3.4** : Robustesse au bruit (données bruitées 10%) ............ 48  
**Tableau 4.1** : API endpoints par service ............................. 57  
**Tableau 4.2** : Configuration Docker des services ..................... 68  
**Tableau 5.1** : Résultats des tests unitaires ......................... 73  
**Tableau 5.2** : Résultats des tests d'intégration ..................... 76  
**Tableau 5.3** : Métriques de performance système ...................... 78  
**Tableau 6.1** : Comparaison V6 vs V7 - Métriques de code .............. 90  
**Tableau 6.2** : Gains de performance après refactorisation ............ 91

---

## LISTE DES ABRÉVIATIONS

**AI** : Artificial Intelligence (Intelligence Artificielle)  
**API** : Application Programming Interface  
**CNN** : Convolutional Neural Network  
**CORS** : Cross-Origin Resource Sharing  
**CPU** : Central Processing Unit  
**CSV** : Comma-Separated Values  
**CWRU** : Case Western Reserve University  
**DB** : Database (Base de données)  
**DL** : Deep Learning (Apprentissage Profond)  
**Docker** : Plateforme de conteneurisation  
**FFT** : Fast Fourier Transform (Transformée de Fourier Rapide)  
**Flask** : Framework web Python  
**GB** : Gigabyte  
**HTTP** : Hypertext Transfer Protocol  
**IoT** : Internet of Things (Internet des Objets)  
**JSON** : JavaScript Object Notation  
**JWT** : JSON Web Token  
**KNN** : K-Nearest Neighbors  
**ML** : Machine Learning (Apprentissage Automatique)  
**MTBF** : Mean Time Between Failures  
**OEE** : Overall Equipment Effectiveness  
**RAM** : Random Access Memory  
**React** : Bibliothèque JavaScript pour interfaces utilisateur  
**Redis** : Base de données en mémoire  
**REST** : Representational State Transfer  
**RF** : Random Forest  
**RMS** : Root Mean Square  
**RUL** : Remaining Useful Life  
**SQL** : Structured Query Language  
**SVM** : Support Vector Machine  
**UML** : Unified Modeling Language  
**URL** : Uniform Resource Locator  
**VM** : Virtual Machine  
**YAML** : Yet Another Markup Language

---

## INTRODUCTION GÉNÉRALE

### CHAPITRE 1 : CONTEXTE ET ÉTAT DE L'ART

1.1 Introduction ....................................................... 4  
1.2 Contexte du projet ................................................. 4  
   1.2.1 Problématique de la maintenance industrielle ................. 4  
   1.2.2 Évolution vers l'Industrie 4.0 ............................... 5  
   1.2.3 Enjeux de la maintenance prédictive .......................... 6  
1.3 État de l'art ...................................................... 7  
   1.3.1 Maintenance corrective et préventive ......................... 7  
   1.3.2 Techniques de maintenance prédictive ......................... 8  
   1.3.3 Apprentissage automatique pour la maintenance ................ 9  
   1.3.4 Solutions existantes ......................................... 10  
1.4 Objectifs du projet ................................................ 12  
1.5 Conclusion ......................................................... 13

### CHAPITRE 2 : ANALYSE ET CONCEPTION

2.1 Introduction ....................................................... 14  
2.2 Analyse des besoins ................................................ 14  
   2.2.1 Besoins fonctionnels ......................................... 14  
   2.2.2 Besoins non fonctionnels ..................................... 15  
   2.2.3 Acteurs du système ........................................... 16  
2.3 Conception de l'architecture ....................................... 17  
   2.3.1 Architecture microservices ................................... 17  
   2.3.2 Architecture des données ..................................... 19  
   2.3.3 Architecture ML .............................................. 20  
2.4 Choix technologiques ............................................... 22  
   2.4.1 Backend et services .......................................... 22  
   2.4.2 Frontend ..................................................... 23  
   2.4.3 Machine Learning ............................................. 23  
   2.4.4 Infrastructure et déploiement ................................ 24  
2.5 Modélisation UML ................................................... 25  
   2.5.1 Diagramme de cas d'utilisation ............................... 25  
   2.5.2 Diagrammes de séquence ....................................... 26  
   2.5.3 Diagramme de classes ......................................... 28  
2.6 Conclusion ......................................................... 29

### CHAPITRE 3 : DÉVELOPPEMENT DES MODÈLES ML

3.1 Introduction ....................................................... 30  
3.2 Données et prétraitement ........................................... 30  
   3.2.1 Sources de données ........................................... 30  
   3.2.2 Exploration des données ...................................... 31  
   3.2.3 Prétraitement et feature engineering ......................... 33  
3.3 Sélection et entraînement des modèles .............................. 35  
   3.3.1 Algorithmes testés ........................................... 35  
   3.3.2 Hyperparamètres et optimisation .............................. 36  
   3.3.3 Validation croisée ........................................... 37  
3.4 Modèles par équipement ............................................. 38  
   3.4.1 Modèle Moteur électrique ..................................... 38  
   3.4.2 Modèle Pompe centrifuge ...................................... 40  
   3.4.3 Modèle Compresseur d'air ..................................... 42  
   3.4.4 Modèle Échangeur thermique ................................... 44  
3.5 Évaluation des performances ........................................ 46  
   3.5.1 Métriques d'évaluation ....................................... 46  
   3.5.2 Matrices de confusion ........................................ 47  
   3.5.3 Robustesse au bruit .......................................... 48  
3.6 Conclusion ......................................................... 49

### CHAPITRE 4 : IMPLÉMENTATION DE LA PLATEFORME

4.1 Introduction ....................................................... 50  
4.2 Architecture microservices ......................................... 50  
   4.2.1 Service IoT .................................................. 50  
   4.2.2 Service ML ................................................... 52  
   4.2.3 Service Alertes .............................................. 54  
   4.2.4 Service Auth ................................................. 55  
   4.2.5 API Gateway .................................................. 56  
4.3 Pipeline de données ................................................ 58  
   4.3.1 Ingestion temps réel ......................................... 58  
   4.3.2 Traitement et prédiction ..................................... 59  
   4.3.3 Génération d'alertes ......................................... 60  
4.4 Interface utilisateur .............................................. 61  
   4.4.1 Dashboard de surveillance .................................... 61  
   4.4.2 Visualisation temps réel ..................................... 62  
   4.4.3 Gestion des alertes .......................................... 63  
   4.4.4 Rapports et historiques ...................................... 64  
4.5 Sécurité et authentification ....................................... 65  
   4.5.1 Authentification JWT ......................................... 65  
   4.5.2 Gestion des rôles ............................................ 66  
   4.5.3 Sécurisation des API ......................................... 66  
4.6 Déploiement Docker ................................................. 67  
   4.6.1 Containerisation ............................................. 67  
   4.6.2 Orchestration docker-compose ................................. 68  
   4.6.3 Configuration réseau ......................................... 69  
4.7 Conclusion ......................................................... 70

### CHAPITRE 5 : TESTS ET VALIDATION

5.1 Introduction ....................................................... 71  
5.2 Stratégie de tests ................................................. 71  
5.3 Tests unitaires .................................................... 72  
   5.3.1 Tests des services backend ................................... 72  
   5.3.2 Tests des modèles ML ......................................... 73  
5.4 Tests d'intégration ................................................ 74  
   5.4.1 Tests du pipeline complet .................................... 74  
   5.4.2 Tests des APIs ............................................... 75  
   5.4.3 Tests de communication inter-services ........................ 76  
5.5 Tests de performance ............................................... 77  
   5.5.1 Latence de prédiction ........................................ 77  
   5.5.2 Débit de données ............................................. 78  
   5.5.3 Utilisation des ressources ................................... 78  
5.6 Résultats et validation ............................................ 79  
   5.6.1 Validation ML ................................................ 79  
   5.6.2 Validation fonctionnelle ..................................... 80  
   5.6.3 Scénarios de test utilisateur ................................ 81  
5.7 Conclusion ......................................................... 82

### CHAPITRE 6 : REFACTORISATION V7

6.1 Introduction ....................................................... 83  
6.2 Motivations de la refactorisation .................................. 83  
6.3 Processus de refactorisation ....................................... 84  
   6.3.1 Audit du code existant ....................................... 84  
   6.3.2 Planification ................................................ 85  
   6.3.3 Exécution .................................................... 86  
6.4 Améliorations apportées ............................................ 87  
   6.4.1 Simplification de l'architecture ............................. 87  
   6.4.2 Unification des services ..................................... 88  
   6.4.3 Optimisation du code ......................................... 89  
6.5 Résultats de la refactorisation .................................... 90  
   6.5.1 Métriques de code ............................................ 90  
   6.5.2 Performance .................................................. 91  
   6.5.3 Maintenabilité ............................................... 91  
6.6 Conclusion ......................................................... 92

**CONCLUSION GÉNÉRALE ET PERSPECTIVES** ............................. 93

**BIBLIOGRAPHIE** ................................................... 95

**ANNEXES** .......................................................... 97  
A. Diagrammes UML complémentaires ..................................... 98  
B. Code source clé .................................................... 102  
C. Documentation technique ............................................ 106  
D. Résultats détaillés des tests ...................................... 110

---



### Contexte Général

Dans un contexte industriel en constante évolution, marqué par l'avènement de l'Industrie 4.0, la maintenance des équipements industriels représente un enjeu stratégique majeur pour les entreprises. Les arrêts non planifiés et les pannes imprévues engendrent des pertes financières considérables, estimées entre 5% et 20% de la capacité de production totale. Les coûts de maintenance imprévue peuvent atteindre jusqu'à 50% du budget opérationnel d'une usine, sans compter les impacts sur la qualité de production et la sécurité des opérateurs.

Les approches traditionnelles de maintenance, qu'elles soient correctives (intervention après panne) ou préventives (maintenance systématique planifiée), présentent des limitations importantes. La maintenance corrective entraîne des temps d'arrêt prolongés et imprévisibles, tandis que la maintenance préventive, bien que planifiée, conduit souvent au remplacement prématuré de composants encore fonctionnels, générant des coûts superflus.

Face à ces défis, la maintenance prédictive émerge comme une solution innovante permettant d'anticiper les défaillances avant qu'elles ne surviennent, en s'appuyant sur l'analyse continue des données de fonctionnement des équipements. Cette approche proactive, rendue possible par les avancées en intelligence artificielle et l'Internet des Objets (IoT), permet d'optimiser les interventions de maintenance en les déclenchant uniquement lorsque nécessaire, sur la base d'indicateurs précis de dégradation.

### Problématique

Comment développer une plateforme IoT intelligente capable de détecter et prédire en temps réel les défaillances de différents types d'équipements industriels critiques, tout en garantissant une architecture évolutive, performante et facile à maintenir ?

Cette problématique soulève plusieurs défis techniques :
- **Hétérogénéité des équipements** : Les moteurs électriques, pompes, compresseurs et échangeurs thermiques présentent des modes de défaillance différents nécessitant des approches de modélisation spécifiques.
- **Traitement temps réel** : La détection précoce nécessite un traitement continu et rapide des flux de données capteurs avec des latences minimales.
- **Précision des prédictions** : Les modèles doivent atteindre une précision suffisante pour éviter les fausses alertes tout en ne manquant aucune défaillance critique.
- **Architecture évolutive** : Le système doit supporter l'ajout de nouveaux équipements et de nouveaux types de défauts sans refonte complète.
- **Maintenabilité du code** : L'architecture logicielle doit rester simple et compréhensible pour faciliter les évolutions futures.

### Objectifs du Projet

L'objectif principal de ce projet est de concevoir et développer **SmartMaintain**, une plateforme complète de maintenance prédictive répondant aux enjeux industriels actuels. Cette plateforme vise à :

1. **Collecter en temps réel** les données de fonctionnement de quatre types d'équipements industriels critiques via des capteurs IoT (vibrations, température, pression, débit).

2. **Détecter automatiquement** huit types de défauts différents avec une précision supérieure à 95% sur données réelles :
   - Moteurs : dégradation de roulement, déséquilibre/désalignement
   - Pompes : cavitation, fuite de joints
   - Compresseurs : fuite d'air, surchauffe
   - Échangeurs thermiques : encrassement, fuite thermique

3. **Générer des alertes intelligentes** en temps réel pour permettre des interventions préventives ciblées avant la panne.

4. **Fournir une interface intuitive** pour la surveillance continue, la visualisation des tendances et la gestion des interventions de maintenance.

5. **Garantir une architecture moderne** basée sur des microservices containerisés pour assurer l'évolutivité, la résilience et la facilité de déploiement.

6. **Simplifier le code** par une refactorisation complète (V7) éliminant les redondances et réduisant la complexité de 35%.

### Méthodologie

Pour atteindre ces objectifs, nous avons adopté une méthodologie de développement itérative en plusieurs phases :

**Phase 1 - Analyse et Conception** : Étude de l'état de l'art, identification des besoins fonctionnels et non-fonctionnels, conception de l'architecture microservices et choix des technologies adaptées.

**Phase 2 - Développement ML** : Collecte et prétraitement des données, sélection des algorithmes (Random Forest, Extra Trees), entraînement de quatre modèles spécialisés, validation croisée et optimisation des hyperparamètres.

**Phase 3 - Implémentation** : Développement de huit microservices (IoT, ML, Alertes, Auth, Gateway, Frontend, bases de données), mise en place du pipeline de données temps réel, développement de l'interface utilisateur, containerisation Docker.

**Phase 4 - Tests et Validation** : Élaboration d'une stratégie de tests complète (unitaires, intégration, performance), validation fonctionnelle du système complet, tests de robustesse avec données bruitées.

**Phase 5 - Refactorisation V7** : Audit du code existant, planification de la simplification, exécution de la refactorisation, validation de la non-régression, documentation des améliorations.

### Contributions

Ce projet apporte plusieurs contributions significatives :

1. **Architecture microservices complète** pour la maintenance prédictive industrielle avec séparation claire des responsabilités.

2. **Quatre modèles ML spécialisés** atteignant 98-100% de précision sur données d'entraînement et 92-100% sur données bruitées.

3. **Pipeline temps réel** complet de l'ingestion IoT à la visualisation, avec latence inférieure à 200ms.

4. **Refactorisation majeure** (V7) réduisant la complexité de 35% tout en maintenant toutes les fonctionnalités.

5. **Documentation technique complète** facilitant la maintenance et l'évolution du système.

6. **Solution opérationnelle** prête pour déploiement industriel avec tests d'intégration complets (5/5 réussis).

### Organisation du Rapport

Ce rapport est organisé en six chapitres détaillant l'ensemble du projet :

**Chapitre 1** présente le contexte industriel, l'état de l'art des techniques de maintenance prédictive et les objectifs détaillés du projet.

**Chapitre 2** expose l'analyse des besoins, la conception de l'architecture microservices, les choix technologiques et la modélisation UML du système.

**Chapitre 3** décrit le développement des modèles d'apprentissage automatique, le prétraitement des données, l'entraînement des quatre modèles spécialisés et l'évaluation des performances.

**Chapitre 4** détaille l'implémentation de la plateforme, les huit microservices, le pipeline de données, l'interface utilisateur, la sécurité et le déploiement Docker.

**Chapitre 5** présente la stratégie de tests, les résultats des tests unitaires et d'intégration, les tests de performance et la validation fonctionnelle complète.

**Chapitre 6** explique la refactorisation V7, les motivations, le processus suivi, les améliorations apportées et les bénéfices obtenus.

Enfin, la **conclusion générale** synthétise les résultats obtenus et propose des perspectives d'évolution pour le système SmartMaintain.

---



# CHAPITRE 1 : CONTEXTE ET ÉTAT DE L'ART

## 1.1 Introduction

La maintenance industrielle a connu une évolution majeure au cours des dernières décennies, passant d'une approche réactive à des stratégies de plus en plus proactives. Dans ce chapitre, nous explorons le contexte industriel actuel, les problématiques liées à la maintenance des équipements, et l'état de l'art des technologies et méthodes de maintenance prédictive. Nous présentons également un panorama des solutions existantes avant de définir précisément les objectifs de notre projet SmartMaintain.

## 1.2 Contexte du projet

### 1.2.1 Problématique de la maintenance industrielle

La maintenance des équipements industriels représente un enjeu économique considérable pour les entreprises. Les statistiques industrielles révèlent que :

- **Les arrêts non planifiés** coûtent en moyenne 260 000 $ par heure aux grandes industries
- **Les coûts de maintenance** représentent 15% à 40% du coût total de production
- **Les pannes imprévues** réduisent l'efficacité globale des équipements (OEE) de 5% à 20%
- **Le gaspillage** lié à la maintenance préventive systématique atteint 25% à 30% des budgets

Les équipements industriels critiques tels que les moteurs électriques, les pompes centrifuges, les compresseurs et les échangeurs thermiques sont particulièrement vulnérables à divers types de défaillances :

**Moteurs électriques** : Les défaillances de roulements représentent 40% des pannes, suivies par les problèmes de déséquilibre et de désalignement (30%). Ces défaillances se manifestent par des signatures vibratoires caractéristiques détectables avant la panne.

**Pompes centrifuges** : La cavitation (formation de bulles de vapeur causant des dommages mécaniques) et les fuites de joints constituent les modes de défaillance principaux. La détection précoce est cruciale pour éviter des dommages coûteux.

**Compresseurs d'air** : Les fuites d'air et la surchauffe sont les problèmes les plus fréquents, entraînant une surconsommation énergétique et des risques de panne totale.

**Échangeurs thermiques** : L'encrassement progressif réduit l'efficacité thermique tandis que les fuites thermiques compromettent les performances du système.

### 1.2.2 Évolution vers l'Industrie 4.0

L'Industrie 4.0, également appelée quatrième révolution industrielle, se caractérise par l'intégration massive des technologies numériques dans les processus de production. Cette transformation repose sur quatre piliers technologiques :

**Internet des Objets Industriel (IIoT)** : La généralisation des capteurs connectés permet une collecte continue et massive de données de fonctionnement des équipements. Les capteurs modernes mesurent avec précision les vibrations, températures, pressions, débits et consommations énergétiques.

**Big Data et Analytics** : Les volumes de données générés par les capteurs IoT nécessitent des infrastructures de traitement et de stockage adaptées. Les technologies de streaming temps réel (Redis, Kafka) permettent le traitement immédiat des flux de données.

**Intelligence Artificielle et Machine Learning** : Les algorithmes d'apprentissage automatique exploitent les données historiques pour identifier des patterns de défaillance et prédire les pannes futures. Les modèles entraînés atteignent aujourd'hui des précisions supérieures à 95%.

**Cloud et Edge Computing** : L'architecture hybride combine traitement local (edge) pour la réactivité et traitement cloud pour les analyses complexes. Les microservices containerisés (Docker, Kubernetes) facilitent le déploiement et la scalabilité.

Cette convergence technologique rend possible la maintenance prédictive à grande échelle, transformant radicalement les stratégies de maintenance industrielle.

### 1.2.3 Enjeux de la maintenance prédictive

La maintenance prédictive répond à plusieurs enjeux stratégiques majeurs :

**Enjeux économiques** :
- Réduction de 25% à 30% des coûts de maintenance
- Diminution de 70% des pannes imprévues
- Augmentation de 10% à 15% de la disponibilité des équipements
- Optimisation des stocks de pièces de rechange

**Enjeux opérationnels** :
- Planification optimale des interventions de maintenance
- Réduction des temps d'arrêt de 35% à 45%
- Amélioration de l'OEE (Overall Equipment Effectiveness)
- Priorisation des interventions selon la criticité

**Enjeux environnementaux** :
- Réduction de la consommation énergétique par détection précoce des dérives
- Diminution du gaspillage par remplacement prématuré de composants
- Optimisation de l'utilisation des ressources
- Conformité aux normes environnementales

**Enjeux de sécurité** :
- Prévention des accidents liés aux défaillances catastrophiques
- Protection des opérateurs et de l'environnement
- Conformité aux réglementations de sécurité industrielle
- Amélioration de la fiabilité globale des installations

## 1.3 État de l'art

### 1.3.1 Maintenance corrective et préventive

L'évolution des stratégies de maintenance suit une progression historique claire :

**Maintenance corrective** (années 1950-1970) : Intervention uniquement après panne. Cette approche "Run-to-Failure" minimise les coûts de maintenance programmée mais maximise les temps d'arrêt imprévus et les coûts de réparation d'urgence. Encore utilisée pour les équipements non critiques à faible coût de remplacement.

**Maintenance préventive systématique** (années 1970-1990) : Interventions planifiées selon un calendrier fixe (heures de fonctionnement, cycles, temps). Cette approche réduit les pannes imprévues mais conduit au remplacement prématuré de composants fonctionnels. Efficace pour les équipements à usure prévisible.

**Maintenance conditionnelle** (années 1990-2010) : Interventions basées sur l'état réel de l'équipement mesuré par des inspections périodiques. Nécessite des outils de diagnostic (analyseurs de vibration, caméras thermiques) et des opérateurs formés. Améliore l'optimisation mais reste réactive.

Le tableau suivant compare ces trois approches :

| Critère | Corrective | Préventive | Conditionnelle |
|---------|-----------|------------|----------------|
| **Déclenchement** | Après panne | Calendrier fixe | Mesures périodiques |
| **Coût maintenance** | Faible planifié | Moyen | Moyen-élevé |
| **Coût panne** | Très élevé | Faible | Très faible |
| **Disponibilité** | 60-75% | 75-85% | 85-92% |
| **Gaspillage** | Faible | Élevé (25-30%) | Faible |
| **Prévisibilité** | Nulle | Totale | Moyenne |
| **Complexité** | Faible | Faible | Moyenne |

### 1.3.2 Techniques de maintenance prédictive

La maintenance prédictive moderne s'appuie sur plusieurs techniques complémentaires :

**Analyse vibratoire** : Technique la plus répandue pour les équipements rotatifs. Les accéléromètres mesurent les vibrations dans les trois axes. L'analyse fréquentielle (FFT) identifie les fréquences caractéristiques de défauts (roulements, désalignement, déséquilibre, desserrage). Précision : 90-95% pour les défauts de roulements.

**Thermographie infrarouge** : Détection des points chauds indiquant surchauffe, mauvais contact électrique, friction anormale. Les caméras thermiques visualisent les gradients de température. Efficace pour équipements électriques et mécaniques. Détection précoce de 85% des défauts électriques.

**Analyse des huiles** : Détection des particules métalliques, contamination, dégradation de lubrifiants. Techniques : spectrométrie, ferrographie, analyse physico-chimique. Permet le suivi de l'usure interne des équipements. Applicable aux moteurs, boîtes de vitesses, systèmes hydrauliques.

**Analyse ultrasonore** : Détection des fuites (air, gaz, liquides), défauts de lubrification, décharges électriques partielles. Capteurs ultrasonores détectent les hautes fréquences inaudibles. Très efficace pour localiser les fuites d'air comprimé (économies énergétiques).

**Surveillance électrique** : Analyse du courant, tension, puissance, facteur de puissance. Détection des déséquilibres, surcharges, défauts de moteurs électriques. Techniques : Motor Current Signature Analysis (MCSA). Non-intrusive et peu coûteuse.

**Monitoring en continu** : Systèmes permanents de capteurs connectés transmettant en temps réel. Permet le suivi continu des tendances et la détection précoce des dérives. Nécessite infrastructure IoT et traitement Big Data.

### 1.3.3 Apprentissage automatique pour la maintenance

L'intelligence artificielle révolutionne la maintenance prédictive grâce à plusieurs familles d'algorithmes :

**Méthodes statistiques classiques** :
- **Régression** : Prédiction de valeurs continues (RUL - Remaining Useful Life)
- **Seuils adaptatifs** : Détection d'anomalies par écart statistique
- **Séries temporelles** : ARIMA, modèles exponentiels pour prévision de tendances
- **Limitations** : Nécessitent expertise domaine, peu adaptés aux relations non-linéaires

**Machine Learning supervisé** :
- **Random Forest** : Ensemble de forêts de décision. Excellent compromis précision/interprétabilité. Robuste au bruit et aux valeurs aberrantes. Utilisé dans SmartMaintain.
- **Extra Trees** : Variant de Random Forest avec randomisation supplémentaire. Plus rapide à entraîner. Performances similaires à Random Forest.
- **Gradient Boosting** (XGBoost, LightGBM) : Très haute performance mais sensible à l'overfitting. Nécessite tuning fin des hyperparamètres.
- **SVM** : Efficace pour classification binaire mais passage à l'échelle difficile sur gros volumes.
- **Précisions typiques** : 85-98% selon qualité des données et complexité des défauts

**Deep Learning** :
- **CNN** : Excellent pour analyse d'images (thermographie) et signaux 1D (vibrations). Extraction automatique de features. Nécessite grands volumes de données.
- **RNN/LSTM** : Adapté aux séries temporelles, capture dépendances long terme. Coûteux en calcul.
- **Autoencoders** : Détection d'anomalies par reconstruction. Apprentissage non-supervisé.
- **Limitations** : Besoin de données massives (>100k samples), coût calcul élevé, faible interprétabilité

**Choix pour SmartMaintain** : Nous avons opté pour Random Forest et Extra Trees car ils offrent :
- Excellent compromis précision/complexité (98-100% de précision atteinte)
- Faible besoin en données (efficaces avec 5k-50k samples)
- Robustesse au bruit et valeurs manquantes
- Interprétabilité (importance des features)
- Temps d'inférence rapides (<50ms)
- Maintenance facilitée du code

### 1.3.4 Solutions existantes

Le marché de la maintenance prédictive est en forte croissance avec plusieurs catégories de solutions :

**Solutions cloud propriétaires** :

**IBM Maximo** : Suite complète de gestion d'actifs avec module prédictif. Intègre IBM Watson AI. Forces : écosystème complet, intégration ERP/MES. Faiblesses : coût élevé (>100k$/an), dépendance cloud, personnalisation limitée.

**Microsoft Azure IoT** : Plateforme cloud avec services ML (Azure ML, Cognitive Services). Forces : scalabilité, intégration Microsoft. Faiblesses : vendor lock-in, coûts variables selon usage.

**AWS IoT + SageMaker** : Infrastructure AWS avec outils ML managés. Forces : flexibilité, nombreux services. Faiblesses : complexité configuration, coûts difficiles à prévoir.

**Solutions spécialisées** :

**Uptake** : Plateforme SaaS spécialisée maintenance prédictive industrielle. Précision annoncée 95%. Forces : facilité déploiement, expertise domaine. Faiblesses : coût élevé, données hébergées externement.

**Predix (GE Digital)** : Plateforme IIoT orientée équipements GE mais ouverte. Forces : expertise industrielle GE. Faiblesses : complexité, support incertain.

**Solutions open source** :

**Prometheus + Grafana** : Monitoring et alertes. Forces : gratuit, communauté active. Faiblesses : pas de ML intégré, nécessite développement custom.

**Apache Kafka + Spark MLlib** : Infrastructure Big Data + ML. Forces : scalabilité, flexibilité. Faiblesses : complexité opérationnelle élevée.

**Comparaison avec SmartMaintain** :

| Critère | Solutions cloud | Solutions spécialisées | SmartMaintain |
|---------|----------------|----------------------|---------------|
| **Coût** | Élevé (abonnement) | Très élevé | Faible (open source) |
| **Personnalisation** | Limitée | Moyenne | Totale |
| **Données** | Cloud externe | Cloud externe | On-premise |
| **Déploiement** | Simple | Simple | Docker (simple) |
| **Maintenance** | Vendeur | Vendeur | Autonome |
| **Scalabilité** | Excellente | Bonne | Bonne (microservices) |
| **Précision ML** | 90-95% | 95-98% | 98-100% (V7) |

**Positionnement de SmartMaintain** : Notre solution se différencie par :
1. **Architecture moderne** : Microservices containerisés, facilement déployables
2. **Contrôle total** : Code source, données, modèles restent internes
3. **Coût maîtrisé** : Pas d'abonnements cloud, infrastructure on-premise
4. **Haute performance** : Modèles V7 atteignant 98-100% de précision
5. **Simplicité** : Refactorisation V7 réduisant la complexité de 35%
6. **Évolutivité** : Architecture permettant l'ajout facile de nouveaux équipements

## 1.4 Objectifs du projet

Sur la base de l'analyse du contexte et de l'état de l'art, nous définissons les objectifs détaillés de SmartMaintain :

**Objectifs fonctionnels** :

1. **Surveillance multi-équipements** : Monitoring simultané de 4 types d'équipements critiques (moteurs, pompes, compresseurs, échangeurs) avec modèles ML spécialisés.

2. **Détection multi-défauts** : Identification de 8 types de défauts spécifiques :
   - Moteurs : normal_operation, degradation_roulement, desequilibre_desalignement
   - Pompes : normal_operation, cavitation, fuite_joints
   - Compresseurs : normal_operation, fuite_air, surchauffe
   - Échangeurs : normal_operation, encrassement, fuite_thermique

3. **Traitement temps réel** : Pipeline complet de l'ingestion IoT à la visualisation avec latence < 200ms.

4. **Alertes intelligentes** : Génération automatique d'alertes avec niveaux de sévérité et recommandations d'intervention.

5. **Interface intuitive** : Dashboard web avec visualisation temps réel, graphiques de tendances, gestion des alertes, historique.

**Objectifs non-fonctionnels** :

1. **Performance** : Prédiction en < 100ms, débit de 100+ prédictions/seconde
2. **Fiabilité** : Disponibilité 99.9%, recovery automatique en cas de panne service
3. **Scalabilité** : Architecture microservices permettant scaling horizontal
4. **Sécurité** : Authentification JWT, RBAC, API sécurisées HTTPS
5. **Maintenabilité** : Code simple (V7), tests automatisés (5/5), documentation complète

**Objectifs techniques** :

1. **Précision ML** : > 95% sur données réelles, > 90% sur données bruitées (10% bruit)
2. **Architecture** : 8 microservices spécialisés, communication asynchrone (Redis)
3. **Déploiement** : Containerisation Docker, orchestration docker-compose
4. **Qualité code** : Refactorisation V7, réduction 35% complexité, tests intégration 100%

## 1.5 Conclusion

Ce chapitre a établi le contexte industriel justifiant le développement de SmartMaintain. Nous avons montré que les approches traditionnelles de maintenance présentent des limitations importantes, et que la convergence IoT/AI/Industrie 4.0 rend possible une maintenance véritablement prédictive. L'analyse de l'état de l'art a révélé que les solutions existantes sont soit coûteuses et propriétaires, soit complexes à mettre en œuvre.

SmartMaintain se positionne comme une solution complète, performante et maîtrisée répondant aux besoins industriels. Les objectifs clairement définis guideront les phases de conception et d'implémentation présentées dans les chapitres suivants.

Le chapitre 2 détaillera l'analyse des besoins et la conception de l'architecture microservices de la plateforme.

---

