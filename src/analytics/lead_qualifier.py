"""Qualification des leads patient pour la clinique."""

from OpenHosta import emulate

from src.models.schemas import LeadQualification


def qualify_lead(conversation_text: str, call_id: str, patient_nom: str) -> LeadQualification:
    """Qualifie le potentiel business d'un patient pour la clinique.

    Analyse la conversation et détermine :

    - est_nouveau_patient : True si c'est sa première visite/appel à la clinique.
      Indices : "je ne suis jamais venu", "on m'a recommandé", absence de référence à un médecin traitant de la clinique.
      False si : "je reviens pour un suivi", "mon médecin habituel", "comme la dernière fois".

    - motif_contact : catégoriser le motif parmi :
      "premier_avis" (nouveau symptôme, première consultation)
      "suivi" (contrôle, résultats, évolution)
      "renouvellement" (ordonnance, certificat)
      "urgence_ressentie" (le patient pense que c'est urgent)
      "information" (question, renseignement)

    - potentiel_suivi : True si le patient a une pathologie chronique, des symptômes persistants,
      ou un besoin de consultations régulières. C'est un indicateur de valeur long terme pour la clinique.

    - source_decouverte : comment le patient a connu la clinique (si mentionné).
      Ex: "bouche à oreille", "internet", "recommandation médecin", null si non mentionné.

    Raisonner en termes de valeur business pour la clinique :
    un patient chronique qui revient régulièrement a plus de valeur qu'un passage ponctuel.
    """
    raw = _extract_lead_info(conversation_text)

    return LeadQualification(
        call_id=call_id,
        patient_nom=patient_nom,
        est_nouveau_patient=raw.est_nouveau_patient,
        motif_contact=raw.motif_contact,
        potentiel_suivi=raw.potentiel_suivi,
        source_decouverte=raw.source_decouverte,
    )


class _LeadInfoGenerated(LeadQualification.__base__):
    """Schema LLM — sans call_id ni patient_nom (calculés)."""
    est_nouveau_patient: bool
    motif_contact: str
    potentiel_suivi: bool
    source_decouverte: str | None = None


def _extract_lead_info(conversation_text: str) -> _LeadInfoGenerated:
    """Extrait les informations de qualification lead depuis la conversation.

    Analyse la conversation et détermine :
    - est_nouveau_patient : True si première visite, False si patient récurrent
    - motif_contact : "premier_avis", "suivi", "renouvellement", "urgence_ressentie" ou "information"
    - potentiel_suivi : True si pathologie chronique ou besoin de consultations régulières
    - source_decouverte : comment le patient a connu la clinique (null si non mentionné)
    """
    return emulate()
