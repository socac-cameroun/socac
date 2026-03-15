SOCAC - Synchronisation simple des prix
======================================

Le site lit maintenant les prix depuis le fichier local `prices.json`.
Le Google Sheet peut donc rester PRIVE dans Google Drive.

Comment mettre les prix a jour
------------------------------
1. Cree un service account Google Cloud.
2. Active Google Sheets API.
3. Partage ton Google Sheet prive avec l'email du service account en lecture.
4. Telecharge la cle JSON du service account.
5. Lance:

   pip install google-api-python-client google-auth
   python sync_prices_from_private_sheet.py --credentials service-account.json

6. Le script met a jour `prices.json`.
7. Republie simplement le site avec le nouveau `prices.json`.

Important
---------
- Le site n'interroge plus Google Drive directement.
- Les prix affiches viennent de `prices.json`.
- Pour voir les nouveaux prix en ligne, il faut redeployer/upload ce fichier apres chaque sync.
- Les catalogues FR et EN utilisent tous les deux le meme `prices.json`.
