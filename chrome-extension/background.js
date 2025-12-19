/**
 * Background service worker pour l'extension Veille
 * Gère les actions en arrière-plan et les menus contextuels
 */

// Crée un menu contextuel pour capturer rapidement un lien
chrome.runtime.onInstalled.addListener(() => {
  // Menu contextuel pour les liens
  chrome.contextMenus.create({
    id: 'capture-link',
    title: 'Ajouter à Veille',
    contexts: ['link']
  });

  // Menu contextuel pour la page
  chrome.contextMenus.create({
    id: 'capture-page',
    title: 'Ajouter cette page à Veille',
    contexts: ['page']
  });
});

// Gère les clics sur le menu contextuel
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'capture-link') {
    captureLink(info.linkUrl, tab.title);
  } else if (info.menuItemId === 'capture-page') {
    capturePage(tab.url, tab.title);
  }
});

/**
 * Capture un lien
 */
async function captureLink(url, pageTitle) {
  const config = await loadConfig();

  if (!config.token) {
    showNotification('⚠️ Configuration requise', 'Cliquez sur l\'extension pour configurer votre token GitHub.');
    return;
  }

  try {
    const issue = await createGitHubIssue(config, url, `Capturé depuis: ${pageTitle}`);
    showNotification(`✅ Article ajouté!`, `Issue #${issue.number} créée`);
  } catch (error) {
    showNotification('❌ Erreur', error.message);
  }
}

/**
 * Capture la page actuelle
 */
async function capturePage(url, title) {
  const config = await loadConfig();

  if (!config.token) {
    showNotification('⚠️ Configuration requise', 'Cliquez sur l\'extension pour configurer votre token GitHub.');
    return;
  }

  try {
    const issue = await createGitHubIssue(config, url, '');
    showNotification(`✅ Article ajouté!`, `Issue #${issue.number} créée`);
  } catch (error) {
    showNotification('❌ Erreur', error.message);
  }
}

/**
 * Charge la configuration depuis chrome.storage
 */
async function loadConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ['githubToken', 'githubUser', 'repoName'],
      (result) => {
        resolve({
          token: result.githubToken,
          user: result.githubUser || 'martinregent',
          repo: result.repoName || 'veille'
        });
      }
    );
  });
}

/**
 * Crée une issue GitHub via l'API
 */
async function createGitHubIssue(config, url, note) {
  // Construction du payload JSON structuré
  const issueData = {
    url: url,
    note: note || "",
    tags: [] // Pas de tags via le menu contextuel pour l'instant
  };

  const body = JSON.stringify(issueData, null, 2);

  const response = await fetch(
    `https://api.github.com/repos/${config.user}/${config.repo}/issues`,
    {
      method: 'POST',
      headers: {
        'Authorization': `token ${config.token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: 'Article à traiter',
        body: body,
        labels: ['to_process']
      })
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `Erreur GitHub: ${response.status}`);
  }

  return await response.json();
}

/**
 * Affiche une notification
 */
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon-128.png',
    title: title,
    message: message
  });
}
