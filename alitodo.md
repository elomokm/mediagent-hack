# Architecture MediAgent

Agent IA de pré-tri médical vendu aux cliniques.
Gère les appels patients : triage → orientation → booking → analytics.

---

## 1. Flux principal d'un appel

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPEL ENTRANT                            │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
              ┌────────────────────────┐
              │   ACCUEIL PATIENT      │  ← emulate() : greeting
              │   (conversation.py)    │
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │   COLLECTE SYMPTÔMES   │  ← emulate() : questions
              │   (conversation.py)    │    itératif tour par tour
              │   boucle jusqu'à info  │    extract_patient_info()
              │   suffisante           │    generate_next_question()
              └───────────┬────────────┘
                          ▼
                          │ PatientInput complet
                          ▼
         ┌─────────────────────────────────┐
         │  TRIAGE URGENCE                 │  ← emulate() + @safe
         │  (triage.py)                    │    temperature=0
         │  evaluate_urgency() → 0.0→1.0   │    seuil incertitude 5%
         └────────────┬────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
    score >= 0.8 &          score < 0.8
    confidence >= 0.9            │
           │                     ▼
           ▼          ┌─────────────────────┐
   ┌───────────────┐  │  ORIENTATION SOIN   │ ← emulate()
   │  TRANSFERT    │  │  (care_router.py)   │   qualify_care_type()
   │  SAMU (15)    │  │  → CareType         │
   │ (call_router) │  └──────────┬──────────┘
   │ logique pure  │          ┌──┴──────────────┐
   └──────┬────────┘          │                 │
          │          PHARMACIE/URGENCES    GENERALISTE/
          │          → message orient.     TELECONSULTATION
          │          → pas de RDV               │
          │                   │                 ▼
          │                   │     ┌───────────────────────┐
          │                   │     │  MATCHING MÉDECIN     │ ← emulate()
          │                   │     │ (doctor_matcher.py)   │   match_doctor()
          │                   │     │ symptômes → spécialité│
          │                   │     └──────────┬────────────┘
          │                   │                ▼
          │                   │     ┌───────────────────────┐
          │                   │     │  BOOKING              │   logique pure
          │                   │     │ (scheduling.py)       │   find_available_slots()
          │                   │     │ → créneaux dispo      │   book_slot()
          │                   │     │ → réservation         │
          │                   │     │ → MAJ planning doc    │
          │                   │     └──────────┬────────────┘
          │                   │                ▼
          │                   │     ┌───────────────────────┐
          │                   │     │  CONFIRMATION         │   logique pure (mock)
          │                   │     │ (notification.py)     │   SMS/email patient
          │                   │     └──────────┬────────────┘
          │                   │                │
          ▼                   ▼                ▼
    ┌─────────────────────────────────────────────────────┐
    │              CLÔTURE APPEL                          │
    │  timestamp_fin, durée, statut                      │
    └──────────────────────────┬──────────────────────────┘
                               ▼
    ┌─────────────────────────────────────────────────────┐
    │              ANALYTICS POST-APPEL                   │
    │                                                     │
    │  Résumé clinique    (summary.py)       ← emulate() │
    │  Analyse appel      (call_analyzer.py) ← emulate() │
    │  Qualif. lead       (lead_qualifier.py)← emulate() │
    │  Stats agrégées     (stats.py)        logique pure  │
    │                                                     │
    │  → CallLog complet sauvegardé (data_store.py)      │
    └─────────────────────────────────────────────────────┘
