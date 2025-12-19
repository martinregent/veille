/**
 * Popup script pour l'extension Veille
 * Gère l'interface de capture d'articles
 */

// Éléments du DOM
const setupState = document.getElementById('setup-state');
const captureState = document.getElementById('capture-state');
const loadingState = document.getElementById('loading-state');
const successState = document.getElementById('success-state');
const errorState = document.getElementById('error-state');

const configForm = document.getElementById('config-form');
const captureBtn = document.getElementById('capture-btn');
const configBtn = document.getElementById('config-btn');
const retryBtn = document.getElementById('retry-btn');
const newCaptureBtn = document.getElementById('new-capture-btn');
const viewIssueBtn = document.getElementById('view-issue-btn');

const articleTitle = document.getElementById('article-title');
const articleUrl = document.getElementById('article-url');
const articleDescription = document.getElementById('article-description');
const articleTags = document.getElementById('article-tags');
const errorMessage = document.getElementById('error-message');
const successMessage = document.getElementById('success-message');

let currentIssueUrl = '';

/**
 * Affiche un état et cache les autres
 */
function showState(state) {
  setupState.style.display = 'none';
  captureState.style.display = 'none';
  loadingState.style.display = 'none';
  successState.style.display = 'none';
  errorState.style.display = 'none';

  state.style.display = 'block';
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
 * Sauvegarde la configuration
 */
function saveConfig(token, user, repo) {
  return new Promise((resolve) => {
    chrome.storage.local.set(
      {
        githubToken: token,
        githubUser: user,
        repoName: repo
      },
      resolve
    );
  });
}

/**
 * Récupère l'URL et le titre de la page actuelle
 */
async function getCurrentPageInfo() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      resolve({
        url: tab.url,
        title: tab.title
      });
    });
  });
}

/**
 * Crée une issue GitHub via l'API
 */
async function createGitHubIssue(config, url, note, tags) {
  // On structure le corps en JSON pour le script de traitement
  const issueData = {
    url: url,
    note: note || "",
    tags: tags ? tags.split(',').map(t => t.trim()).filter(t => t) : []
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
 * Initialise l'extension
 */
async function init() {
  const config = await loadConfig();

  // Si la config existe, affiche le formulaire de capture
  if (config.token) {
    const pageInfo = await getCurrentPageInfo();
    articleTitle.value = pageInfo.title;
    articleUrl.value = pageInfo.url;
    showState(captureState);
  } else {
    // Sinon, affiche le formulaire de configuration
    showState(setupState);
  }
}

/**
 * Événement: Sauvegarde de la configuration
 */
configForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const token = document.getElementById('github-token').value;
  const user = document.getElementById('github-user').value;
  const repo = document.getElementById('repo-name').value;

  if (!token || !user || !repo) {
    alert('Veuillez remplir tous les champs');
    return;
  }

  try {
    await saveConfig(token, user, repo);
    await init(); // Recharge l'interface
  } catch (error) {
    alert('Erreur lors de la sauvegarde: ' + error.message);
  }
});

/**
 * Événement: Capture d'article
 */
captureBtn.addEventListener('click', async () => {
  const config = await loadConfig();
  const url = articleUrl.value;
  const description = articleDescription.value;
  const tags = articleTags.value;

  if (!url) {
    showError('L\'URL est requise');
    return;
  }

  showState(loadingState);

  try {
    const issue = await createGitHubIssue(config, url, description, tags);
    currentIssueUrl = issue.html_url;
    successMessage.textContent = `Issue #${issue.number} créée avec succès!`;
    showState(successState);
  } catch (error) {
    showError(error.message);
  }
});

/**
 * Événement: Affiche la configuration
 */
configBtn.addEventListener('click', async () => {
  const config = await loadConfig();
  document.getElementById('github-token').value = config.token || '';
  document.getElementById('github-user').value = config.user || 'martinregent';
  document.getElementById('repo-name').value = config.repo || 'veille';
  showState(setupState);
});

/**
 * Événement: Nouvelle capture
 */
newCaptureBtn.addEventListener('click', async () => {
  articleDescription.value = '';
  articleTags.value = '';
  await init();
});

/**
 * Événement: Voir l'issue
 */
viewIssueBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: currentIssueUrl });
});

/**
 * Événement: Réessayer
 */
retryBtn.addEventListener('click', () => {
  showState(captureState);
});

/**
 * Affiche un message d'erreur
 */
function showError(message) {
  errorMessage.textContent = message;
  showState(errorState);
}

// Initialise l'extension au chargement
init();
