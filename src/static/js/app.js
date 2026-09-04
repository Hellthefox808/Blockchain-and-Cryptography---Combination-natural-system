/**
 * Blockchain & Cryptography Combo Nature System Frontend Client
 */

// Application State
const state = {
  activeWallet: null,
  presetWallets: {},
  chain: [],
  stats: null,
  pendingTxs: [],
};

// DOM Elements
const elements = {
  statHeight: document.getElementById('stat-height'),
  statDifficulty: document.getElementById('stat-difficulty'),
  statMempool: document.getElementById('stat-mempool'),
  statusBadge: document.getElementById('status-badge'),
  statusText: document.getElementById('status-text'),
  btnRefresh: document.getElementById('btn-refresh'),

  // Tabs
  tabBtns: document.querySelectorAll('.tab-btn'),
  tabPanes: document.querySelectorAll('.tab-pane'),

  // Explorer
  chainContainer: document.getElementById('chain-container'),
  btnValidateChain: document.getElementById('btn-validate-chain'),
  blockDetailPanel: document.getElementById('block-detail-panel'),
  btnCloseDetail: document.getElementById('btn-close-detail'),
  detailBlockTitle: document.getElementById('detail-block-title'),
  detailBlockHash: document.getElementById('detail-block-hash'),
  detailPrevHash: document.getElementById('detail-prev-hash'),
  detailMerkleRoot: document.getElementById('detail-merkle-root'),
  detailNonce: document.getElementById('detail-nonce'),
  detailDifficulty: document.getElementById('detail-difficulty'),
  detailTimestamp: document.getElementById('detail-timestamp'),
  detailTxCount: document.getElementById('detail-tx-count'),
  detailTxList: document.getElementById('detail-tx-list'),

  // Wallet
  btnCreateWallet: document.getElementById('btn-create-wallet'),
  btnLoadVinny: document.getElementById('btn-load-vinny'),
  btnLoadKinny: document.getElementById('btn-load-kinny'),
  btnLoadMiner: document.getElementById('btn-load-miner'),
  activeWalletAddress: document.getElementById('active-wallet-address'),
  activeWalletPubkey: document.getElementById('active-wallet-pubkey'),
  activeWalletPrivkey: document.getElementById('active-wallet-privkey'),
  walletBalance: document.getElementById('wallet-balance'),

  // Transaction
  formTransaction: document.getElementById('form-transaction'),
  txSender: document.getElementById('tx-sender'),
  txRecipient: document.getElementById('tx-recipient'),
  txAmount: document.getElementById('tx-amount'),
  txFee: document.getElementById('tx-fee'),
  txPrivkey: document.getElementById('tx-privkey'),
  mempoolList: document.getElementById('mempool-list'),
  btnRefreshMempool: document.getElementById('btn-refresh-mempool'),

  // Mining
  minerAddress: document.getElementById('miner-address'),
  btnMineBlock: document.getElementById('btn-mine-block'),
  miningConsoleLog: document.getElementById('mining-console-log'),
  mineRewardDisplay: document.getElementById('mine-reward-display'),

  // Crypto Lab
  avalancheInput1: document.getElementById('avalanche-input-1'),
  avalancheInput2: document.getElementById('avalanche-input-2'),
  btnRunAvalanche: document.getElementById('btn-run-avalanche'),
  avalancheResults: document.getElementById('avalanche-results'),
  resFlippedBits: document.getElementById('res-flipped-bits'),
  resDivergencePct: document.getElementById('res-divergence-pct'),
  resAvalancheStatus: document.getElementById('res-avalanche-status'),
  resHash1: document.getElementById('res-hash1'),
  resHash2: document.getElementById('res-hash2'),
  bitMatrix: document.getElementById('bit-matrix'),

  // Tampering
  tamperBlockIdx: document.getElementById('tamper-block-idx'),
  tamperAmount: document.getElementById('tamper-amount'),
  btnTamperBlock: document.getElementById('btn-tamper-block'),
  btnResetChain: document.getElementById('btn-reset-chain'),

  // Toasts
  toastContainer: document.getElementById('toast-container'),
};

