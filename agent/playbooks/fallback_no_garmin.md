# Playbook — Fallback no Garmin

## But

Rester utile quand Garmin n’est pas synchronisable.

## Comportement

Si `sync-garmin` ou l’auth Garmin n’est pas disponible :
- le dire clairement
- ne pas bloquer si des données locales existent déjà
- basculer sur les derniers snapshots locaux disponibles
- réduire le niveau de certitude de la recommandation

## Sortie attendue

Une réponse du type :
- ce qu’on sait
- ce qu’on ne sait pas
- la recommandation la plus prudente possible
