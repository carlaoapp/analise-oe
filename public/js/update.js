/**
 * UPDATE.JS - ANALISE O.E
 * Controle de versao do aplicativo + aviso de atualizacao disponivel na tela.
 * Exibe popup para baixar/instalar o app na tela inicial e notifica na tela
 * quando uma nova versao for lancada para o usuario clicar e atualizar.
 *
 * Atualizar NAO apaga ordens de servico, dados, orcamentos nem configuracoes.
 * Esses dados ficam salvos em localStorage/IndexedDB, que nao sao tocados.
 */

const APP_VERSION = '1.0.0';
const UPDATE_CHECK_INTERVAL_MS = 60000;
let updatePromptShownFor = null;

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderAppVersionTags() {
  document.querySelectorAll('.app-version-tag').forEach((el) => {
    el.textContent = `v${APP_VERSION}`;
  });
}

function showToast(msg, tipo = 'info') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px; z-index: 99999999;
    padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: 0.9rem;
    color: #fff; background: ${tipo === 'success' ? '#059669' : tipo === 'warning' ? '#d97706' : '#0284c7'};
    box-shadow: 0 8px 24px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 8px;
    animation: fadeInToast 0.3s ease;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==========================================
// VERIFICACAO DE NOVA VERSAO
// ==========================================
async function fetchLatestVersion() {
  try {
    const res = await fetch(`version.json?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) return null;
    const data = await res.json();
    return data && data.version ? String(data.version) : null;
  } catch (e) {
    return null;
  }
}

async function checkForUpdates(manual = false) {
  if (!navigator.onLine) {
    if (manual) showToast('Sem conexao no momento para verificar atualizacoes.', 'warning');
    return;
  }

  try {
    const latest = await fetchLatestVersion();
    if (!latest) return;

    if (latest !== APP_VERSION) {
      if (!manual && sessionStorage.getItem(`update_postponed_${latest}`) === 'true') return;
      showUpdatePrompt(latest);
    } else {
      const box = document.getElementById('appUpdatePromptBox');
      if (box) box.remove();
      if (manual) showToast(`O app ja esta na versao mais recente (v${APP_VERSION}).`, 'success');
    }
  } catch (e) {
    if (manual) showToast('Nao foi possivel verificar atualizacoes agora.', 'warning');
  }
}

// ==========================================
// MENSAGEM NA TELA: "ATUALIZACAO DISPONIVEL"
// ==========================================
function showUpdatePrompt(newVersion) {
  if (document.getElementById('appUpdatePromptBox')) return;
  updatePromptShownFor = newVersion;

  const box = document.createElement('div');
  box.id = 'appUpdatePromptBox';
  box.className = 'app-update-prompt';
  box.setAttribute('role', 'alertdialog');
  box.innerHTML = `
    <div class="app-update-title">
      <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="width:22px;height:22px;color:#93c5fd;"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
      <span>Atualizacao Disponivel!</span>
    </div>
    <div class="app-update-text">
      Nova versao <strong>v${escapeHtml(newVersion)}</strong> pronta para uso.<br>
      Versao atual: v${escapeHtml(APP_VERSION)}. Suas ordens de servico serao mantidas intactas.
    </div>
    <div class="app-update-buttons">
      <button id="btnUpdateNow" type="button" class="app-update-btn-now">
        <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="width:16px;height:16px;"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        <span>Atualizar Agora</span>
      </button>
      <button id="btnUpdateLater" type="button" class="app-update-btn-later">Mais Tarde</button>
    </div>
  `;
  document.body.appendChild(box);

  document.getElementById('btnUpdateNow').addEventListener('click', () => applyUpdate(newVersion, box));
  document.getElementById('btnUpdateLater').addEventListener('click', () => {
    sessionStorage.setItem(`update_postponed_${newVersion}`, 'true');
    box.classList.add('closing');
    setTimeout(() => box.remove(), 350);
  });
}

// ==========================================
// APLICAR ATUALIZACAO (RENOVA O CACHE)
// ==========================================
async function applyUpdate(newVersion, box) {
  box.innerHTML = `
    <div class="app-update-title">
      <svg class="ui-icon app-update-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="width:20px;height:20px;"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg>
      <span>Instalando atualizacao...</span>
    </div>
  `;

  try {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const reg of regs) await reg.unregister();
    }
    if ('caches' in window) {
      const keys = await caches.keys();
      for (const key of keys) await caches.delete(key);
    }

    setTimeout(() => {
      window.location.replace(`${window.location.origin}${window.location.pathname}?v=${Date.now()}`);
    }, 400);
  } catch (e) {
    console.warn('Falha ao atualizar:', e);
    box.remove();
    showToast('Falha temporaria. Recarregue a pagina para atualizar.', 'warning');
  }
}

// ==========================================
// BAIXAR / INSTALAR APLICATIVO NA TELA INICIAL
// ==========================================
let deferredInstallPrompt = null;

function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

function showInstallPrompt() {
  if (isAppInstalled()) return;
  if (sessionStorage.getItem('pwa_install_dismissed') === 'true') return;
  if (document.getElementById('pwaInstallPromptBox')) return;

  const box = document.createElement('div');
  box.id = 'pwaInstallPromptBox';
  box.className = 'app-install-prompt';
  box.setAttribute('role', 'dialog');
  box.innerHTML = `
    <div class="app-install-card">
      <div class="app-install-header">
        <img src="icon-192.png" alt="Análise O.E" class="app-install-logo">
        <div class="app-install-info">
          <div class="app-install-title">Baixar Análise O.E?</div>
          <div class="app-install-subtitle">Acesso instantâneo e tela cheia</div>
        </div>
      </div>
      <div class="app-install-desc">
        Deseja baixar e instalar o aplicativo no seu aparelho? Ele fica salvo na tela inicial do celular ou computador e abre instantaneamente.
      </div>
      <div class="app-install-buttons">
        <button id="btnPwaInstallNow" type="button" class="btn-pwa-install-now">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="width:16px;height:16px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>Baixar / Instalar App</span>
        </button>
        <button id="btnPwaInstallDismiss" type="button" class="btn-pwa-install-later">Agora Não</button>
      </div>
    </div>
  `;

  document.body.appendChild(box);

  document.getElementById('btnPwaInstallNow').addEventListener('click', () => triggerAppInstall(box));
  document.getElementById('btnPwaInstallDismiss').addEventListener('click', () => {
    sessionStorage.setItem('pwa_install_dismissed', 'true');
    box.classList.add('closing');
    setTimeout(() => box.remove(), 350);
  });
}

async function triggerAppInstall(boxEl = null) {
  if (deferredInstallPrompt) {
    try {
      deferredInstallPrompt.prompt();
      const choiceResult = await deferredInstallPrompt.userChoice;
      if (choiceResult.outcome === 'accepted') {
        showToast('Instalando aplicativo na sua tela inicial...', 'success');
        if (boxEl) boxEl.remove();
      } else {
        showToast('Instalacao adiada.', 'info');
      }
      deferredInstallPrompt = null;
    } catch (e) {
      console.warn('Erro ao acionar instalacao:', e);
    }
  } else if (isIOS()) {
    alert("Para baixar no iPhone/iPad:\n1. Toque no botao Compartilhar (icone com seta para cima) no Safari;\n2. Role e selecione 'Adicionar a Tela de Inicio'.");
  } else {
    showToast("Para instalar: toque nos 3 pontinhos do navegador e escolha 'Instalar aplicativo' ou 'Adicionar a tela inicial'.", 'info');
  }
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  setTimeout(showInstallPrompt, 1500);
});

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  const box = document.getElementById('pwaInstallPromptBox');
  if (box) box.remove();
  showToast('Aplicativo Analise O.E instalado com sucesso!', 'success');
});

// Inicializacao automatica
document.addEventListener('DOMContentLoaded', () => {
  renderAppVersionTags();
  setTimeout(() => checkForUpdates(false), 2500);
  setInterval(() => checkForUpdates(false), UPDATE_CHECK_INTERVAL_MS);
  window.addEventListener('online', () => checkForUpdates(false));
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForUpdates(false);
  });
});

window.APP_VERSION = APP_VERSION;
window.checkForUpdates = checkForUpdates;
window.showUpdatePrompt = showUpdatePrompt;
window.triggerAppInstall = triggerAppInstall;
window.showInstallPrompt = showInstallPrompt;