// Toast notification helper
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div style="font-weight: 600; text-transform: capitalize;">${type}:</div>
    <div>${message}</div>
  `;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// API Client Utilities
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'API request failed');
    }
    return await res.json();
  } catch (err) {
    showToast(err.message, 'error');
    throw err;
  }
}

async function apiPost(endpoint, data = {}) {
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'API request failed');
    }
    return await res.json();
  } catch (err) {
    showToast(err.message, 'error');
    throw err;
  }
}

// Update System Telemetry & Stats
async function refreshStats() {
  try {
    const stats = await apiGet('/api/stats');
    state.stats = stats;

    elements.statHeight.textContent = stats.chain_length;
    elements.statDifficulty.textContent = '0'.repeat(stats.difficulty);
    elements.statMempool.textContent = stats.pending_transactions_count;
    elements.mineRewardDisplay.textContent = stats.mining_reward.toFixed(1);

    if (stats.is_valid) {
      elements.statusBadge.className = 'status-badge valid';
      elements.statusText.textContent = 'CHAIN SECURE';
    } else {
      elements.statusBadge.className = 'status-badge tampered';
      elements.statusText.textContent = `CORRUPTED (Block #${stats.broken_block_index})`;
    }
  } catch (e) {
    console.error('Failed to load stats', e);
  }
}

// Render Blockchain Timeline
async function refreshChain() {
  try {
    const chainData = await apiGet('/api/chain');
    state.chain = chainData.chain || [];
    elements.chainContainer.innerHTML = '';

    const isCorrupted = state.stats && !state.stats.is_valid;
    const brokenIndex = state.stats ? state.stats.broken_block_index : -1;

    state.chain.forEach((block) => {
      const card = document.createElement('div');
      const isThisBlockCorrupted = isCorrupted && block.index >= brokenIndex;
      card.className = `block-card ${isThisBlockCorrupted ? 'corrupted' : ''}`;

      const dateStr = new Date(block.timestamp * 1000).toLocaleTimeString();
      card.innerHTML = `
        <div class="block-card-header">
          <span class="block-height">Block #${block.index}</span>
          <span class="block-nonce">Nonce: ${block.nonce}</span>
        </div>
        <div class="block-hash-box">
          <div class="hash-label">Block Hash:</div>
          <div class="hash-value">${block.hash.substring(0, 18)}...${block.hash.substring(56)}</div>
        </div>
        <div class="block-hash-box">
          <div class="hash-label">Prev Hash:</div>
          <div class="hash-value">${block.previous_hash.substring(0, 18)}...</div>
        </div>
        <div class="block-meta">
          <span>TXs: ${block.transactions.length}</span>
          <span>${dateStr}</span>
        </div>
      `;

      card.addEventListener('click', () => openBlockDetail(block.index));
      elements.chainContainer.appendChild(card);
    });
  } catch (e) {
    console.error('Failed to load chain', e);
  }
}

