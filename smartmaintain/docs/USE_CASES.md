# Diagramme de Cas d'Utilisation — SmartMaintain

## Système : SmartMaintain

---

## Acteurs

| Acteur | Description |
|--------|-------------|
| **Administrateur** | Gère les utilisateurs, le fine-tuning ML et le traitement des alertes |
| **Technicien** | Surveille les équipements et traite les alertes qui lui sont assignées |
| **Viewer** | Consulte les indicateurs et la surveillance en lecture seule |

---

## Cas d'utilisation par acteur

### Administrateur

| Cas d'utilisation | Relation |
|-------------------|----------|
| Se connecter | — |
| Consulter le dashboard | — |
| Surveiller les machines en temps réel | — |
| Consulter les alertes | — |
| Assigner une alerte à un technicien | — |
| Résoudre une alerte | — |
| Gérer les utilisateurs | — |
| Lancer un Fine-Tuning | **«include»** → Valider et activer un modèle ML |

> **Note :** Le cas d'utilisation *Lancer un Fine-Tuning* inclut obligatoirement *Valider et activer un modèle ML*.

---

### Technicien

| Cas d'utilisation | Relation |
|-------------------|----------|
| Se connecter | — |
| Consulter le dashboard | — |
| Surveiller les machines en temps réel | — |
| Consulter les alertes | — |
| Acquitter une alerte assignée | — |
| Mettre à jour le statut de prise en charge | — |

---

### Viewer

| Cas d'utilisation | Relation |
|-------------------|----------|
| Se connecter | — |
| Consulter le dashboard | — |
| Surveiller une machine en temps réel | — |
| Consulter les alertes | Non autorisé |
| Accéder au Fine-Tuning | Non autorisé |
| Gérer les utilisateurs | Non autorisé |

> **Note :** Le rôle *Viewer* est strictement en lecture seule.

---

## Relations entre cas d'utilisation

| Type | Cas source | Cas cible |
|------|-----------|-----------|
| `«include»` | Lancer un Fine-Tuning | Valider et activer un modèle ML |

---

## Matrice des permissions (version explicite)

| Fonctionnalité | Administrateur | Technicien | Viewer |
|----------------|----------------|------------|--------|
| Se connecter | Autorisé | Autorisé | Autorisé |
| Consulter le dashboard | Autorisé | Autorisé | Autorisé |
| Surveiller les machines en temps réel | Autorisé | Autorisé | Autorisé |
| Consulter les alertes | Autorisé | Autorisé | Non autorisé |
| Acquitter une alerte | Autorisé | Autorisé (si assignée) | Non autorisé |
| Assigner une alerte | Autorisé | Non autorisé | Non autorisé |
| Résoudre une alerte | Autorisé | Autorisé (selon workflow) | Non autorisé |
| Lancer un Fine-Tuning | Autorisé | Non autorisé | Non autorisé |
| Gérer les utilisateurs | Autorisé | Non autorisé | Non autorisé |

> **Note :** Cette matrice décrit explicitement ce qui est autorisé/interdit pour valider les rôles dans l'application.

---

## Récapitulatif complet

```
SmartMaintain
│
├── Administrateur
│   ├── Se connecter
│   ├── Consulter le dashboard
│   ├── Surveiller les machines en temps réel
│   ├── Consulter les alertes
│   ├── Assigner une alerte à un technicien
│   ├── Résoudre une alerte
│   ├── Gérer les utilisateurs
│   ├── Lancer un Fine-Tuning
│   │   └── «include» Valider et activer un modèle ML
│
├── Technicien
│   ├── Se connecter
│   ├── Consulter le dashboard
│   ├── Surveiller les machines en temps réel
│   ├── Consulter les alertes
│   ├── Acquitter une alerte assignée
│   └── Mettre à jour le statut de prise en charge
│
└── Viewer
    ├── Se connecter
    ├── Consulter le dashboard
    ├── Surveiller une machine en temps réel
    ├── Consulter les alertes (non autorisé)
    ├── Accéder au Fine-Tuning (non autorisé)
    └── Gérer les utilisateurs (non autorisé)
```

---

*Diagramme réalisé dans le cadre du projet SmartMaintain — Stage PHOTOCARB 2025*