```

---

## 2. Structure des modules

```
src/
├── models/
│   └── schemas.py           # TOUS les types Pydantic (source de vérité)
│
├── agent/
│   ├── triage.py            # Évaluation urgence (@safe + emulate)
│   ├── care_router.py       # Orientation type de soin (emulate)
│   ├── conversation.py      # Accueil + collecte tour par tour (emulate)
│   ├── doctor_matcher.py    # Matching symptômes → médecin (emulate)
│   ├── summary.py           # Résumé clinique + résumé appel (emulate)
│   └── pipeline.py          # Orchestrateur principal (logique pure)
│
├── tools/
│   ├── scheduling.py        # Planning médecins + booking (logique pure)
│   ├── notification.py      # Envoi confirmations SMS/email (mock)
│   ├── call_router.py       # Transfert SAMU / redirection (logique pure)
│   └── data_store.py        # Persistence JSON pour la démo (logique pure)
│
├── analytics/
│   ├── call_analyzer.py     # Analyse qualité appel (emulate)
│   ├── lead_qualifier.py    # Qualification lead (emulate)
│   └── stats.py             # Statistiques agrégées (logique pure)
│
├── config.py                # Variables d'env + seuils métier
└── main.py                  # Point d'entrée démo
```

---

## 3. Schemas Pydantic

### Existants (schemas.py)

| Schema | Rôle |
|---|---|
| `PatientInput` | Identité + symptômes du patient |
| `UrgencyScore` | Score urgence (0→1) + confiance + reasoning |
| `CareType` | Enum : URGENCES, GENERALISTE, TELECONSULTATION, PHARMACIE |
| `CareRecommendation` | Type de soin + message patient |
| `TimeSlot` | Créneau horaire (début, fin, médecin, lieu) |
| `Appointment` | RDV confirmé + ID confirmation |
| `ClinicalSummary` | Résumé structuré pour le médecin |
| `SurveyResponse` | Réponse enquête satisfaction |
| `SurveyAnalysis` | Analyse NLP de l'enquête |

### À ajouter

| Schema | Rôle |
|---|---|
| `Specialite` | Enum spécialités médicales |
| `Doctor` | Médecin (id, nom, spécialités, lieu) |
| `DoctorSchedule` | Planning d'un médecin (slots dispo/réservés) |
| `Clinic` | Clinique (nom, adresse, médecins, horaires) |
| `CallStatus` | Enum : EN_COURS, TERMINE, TRANSFERE_SAMU, ABANDONNE |
| `ConversationTurn` | Un tour de conversation (role + message + timestamp) |
| `CallSession` | Session d'appel complète (id, timestamps, conversation) |
| `CallSentiment` | Enum : POSITIF, NEUTRE, NEGATIF, ANXIEUX |
| `CallAnalysis` | Analyse post-appel (durée, sentiment, thèmes, qualité) |
| `CallSummaryStructured` | Résumé structuré de l'appel pour dashboard |
| `LeadQualification` | Qualif. lead (nouveau patient, potentiel suivi, motif) |
| `DailyStats` | Stats agrégées par jour (volume, taux RDV, etc.) |
| `CallLog` | Objet complet d'un appel (session + summary + analysis + lead) |

---

## 4. Répartition emulate() vs logique pure

### Fonctions emulate() (décisions IA via OpenHosta)

| Fonction | Module | Notes |
|---|---|---|
| `evaluate_urgency` | triage.py | **+ @safe** (décision critique, temp=0) |
| `qualify_care_type` | care_router.py | temp=0 |
| `generate_greeting` | conversation.py | |
| `extract_patient_info` | conversation.py | |
| `generate_next_question` | conversation.py | |
| `match_doctor` | doctor_matcher.py | temp=0 |
| `generate_clinical_summary` | summary.py | |
| `generate_call_summary` | summary.py | |
| `analyze_call` | call_analyzer.py | |
| `qualify_lead` | lead_qualifier.py | |

### Fonctions logique pure (pas de LLM)

| Fonction | Module |
|---|---|
| `is_life_threatening` | triage.py |
| `has_sufficient_info` | conversation.py |
| `find_available_slots` | scheduling.py |
| `book_slot` | scheduling.py |
| `redirect_to_samu` | call_router.py |
| `compute_daily_stats` | stats.py |
| `compute_doctor_load` | stats.py |
| `compute_peak_hours` | stats.py |
| Tout `DataStore` | data_store.py |
| Tout `notification` | notification.py |

---

## 5. Données analytics capturées par appel

| Donnée | Source | Type |
|---|---|---|
| Durée appel (sec) | `session.timestamp_fin - debut` | calculé |
| Résumé structuré | `generate_call_summary()` | emulate |
| Sentiment global | `analyze_call()` | emulate |
| Thèmes principaux | `analyze_call()` | emulate |
| Score qualité | `analyze_call()` | emulate |
| Orientation choisie | `qualify_care_type()` | emulate |
| RDV pris oui/non | booking logic | calculé |
| Médecin assigné | `match_doctor()` | emulate |
| Nouveau patient ? | `qualify_lead()` | emulate |
| Potentiel suivi | `qualify_lead()` | emulate |

### Stats agrégées pour le dashboard clinique

- Volume d'appels (jour/semaine/mois)
- Répartition par orientation (URGENCES / GENERALISTE / TELECONSULTATION / PHARMACIE)
- Taux de conversion en RDV
- Nombre de transferts SAMU
- Durée moyenne des appels
- Distribution sentiment (positif/neutre/négatif/anxieux)
- Heures de pointe
- Top 10 symptômes les plus fréquents
- Charge par médecin (taux d'occupation)
- Nombre de nouveaux patients vs récurrents

---

## 6. Seuils métier (config.py)

| Constante | Valeur | Usage |
|---|---|---|
| `URGENCY_LIFE_THREATENING_SCORE` | 0.8 | Score au-dessus → transfert SAMU |
| `URGENCY_LIFE_THREATENING_CONFIDENCE` | 0.9 | Confiance minimum pour décision vitale |
| `SAFE_UNCERTAINTY_THRESHOLD` | 0.05 | Seuil @safe pour le triage |
| `SAFE_SEED` | 42 | Reproductibilité des décisions |

---

## 7. Contrainte légale

**L'agent ne fait JAMAIS :**
- De diagnostic médical
- De recommandation de traitement ou médicament
- De prescription
- De remplacement d'un professionnel de santé

**Toujours rappeler : "En cas de doute, appelez le 15 (SAMU)"**

---

## 8. Décisions POC / Hackathon

### Persistence — SQLite

Fichier unique `data/mediagent.db`. Tables :
- `calls` → CallLog sérialisé (JSON dans une colonne + colonnes indexées pour les stats)
- `appointments` → RDV avec doctor_id, patient_name, slot
- `schedules` → Planning par médecin par jour

Avantage : données persistent entre les lancements, requêtes SQL directes pour les stats, crédible pour le jury.

### Contexte agent — AgentContext centralisé

```python
class AgentContext(BaseModel):
    clinic: Clinic                              # infos clinique (nom, adresse, médecins)
    current_session: CallSession                # session d'appel en cours
    conversation_history: list[ConversationTurn] # historique conversation
    patient_partial: PatientInput | None        # infos patient en cours de collecte
