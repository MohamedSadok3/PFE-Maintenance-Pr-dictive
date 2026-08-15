# Audit technique de SmartMaintain

Date de l'audit : 2026-08-15  
Portee : inspection statique en lecture seule du code source. Sont exclus de l'analyse detaillee : `node_modules`, environnements virtuels, caches, sorties de build, gros jeux CSV et contenu binaire des artefacts ML. Les en-tetes/echantillons des CSV et les noms, tailles et metadata des artefacts ont toutefois ete inspectes.

## 1. Arborescence utile

```text
smartmaintain/
|-- .env.example
|-- docker-compose.yml
|-- mosquitto.conf
|-- README.md
|-- backend/
|   |-- gateway/                 # point d'entree HTTP et relais WebSocket
|   |-- auth/                    # authentification, usines, utilisateurs, composants
|   |-- iot/                     # configuration IoT, injection et rejeu CSV
|   |   |-- data/                # 4 CSV de demonstration (500 lignes chacun)
|   |   `-- services/replay_service.py
|   |-- ml/                      # inference, fine-tuning, feedback, artefacts
|   |   |-- engines/{mock_engine,real_engine}.py
|   |   |-- routes/{predict,status,finetune,reload,feedback}.py
|   |   |-- services/{ml_service,finetune_service,feedback_service}.py
|   |   |-- migrations/001_prediction_logging.sql
|   |   `-- models/trained/      # 4 x model/scaler/encodeur/metadata
|   |-- alertes/                 # alertes, dashboard et consommateur Redis
|   |-- shared/                  # auth JWT, config, constantes, DB, reponses HTTP
|   |-- migrations/              # schema principal et runner
|   `-- tests/                   # tests unitaires backend
|-- frontend/
|   |-- src/
|   |   |-- components/          # layout et controle de routes
|   |   |-- hooks/               # dashboard et surveillance temps reel
|   |   |-- pages/               # ecrans React
|   |   |-- services/            # Axios et Socket.IO
|   |   `-- constants/
|   `-- Dockerfile, nginx.conf, package.json
`-- docs/                        # installation, architecture, cas d'usage, guide ML
```

## 2. Technologies reellement utilisees

- Backend : Python, Flask, Flask-CORS, PyJWT, psycopg/PostgreSQL, Redis Pub/Sub.
- Temps reel : Flask-SocketIO/Eventlet dans Gateway et Alertes, client `socket.io-client` dans React.
- IoT et traitement du signal : pandas, NumPy, SciPy ; rejeu de CSV avec fenetre glissante.
- ML : scikit-learn 1.2.2, XGBoost 2.1.3, joblib, pandas/NumPy ; moteur fictif selectionnable par `MOCK_ML`.
- Frontend : React 19, Vite, React Router 6, Axios, React Hook Form, Recharts, Tailwind CSS.
- Infrastructure : Docker Compose, PostgreSQL 15, Redis 7, Eclipse Mosquitto 2, Nginx pour le frontend.

Ports internes definis dans le code : Gateway `5000`, IoT `5001`, ML `5002`, Alertes `5003`, Auth `5004`. Seuls Gateway (`5000`) et Frontend (`3000`) sont exposes par Compose.

## 3. Les cinq microservices Flask

| Service | Fichier d'entree | Responsabilite | Dependances principales |
|---|---|---|---|
| API Gateway | `backend/gateway/app.py` | Proxy `/api/*`, validation JWT pour Socket.IO, relais des evenements par usine | services HTTP, Redis, Socket.IO Alertes |
| Auth | `backend/auth/app.py` | connexion, inscriptions d'usine, utilisateurs, usines, composants, email d'approbation | PostgreSQL, SMTP |
| IoT | `backend/iot/app.py` | configuration/test TCP MQTT, injection, rejeu des 4 CSV | PostgreSQL, Redis, fichiers CSV |
| ML | `backend/ml/app.py` | prediction, consommation Redis, artefacts XGBoost, fine-tuning et feedback | Redis, PostgreSQL, joblib/XGBoost |
| Alertes | `backend/alertes/app.py` | creation/gestion d'alertes, synthese dashboard, emission Socket.IO | PostgreSQL, Redis |

Le Gateway mappe `auth`, `users`, `plants` et `components` vers Auth ; `iot` vers IoT ; `ml` vers ML ; `alertes` et `dashboard` vers Alertes.

## 4. Fichiers importants et role