// Open Detailed Block Inspection
async function openBlockDetail(index) {
  try {
    const block = await apiGet(`/api/block/${index}`);
    elements.detailBlockTitle.textContent = `Block #${block.index} Cryptographic Verification`;
    elements.detailBlockHash.textContent = block.hash;
    elements.detailPrevHash.textContent = block.previous_hash;
    elements.detailMerkleRoot.textContent = block.merkle_root;
    elements.detailNonce.textContent = block.nonce;
    elements.detailDifficulty.textContent = block.difficulty;
    elements.detailTimestamp.textContent = new Date(block.timestamp * 1000).toLocaleString();
    elements.detailTxCount.textContent = block.transactions.length;

    elements.detailTxList.innerHTML = '';
    block.transactions.forEach((tx) => {
      const txItem = document.createElement('div');
      txItem.className = 'tx-preview-card';
      txItem.innerHTML = `
        <div class="flex-row-space">
          <span style="color:var(--accent-sky); font-weight:600;">${tx.amount} Tokens</span>
          <span style="color:var(--text-muted); font-size:0.75rem;">TX: ${tx.tx_id ? tx.tx_id.substring(0, 12) + '...' : 'N/A'}</span>
        </div>
        <div style="color:var(--text-secondary); font-family:var(--font-mono); font-size:0.75rem;">
          From: ${tx.sender.substring(0, 20)}...<br>
          To: ${tx.recipient.substring(0, 20)}...
        </div>
      `;
      elements.detailTxList.appendChild(txItem);
    });

    elements.blockDetailPanel.classList.remove('hidden');
    elements.blockDetailPanel.scrollIntoView({ behavior: 'smooth' });
  } catch (e) {
    console.error('Failed to open block detail', e);
  }
}