```

Chaque fonction `emulate()` reçoit `AgentContext` en argument. La docstring de la fonction utilise ce contexte pour donner au LLM toutes les infos nécessaires (nom de la clinique, médecins dispos, historique conversation, etc.).

### Génération dynamique de la clinique

Au lancement, `generate_clinic()` crée :
- 1 clinique "MediSanté" (nom, adresse, horaires)
- 5 médecins (généraliste x2, cardiologue, dermatologue, pédiatre)
- Plannings sur 7 jours : créneaux 30min, 9h-12h / 14h-18h, ~30% déjà réservés

### Modes d'exécution

```bash
python main.py              # Mode interactif (conversation texte)
python main.py --demo       # 3 scénarios automatiques
python main.py --vocal      # Mode vocal (STT Whisper + TTS OpenAI)
```

### 3 scénarios de démo

| # | Profil patient | Chemin attendu | Ce que ça montre |
|---|---|---|---|
| 1 | 65 ans, douleur thoracique intense | Triage > 0.8 → SAMU (15) | Détection urgence vitale |
| 2 | 35 ans, maux de tête 2 semaines | Généraliste → matching → booking | Flux complet avec RDV |
| 3 | 28 ans, rhume léger 2 jours | Pharmacie → conseil | Orientation sans RDV |

### Output terminal attendu

Après chaque appel :
```
═══════════════ ANALYTICS APPEL #a3f2 ═══════════════
Durée          : 45s
Orientation    : GENERALISTE
RDV            : Dr. Martin — 22/03 à 10h30
Sentiment      : Positif
Thèmes         : [maux de tête, stress, suivi]
Qualité        : 0.87/1.0
Lead           : Nouveau patient, potentiel suivi
══════════════════════════════════════════════════════
```

Fin de session :
```
═══════════════ STATS JOURNALIÈRES ══════════════════
Appels         : 3
SAMU           : 1 (33%)
RDV pris       : 1 (33%)
Pharmacie      : 1 (33%)
Durée moyenne  : 38s
══════════════════════════════════════════════════════
```