- `docker-compose.yml` : demarrage des 5 services, migrations, PostgreSQL, Redis, Mosquitto et frontend ; volumes DB, CSV et modeles.
- `.env.example` : contrat de configuration DB, Redis, MQTT, JWT, superadmin, SMTP, mode ML et identifiant d'usine de rejeu.
- `backend/shared/constants.py` : roles, machines, ports, canaux Redis et seuils de severite.
- `backend/shared/auth.py` : lecture du Bearer JWT, verification et placement de l'utilisateur dans `flask.g`.
- `backend/migrations/*.sql` et `run_migrations.py` : schema principal et migrations appliquees dans l'ordre lexical.
- `backend/iot/services/replay_service.py` : fenetres de 20 mesures, calcul des caracteristiques et publication dans `sensor_data`.
- `backend/ml/engines/real_engine.py` : chargement des artefacts et construction du vecteur d'inference.
- `backend/ml/services/ml_service.py` : prediction HTTP et boucle Redis `sensor_data` -> `ml_predictions`.
- `backend/alertes/services/redis_consumer.py` : consommation des predictions, seuils, persistence et evenements.
- `backend/gateway/app.py` : proxy et deux relais temps reel vers les navigateurs.
- `frontend/src/services/api.js` : client Axios vers `VITE_API_URL` ou `http://localhost:5000` et Bearer token.
- `frontend/src/services/socketService.js` : singleton Socket.IO authentifie.
- `frontend/src/hooks/useSurveillance.js` : reception des mesures ; simulation possible en developpement.

## 5. Endpoints existants

Tous les endpoints applicatifs sont accessibles via le Gateway. Sauf mention contraire, ils demandent un JWT.

### Gateway

- `GET /health`
- proxy generique des chemins `/api/<section>` et `/api/<section>/<path>`
- Socket.IO : `connect`; relais `sensor:data`, `alert:new`, `alert:updated` vers la salle `plant:<plant_id>` ; salle speciale `role:superadmin`.

### Auth, utilisateurs, usines et composants

- `POST /api/auth/login` (public) ; entree `{email,password}` ; sortie `{token,user}`.
- `GET|PATCH /api/auth/me`.
- `POST /api/auth/register-plant` (public) ; donnees usine, administrateur et documents ; `201` avec inscription.
- `GET /api/auth/registrations?status=...` (superadmin).
- `PATCH /api/auth/registrations/:id/review` (superadmin) ; `{action,note}`.
- `GET|POST /api/users`, `PATCH|DELETE /api/users/:id` (droits variables admin/superadmin/superviseur).
- `GET|PATCH /api/plants/me` (admin).
- `GET /api/plants`, `DELETE /api/plants/:id`, `GET /api/plants/:id/overview` (superadmin).
- `PATCH /api/plants/:id` existe mais retourne explicitement `403`.
- `GET|POST /api/components`, `PATCH|DELETE /api/components/:id` ; lecture pour tous les roles, ecriture admin/superadmin.

### IoT