// Mempool Management
async function refreshMempool() {
  try {
    const pending = await apiGet('/api/transaction/pending');
    state.pendingTxs = pending;
    elements.mempoolList.innerHTML = '';

    if (pending.length === 0) {
      elements.mempoolList.innerHTML = `
        <div style="color: var(--text-muted); text-align: center; padding: 2rem;">
          No pending transactions in mempool. Send tokens from the Transaction Hub!
        </div>
      `;
      return;
    }

    pending.forEach((tx) => {
      const item = document.createElement('div');
      item.className = 'glass-card';
      item.style.padding = '1rem';
      item.style.marginBottom = '0';
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-weight: 700; color: var(--accent-sky);">${tx.amount} Tokens</span>
          <span class="hash-label">Fee: ${tx.fee}</span>
        </div>
        <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary);">
          <div>From: ${tx.sender}</div>
          <div>To: ${tx.recipient}</div>
          <div style="color: var(--accent-cyan); margin-top: 0.3rem;">Sig: ${tx.signature ? tx.signature.substring(0, 24) + '...' : 'unsigned'}</div>
        </div>
      `;
      elements.mempoolList.appendChild(item);
    });
  } catch (e) {
    console.error('Failed to refresh mempool', e);
  }
}

// Wallet Studio Functions
async function createNewWallet() {
  try {
    const wallet = await apiPost('/api/wallet/create');
    setActiveWallet(wallet);
    showToast('New SECP256k1 Keypair Generated!', 'success');
  } catch (e) {
    console.error('Wallet generation failed', e);
  }
}

function setActiveWallet(wallet) {
  state.activeWallet = wallet;
  elements.activeWalletAddress.textContent = wallet.address;
  elements.activeWalletPubkey.value = wallet.public_key_pem;
  elements.activeWalletPrivkey.value = wallet.private_key_pem;

  // Pre-fill transaction sender form
  elements.txSender.value = wallet.address;
  elements.txPrivkey.value = wallet.private_key_pem;
  elements.minerAddress.value = wallet.address;

  updateWalletBalance(wallet.address);
}

async function updateWalletBalance(address) {
  try {
    const balanceData = await apiGet(`/api/wallet/${address}/balance`);
    elements.walletBalance.textContent = balanceData.balance.toFixed(2);
  } catch (e) {
    elements.walletBalance.textContent = '0.00';
  }
}

async function getOrCreatePresetWallet(name) {
  if (state.presetWallets[name]) {
    setActiveWallet(state.presetWallets[name]);
    showToast(`Loaded preset wallet: ${name}`, 'info');
    return;
  }
  const wallet = await apiPost('/api/wallet/create');
  state.presetWallets[name] = wallet;
  setActiveWallet(wallet);
  showToast(`Created & loaded preset wallet: ${name}`, 'success');
}

// Transaction Submission
async function handleTransactionSubmit(e) {
  e.preventDefault();
  const sender = elements.txSender.value.trim();
  const recipient = elements.txRecipient.value.trim();
  const amount = parseFloat(elements.txAmount.value);
  const fee = parseFloat(elements.txFee.value) || 0.0;
  const privateKey = elements.txPrivkey.value.trim();

  if (!sender || !recipient || isNaN(amount) || amount <= 0 || !privateKey) {
    showToast('Please fill out all required transaction fields.', 'error');
    return;
  }

  try {
    const payload = {
      sender,
      recipient,
      amount,
      fee,
      private_key: privateKey,
    };
    const tx = await apiPost('/api/transaction/new', payload);
    showToast(`Transaction ${tx.tx_id.substring(0, 10)}... submitted to mempool!`, 'success');

    // Reset amount
    elements.txAmount.value = '';
    await refreshStats();
    await refreshMempool();
    if (state.activeWallet) updateWalletBalance(state.activeWallet.address);
  } catch (e) {
    console.error('Transaction broadcast failed', e);
  }
}

// Mining Execution
async function handleMineBlock() {
  const miner = elements.minerAddress.value.trim();
  if (!miner) {
    showToast('Please enter a miner address to receive the block reward.', 'error');
    return;
  }

  const logBox = elements.miningConsoleLog;
  logBox.innerHTML += `<div>> [${new Date().toLocaleTimeString()}] Mining initiated for miner ${miner.substring(0, 16)}...</div>`;
  logBox.innerHTML += `<div>> Packing transactions from mempool & computing Merkle Root...</div>`;
  logBox.scrollTop = logBox.scrollHeight;

  try {
    elements.btnMineBlock.disabled = true;
    elements.btnMineBlock.innerHTML = '<span class="status-dot" style="background:var(--accent-amber);"></span> Mining PoW...';

    const result = await apiPost('/api/mine', { miner_address: miner });

    logBox.innerHTML += `<div style="color: var(--accent-emerald);">> Mined Block #${result.block_index}! Hash: ${result.block_hash.substring(0, 20)}... (Nonce: ${result.nonce})</div>`;
    logBox.scrollTop = logBox.scrollHeight;

    showToast(result.message, 'success');
    await refreshStats();
    await refreshChain();
    await refreshMempool();
    if (state.activeWallet) updateWalletBalance(state.activeWallet.address);
  } catch (e) {
    logBox.innerHTML += `<div style="color: var(--accent-rose);">> Mining failed: ${e.message}</div>`;
  } finally {
    elements.btnMineBlock.disabled = false;
    elements.btnMineBlock.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      Mine Next Block Now
    `;
  }
}

// Cryptographic Lab: Avalanche Effect
async function handleRunAvalanche() {
  const in1 = elements.avalancheInput1.value;
  const in2 = elements.avalancheInput2.value;

  try {
    const data = await apiPost('/api/crypto/avalanche', { input1: in1, input2: in2 });
    elements.resFlippedBits.textContent = data.differing_bits;
    elements.resDivergencePct.textContent = `${data.percentage_divergence}%`;
    elements.resAvalancheStatus.textContent = data.is_avalanche_ideal ? 'IDEAL (~50%)' : 'STRONG';
    elements.resHash1.textContent = data.hash1_hex;
    elements.resHash2.textContent = data.hash2_hex;

    // Build 256-bit matrix
    elements.bitMatrix.innerHTML = '';
    for (let i = 0; i < data.diff_mask.length; i++) {
      const cell = document.createElement('div');
      const isFlipped = data.diff_mask[i] === '1';
      cell.className = `bit-cell ${isFlipped ? 'divergence' : 'match'}`;
      cell.title = `Bit #${i}: ${isFlipped ? 'FLIPPED' : 'MATCH'}`;
      elements.bitMatrix.appendChild(cell);
    }

    elements.avalancheResults.classList.remove('hidden');
    showToast(`Avalanche analyzed: ${data.differing_bits} bits changed (${data.percentage_divergence}%)`, 'info');
  } catch (e) {
    console.error('Avalanche analysis failed', e);
  }
}

