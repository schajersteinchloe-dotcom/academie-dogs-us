// Pont Drive — Académie Dogs & Us
// Donne à la routine du soir de Claude un accès d'une heure à ton Google Drive, seulement avec ta clé
// (Paramètres du projet → Propriétés du script → CLE). Claude ne voit jamais ton mot de passe Google.

const DOSSIERS = {
  A_MONTER: 'Académie - À monter',      // tu déposes les rushs ici
  MONTEES: 'Académie - Montées',        // Claude dépose les leçons finies ici
  FAITS: 'Rushs déjà montés',           // dans « À monter » : les rushs déjà traités
};

// Une fois, depuis l'éditeur (bouton Exécuter) : demande l'autorisation et crée les dossiers dans ton Drive.
function installer() {
  dossiers_();
  Drive.Files.list({pageSize: 1});      // active l'API Drive que la routine utilise
}

function doPost(e) {
  const cle = PropertiesService.getScriptProperties().getProperty('CLE');
  const demande = JSON.parse((e.postData && e.postData.contents) || '{}');
  if (!cle || demande.cle !== cle) return json_({erreur: 'clé refusée'});
  const d = dossiers_();
  return json_({jeton: ScriptApp.getOAuthToken(), a_monter: d.A_MONTER, montees: d.MONTEES, faits: d.FAITS});
}

// les dossiers sont retrouvés par leur identifiant : tu peux les renommer ou les déplacer
function dossiers_() {
  const props = PropertiesService.getScriptProperties();
  const trouve = (nom, parent) => {
    const id = props.getProperty(nom);
    if (id) {
      try {
        const f = DriveApp.getFolderById(id);
        if (!f.isTrashed()) return f;
      } catch (err) {}
    }
    const f = (parent || DriveApp.getRootFolder()).createFolder(DOSSIERS[nom]);
    props.setProperty(nom, f.getId());
    return f;
  };
  const aMonter = trouve('A_MONTER');
  return {A_MONTER: aMonter.getId(), MONTEES: trouve('MONTEES').getId(), FAITS: trouve('FAITS', aMonter).getId()};
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