- `GET /api/iot/status` (tout utilisateur authentifie).
- `GET|POST /api/iot/config` (admin de l'usine).
- `POST /api/iot/config/test` (admin) : teste uniquement une connexion TCP a `host:port`.
- `POST /api/iot/inject` (admin/superadmin) ; entree `{machine,sensors,timestamp?,plant_id?}` ; le superadmin doit fournir l'usine, l'admin utilise son usine.

### ML

- `POST /api/ml/predict` ; entree `{machine,sensors,plant_id?,component_id?}` ; sortie avec classe, scores, confiance, timestamps et capteurs.
- `GET /api/ml/status`.
- `POST /api/ml/finetune` (admin/superadmin) : multipart CSV (`machine`, `model_name`, `file`) ou selection JSON de modele.
- `GET /api/ml/finetune/status/:job_id`, `GET /api/ml/finetune/jobs`.
- `POST /api/ml/reload?machine=...`, `GET /api/ml/reload/verify`.
- Feedback : `GET /api/ml/feedback/predictions`, `GET /predictions/:id`, `GET|POST /predictions/:id/feedback`, `GET /export/training-data`, `GET /statistics`, `POST /batch-feedback`, tous sous le prefixe `/api/ml/feedback`.

Attention : les routes `reload` et plusieurs routes `feedback` ne peuvent actuellement pas etre enregistrees, car elles appellent `require_auth(require_role=...)` alors que le decorateur accepte `roles` en argument positionnel. Deux handlers feedback lisent aussi `request.current_user`, alors que l'authentification ecrit dans `flask.g.current_user`.

### Alertes et dashboard

- `GET /api/alertes` ; filtres `machine`, `severity`, `status`, `acknowledged`, `page`, `limit`.
- `GET|PATCH /api/alertes/:id` ; actions d'assignation, acquittement, resolution et reouverture selon le role.
- `GET /api/dashboard/summary`.

## 6. Applications React et appels API

Il existe une seule application React. Routes publiques : `/login`, `/inscription-usine`. Routes authentifiees principales : `/dashboard`, `/profil`, `/surveillance`, `/alertes`, `/alertes/:id`; puis pages conditionnees par role pour usine, inscriptions, utilisateurs, composants, configuration IoT et fine-tuning.

Les services frontend appellent :

- `authService` : login, profil, inscription/revue d'usine et administration des usines.
- `userService` : CRUD utilisateurs.
- `componentService` : CRUD composants.
- `iotService` : statut, configuration, test et injection IoT.
- `alerteService` : liste, detail et mise a jour des alertes.
- `dashboardService` : synthese du dashboard.
- `socketService` : `sensor:data`, `alert:new`, `alert:updated`.

La page `FineTuningPage.jsx` ne contient actuellement aucun appel aux endpoints ML de fine-tuning, reload ou feedback. Aucun service frontend ML n'existe. En mode developpement, `useSurveillance` peut produire des donnees simulees, ce qui peut masquer l'absence de flux reel.

## 7. PostgreSQL, Redis, WebSocket, MQTT et Compose

### PostgreSQL

Le schema principal cree `plants`, `users`, `components`, `plant_registrations`, `alerts`, `interventions`, `iot_mqtt_configs`, `iot_sensor_configs` et leurs index. La migration `0003` ajoute `plant_id` aux alertes et remplit les anciennes lignes avec la premiere usine disponible. `0004` copie les anciennes tables IoT au singulier vers les tables au pluriel, sans supprimer les anciennes.

La migration ML cree `prediction_log`, `prediction_feedback` et la vue `training_data_export`, mais se trouve dans `backend/ml/migrations`. Le runner principal ne parcourt que `backend/migrations/*.sql`; cette migration n'est donc pas appliquee par le conteneur `migrations` actuel.

### Redis et WebSocket

- Canal `sensor_data` : IoT -> ML.
- Canal `ml_predictions` : ML -> Alertes et Gateway.
- Alertes emet sur son Socket.IO interne ; Gateway s'y connecte et retransmet.
- Gateway consomme egalement directement `ml_predictions` et emet `sensor:data`.

Ces deux chemins peuvent emettre deux fois le meme `sensor:data`. Les consommateurs rejettent les evenements sans `plant_id`; si `IOT_PLANT_ID` n'est pas configure pour le rejeu CSV, aucune alerte ni mesure temps reel tenant-scoped n'arrive a l'interface.

### MQTT/Mosquitto

Mosquitto ecoute sur `1883` avec `allow_anonymous true`. Le code sauvegarde une configuration MQTT et teste l'ouverture TCP, mais aucun client MQTT, abonnement, parsing de topic ou publication MQTT n'est implemente. Aucune dependance Paho MQTT n'est presente. Le trajet MQTT annonce n'existe donc pas encore.

## 8. Formats CSV et colonnes par equipement

Les quatre fichiers inspectes contiennent exactement 500 lignes de donnees, un en-tete, des timestamps ISO sans fuseau et un pas d'une minute.

| Equipement | Nom du fichier | Colonnes exactes |
|---|---|---|
| moteur | `backend/iot/data/moteur.csv` | `timestamp,vibration,current,temperature` |
| pompe | `backend/iot/data/pompe.csv` | `timestamp,vibration,pressure_in,pressure_out,flow_rate` |
| compresseur | `backend/iot/data/compresseur.csv` | `timestamp,pressure,current,temperature_oil,temperature_air` |
| echangeur thermique | `backend/iot/data/echangeur.csv` | `timestamp,temp_in_hot,temp_out_hot,temp_in_cold,temp_out_cold,flow_rate` |

Pour chaque colonne capteur, le rejeu calcule sur 20 lignes : `max`, `min`, `mean`, `sd`, `rms`, `skewness`, `kurtosis`, `crest`, `form`, sous la forme `<capteur>_<feature>`, et ajoute `<capteur>_instant`. Des alias bruts ne sont ajoutes que pour `temperature`, `pressure` et `flow_rate`.

Le moteur ML declare comme capteurs requis : moteur `vibration,current`; pompe `vibration,pressure_in,pressure_out`; compresseur `pressure,current`; echangeur `temp_in_hot,temp_out_hot,flow_rate`.

## 9. Artefacts ML presents

Chaque equipement possede les quatre fichiers attendus dans `backend/ml/models/trained` :

- `<machine>_xgb.pkl`
- `<machine>_scaler.pkl`
- `<machine>_label_encoder.pkl`
- `<machine>_metadata.json`

Il y a donc 16 artefacts pour `moteur`, `pompe`, `compresseur` et `echangeur`. Les metadata declarent neuf features dans cet ordre exact : `max,min,mean,sd,rms,skewness,kurtosis,crest,form`.

Classes declarees :

- moteur : `degradation_roulement`, `desequilibre_desalignement`, `normal_operation` ; accuracy metadata `1.0`.
- pompe : `cavitation`, `fuite_joints`, `normal_operation` ; accuracy `1.0`.
- compresseur : `fuite_air`, `normal_operation`, `surchauffe` ; accuracy `0.965`.
- echangeur : `encrassement`, `fuite_thermique`, `normal_operation` ; accuracy `0.925`.

Le service charge toutefois les artefacts depuis le chemin code en dur `/app/models/trained`; la variable documentee `ML_MODELS_PATH=/app/models` n'est pas lue. Le mode actif depend de `MOCK_ML` dans l'environnement d'execution et n'est pas deduit ici du fichier `.env` prive.

## 10. Parcours actuel d'une mesure

```text
CSV -> ReplayService (fenetre 20 + features)
    -> Redis sensor_data
    -> MLService + moteur mock/reel
    -> Redis ml_predictions
       |-> Alertes: seuil, persistence PostgreSQL, alert:new, sensor:data
       `-> Gateway: sensor:data direct
    -> Gateway Socket.IO, salle de l'usine
    -> hooks/pages React
```

Une injection HTTP rejoint le flux au niveau de `sensor_data`. Il n'existe actuellement aucun trajet depuis MQTT : Mosquitto et les configurations sont presents, mais aucun consommateur MQTT n'alimente Redis.

Seuils d'alerte : score `< 0.40` sans alerte ; `0.40` Mineure ; `0.65` Majeure ; `0.85` Critique. Une classe normale ne cree pas d'alerte.

## 11. Problemes detectes

### Bloquants

1. `backend/ml/routes/reload.py` et des routes de `feedback.py` utilisent un mot-cle non supporte par `require_auth`; l'import du service ML peut echouer avant son demarrage.
2. `feedback.py` lit `request.current_user` au lieu de `flask.g`/`get_current_user`; il cherche aussi `id` alors que le JWT utilise `sub`.
3. `001_prediction_logging.sql` n'est pas execute par le runner principal : les fonctions de journalisation/feedback ciblent des tables potentiellement absentes.
4. `real_engine._extract_features` ne construit le vecteur de neuf features qu'a partir des cles `vibration_*`. Cela correspond au moteur et a la pompe, mais pas au compresseur ni a l'echangeur. Pour ces deux machines, le code bascule vers un signal scalaire de secours largement nul et ne respecte pas clairement le contrat d'entrainement.
5. L'integration MQTT n'est pas implementee.

### Importants

6. Le reload instancie un nouveau `MLService` local ; il ne recharge pas necessairement l'instance longue duree qui consomme Redis.
7. Les noms de modeles exposes par les constantes parlent encore de LSTM/Transformer, alors que les artefacts reels sont XGBoost.
8. Les erreurs du consommateur ML sont capturees sans propagation ; une prediction normale de secours peut cacher une inference invalide.
9. Le healthcheck ML recharge potentiellement tous les artefacts a chaque appel en mode reel.
10. Deux ponts Gateway/Alertes retransmettent `sensor:data`, avec risque de doublons frontend.
11. Le rejeu depend de `IOT_PLANT_ID`; sans valeur, les evenements sont volontairement abandonnes pour respecter l'isolation multi-usine.
12. La page fine-tuning est seulement une interface locale et n'utilise pas l'API ML existante.
13. `allow_anonymous true` sur Mosquitto est acceptable pour une demonstration isolee, pas pour un deploiement partage.
14. Des documents/commentaires historiques indiquent des ports ou architectures qui ne correspondent pas tous aux constantes et a Compose actuels.

## 12. Elements manquants pour integrer proprement les quatre modeles Colab

- Un contrat versionne par equipement indiquant exactement quelles series produisent les neuf features et dans quel ordre elles sont agregees.
- La confirmation que les 16 artefacts presents sont bien les exports finaux du notebook Colab et sont compatibles avec les versions Python/scikit-learn/XGBoost du conteneur.
- Une metadata complete : version du modele, schema d'entree, unite de chaque capteur, fenetre, frequence, mapping des labels, date et metriques par classe.
- Une extraction de features par machine conforme au notebook, au lieu du chemin unique `vibration_*`.
- Validation stricte des capteurs, types, NaN, unites et ordre avant `scaler.transform`.
- Tests d'inference de reference avec vecteurs et sorties attendues pour les quatre machines.
- Une strategie atomique de depot/versionnement et de rollback des quatre groupes d'artefacts.
- Un reload agissant sur l'instance partagee par le consommateur Redis.
- L'application de la migration de prediction et une politique de retention/isolation par usine.
- Le branchement de la page React aux endpoints de jobs, reload et feedback, si cette fonction doit etre exposee.
- Un vrai adaptateur MQTT vers le schema canonique `{machine,sensors,timestamp,plant_id}`.

## 13. Plan d'integration fichier par fichier (aucune integration effectuee)

1. `backend/ml/models/trained/*_metadata.json` : enrichir et figer le contrat exact de chaque modele apres confirmation du notebook.
2. `backend/ml/engines/real_engine.py` : implementer un mapping de features propre a chaque equipement, validation stricte et erreurs explicites.
3. `backend/ml/engines/base_engine.py` : formaliser le contrat entree/sortie commun.
4. `backend/ml/services/ml_service.py` : partager une instance d'engine, rendre le reload effectif et fiabiliser le logging.
5. `backend/ml/routes/reload.py` et `feedback.py` : aligner le decorateur et la lecture de l'utilisateur courant.
6. `backend/ml/migrations/001_prediction_logging.sql` : renommer/deplacer vers `backend/migrations` avec un numero non conflictuel, puis le faire gerer par le runner.
7. `backend/ml/routes/predict.py` : valider le schema par machine et l'isolation `plant_id`.
8. `backend/iot/services/replay_service.py` : produire uniquement le schema de features confirme par les modeles.
9. `backend/iot/services/` : ajouter un consommateur MQTT et le cycle reconnexion/abonnement.
10. `backend/iot/routes/iot.py` et `config_service.py` : valider topics, credentials, TLS et test MQTT reel.
11. `backend/gateway/app.py` et `backend/alertes/services/redis_consumer.py` : choisir un seul chemin de diffusion des mesures.
12. `backend/shared/constants.py` : remplacer les noms de modeles historiques et centraliser les schemas par machine.
13. `frontend/src/services/mlService.js` (a creer apres accord) : encapsuler status, predict, jobs, reload et feedback.
14. `frontend/src/pages/FineTuningPage.jsx` : brancher les appels et afficher progression/erreurs/versions.
15. `backend/tests/` : ajouter fixtures d'artefacts, tests des quatre vecteurs, pipeline Redis, MQTT et isolation multi-usine.
16. `docs/ML_GUIDE.md`, `docs/ARCHITECTURE.md`, `.env.example` : synchroniser contrat, versions, ports, chemin d'artefacts et procedure de deploiement.

## 14. Questions necessitant confirmation

1. Pour chaque modele Colab, quel capteur exact produit le vecteur `[max,min,mean,sd,rms,skewness,kurtosis,crest,form]` ? Un seul capteur ou une combinaison ?
2. La fenetre d'entrainement est-elle exactement 20 echantillons, avec quelle frequence et quelles unites ?
3. Les 16 fichiers actuellement presents sont-ils les exports definitifs a integrer ou des artefacts de test ?
4. Les classes et leur ordre dans chaque encodeur doivent-ils etre consideres contractuels ?
5. `echangeur` est-il l'identifiant canonique API/ML pour « echangeur thermique » ?
6. Le flux de production doit-il venir de topics MQTT par usine, par equipement ou par capteur ? Quel format de payload et quelle politique TLS/authentification ?
7. Souhaitez-vous conserver le rejeu CSV et le moteur mock en production, uniquement en developpement, ou les retirer apres validation ?
8. Quel composant doit etre l'unique source WebSocket des mesures : Gateway directement depuis Redis, ou Alertes via son Socket.IO ?
9. Le feedback/fine-tuning doit-il etre accessible aux techniciens, aux admins, ou seulement au superadmin ? Le role `operator` reference par le ML n'existe pas dans les constantes actuelles.
10. Le fine-tuning doit-il reellement entrainer dans le conteneur, ou uniquement importer et activer des artefacts produits dans Colab ?

## Conclusion d'audit

L'architecture des cinq services et le trajet CSV -> Redis -> ML -> Alertes/Gateway -> React sont identifiables et globalement structures. Les quatre jeux d'artefacts multiclasse existent deja, mais leur contrat d'entree n'est pas suffisamment documente et l'extracteur courant est incompatible avec au moins le compresseur et l'echangeur. Avant toute integration, il faut confirmer le schema de features Colab, corriger le demarrage des routes ML et rendre la migration de feedback effectivement applicable. MQTT est pour l'instant une configuration sans ingestion fonctionnelle.