// Tampering Simulation
async function handleTamperBlock() {
  const blockIdx = parseInt(elements.tamperBlockIdx.value, 10);
  const newAmount = parseFloat(elements.tamperAmount.value) || 99999.0;

  try {
    const result = await apiPost('/api/tamper', { block_index: blockIdx, new_amount: newAmount });
    showToast(result.message, 'error');

    // Immediately audit chain integrity
    await auditChainIntegrity();
  } catch (e) {
    console.error('Tamper attack failed', e);
  }
}

// Audit Chain Integrity
async function auditChainIntegrity() {
  try {
    const val = await apiGet('/api/validate');
    await refreshStats();
    await refreshChain();

    if (val.is_valid) {
      showToast('Chain Verification Passed: All blocks & Merkle roots valid!', 'success');
    } else {
      showToast(`Tamper Alert: Block #${val.broken_block_index} corrupted! Downstream hashes broken.`, 'error');
    }
  } catch (e) {
    console.error('Chain audit failed', e);
  }
}

// Reset Chain
async function handleResetChain() {
  if (!confirm('Are you sure you want to reset the blockchain to the initial Genesis block?')) {
    return;
  }
  try {
    const res = await apiPost('/api/reset');
    showToast(res.message, 'info');
    await refreshStats();
    await refreshChain();
    await refreshMempool();
    if (state.activeWallet) updateWalletBalance(state.activeWallet.address);
  } catch (e) {
    console.error('Chain reset failed', e);
  }
}

// Tab Switching
function initTabs() {
  elements.tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      elements.tabBtns.forEach((b) => b.classList.remove('active'));
      elements.tabPanes.forEach((p) => p.classList.remove('active'));

      btn.classList.add('active');
      const pane = document.getElementById(targetId);
      if (pane) pane.classList.add('active');
    });
  });
}

// Event Listeners
function initEventListeners() {
  elements.btnRefresh.addEventListener('click', async () => {
    await refreshStats();
    await refreshChain();
    await refreshMempool();
    if (state.activeWallet) updateWalletBalance(state.activeWallet.address);
    showToast('Dashboard data refreshed.', 'info');
  });

  elements.btnValidateChain.addEventListener('click', auditChainIntegrity);
  elements.btnCloseDetail.addEventListener('click', () => {
    elements.blockDetailPanel.classList.add('hidden');
  });

  elements.btnCreateWallet.addEventListener('click', createNewWallet);
  elements.btnLoadVinny.addEventListener('click', () => getOrCreatePresetWallet('Vinny'));
  elements.btnLoadKinny.addEventListener('click', () => getOrCreatePresetWallet('Kinny'));
  elements.btnLoadMiner.addEventListener('click', () => getOrCreatePresetWallet('Miner'));

  elements.formTransaction.addEventListener('submit', handleTransactionSubmit);
  elements.btnRefreshMempool.addEventListener('click', refreshMempool);

  elements.btnMineBlock.addEventListener('click', handleMineBlock);
  elements.btnRunAvalanche.addEventListener('click', handleRunAvalanche);

  elements.btnTamperBlock.addEventListener('click', handleTamperBlock);
  elements.btnResetChain.addEventListener('click', handleResetChain);
}

// Initialization
async function init() {
  initTabs();
  initEventListeners();

  await refreshStats();
  await refreshChain();
  await refreshMempool();

  // Run initial avalanche demo
  await handleRunAvalanche();

  // Initialize Vinny preset wallet as default active wallet
  await getOrCreatePresetWallet('Vinny');

  // Periodic polling every 10 seconds
  setInterval(async () => {
    await refreshStats();
  }, 10000);
}

document.addEventListener('DOMContentLoaded', init);
