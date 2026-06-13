let currentPuuid = "";
let initialAlliesHtml = "";
let initialEnemiesHtml = "";
let initialAlliesAvgHtml = "";
let initialEnemiesAvgHtml = "";
let lastCareerData = null;
let currentMatchDetailsData = null;
let currentMatchDetailsTab = 'scoreboard';
let currentPerformancePuuid = '';

const RANKS = [
    "Unranked",
    "Iron 1", "Iron 2", "Iron 3",
    "Bronze 1", "Bronze 2", "Bronze 3",
    "Silver 1", "Silver 2", "Silver 3",
    "Gold 1", "Gold 2", "Gold 3",
    "Platinum 1", "Platinum 2", "Platinum 3",
    "Diamond 1", "Diamond 2", "Diamond 3",
    "Ascendant 1", "Ascendant 2", "Ascendant 3",
    "Immortal 1", "Immortal 2", "Immortal 3",
    "Radiant"
];

/**
 * Maps queue IDs to user-friendly titles and formats game mode strings.
 * Replaces HURM with TEAM DEATHMATCH.
 * 
 * @param {string} mode Game mode queue ID.
 * @return {string} Formatted game mode name.
 */
function formatGameMode(mode) {
    if (!mode) {
        return '';
    }
    const upper = mode.trim().toUpperCase();
    if (upper === 'HURM') {
        return 'TEAM DEATHMATCH';
    }
    return upper;
}

/**
 * Gets index of a rank name.
 * 
 * @param {string} rankName The name of the rank.
 * @return {number} Index.
 */
function getRankIndex(rankName) {
    if (!rankName) return 0;
    let cleanRankName = rankName.toLowerCase();
    const romanMap = { iii: '3', ii: '2', i: '1' };
    ['iron', 'bronze', 'silver', 'gold', 'platinum', 'diamond', 'ascendant', 'immortal'].forEach(rankRoot => {
        cleanRankName = cleanRankName.replace(
            new RegExp(`\\b${rankRoot}\\s+(iii|ii|i)\\b`, 'g'),
            (_, roman) => `${rankRoot} ${romanMap[roman]}`
        );
    });
    for (let i = 0; i < RANKS.length; i++) {
        if (cleanRankName.includes(RANKS[i].toLowerCase())) {
            return i;
        }
    }
    return 0;
}

/**
 * Calculates the average rank of a list of players.
 * 
 * @param {Array} players List of players.
 * @return {string} Average rank name.
 */
function averageRankName(players) {
    const rankIndexes = players
        .map(player => getRankIndex(player.rank || ""))
        .filter(idx => idx > 0);
    if (rankIndexes.length === 0) {
        return "Unranked";
    }
    const sum = rankIndexes.reduce((a, b) => a + b, 0);
    const avgIdx = Math.round(sum / rankIndexes.length);
    return RANKS[Math.max(0, Math.min(RANKS.length - 1, avgIdx))];
}

/**
 * Calculates a player's tracker score out of 1000 dynamically by querying the GBR backend model.
 */
async function calculateTrackerScore(kd, hsPercent, acs, rank, peakRank, details = {}) {
    try {
        const response = await fetch('/api/calculate-score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kd: kd,
                hs_percent: hsPercent,
                acs: acs,
                rank: rank,
                peak_rank: peakRank,
                ...details
            })
        });
        const data = await response.json();
        return data.score || 0;
    } catch (err) {
        console.error("Error calculating score:", err);
        return 0;
    }
}



/**
 * Restores the HTML placeholders for the player lists and average stats.
 */
function restorePlaceholders() {
    setPostMatchLayout(false);
    resetTeamHeaders();
    const alliesList = document.getElementById('allies-player-list');
    const enemiesList = document.getElementById('enemies-player-list');
    const alliesAvg = document.getElementById('allies-avg-stats');
    const enemiesAvg = document.getElementById('enemies-avg-stats');
    
    if (alliesList && initialAlliesHtml) {
        alliesList.innerHTML = initialAlliesHtml;
    }
    if (enemiesList && initialEnemiesHtml) {
        enemiesList.innerHTML = initialEnemiesHtml;
    }
    if (alliesAvg && initialAlliesAvgHtml) {
        alliesAvg.innerHTML = initialAlliesAvgHtml;
    }
    if (enemiesAvg && initialEnemiesAvgHtml) {
        enemiesAvg.innerHTML = initialEnemiesAvgHtml;
    }
}

/**
 * Escapes dynamic text before inserting it into HTML templates.
 *
 * @param {string|number} value The value to escape.
 * @return {string} The escaped string.
 */
function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[char]));
}

/**
 * Converts Riot map paths to compact labels.
 *
 * @param {string} mapId Riot map id/path.
 * @return {string} Display label.
 */
function formatMapLabel(mapId) {
    if (!mapId) {
        return 'Unknown Map';
    }
    const lastPart = mapId.split('/').filter(Boolean).pop() || mapId;
    return lastPart.replace(/_/g, ' ');
}

/**
 * Builds an image tag when an asset URL is available.
 *
 * @param {string} src Image source.
 * @param {string} alt Image alt text.
 * @param {string} className Optional CSS class.
 * @return {string} Image HTML or an empty string.
 */
function renderImage(src, alt, className = '') {
    if (!src) {
        return '';
    }
    const classAttr = className ? ` class="${escapeHtml(className)}"` : '';
    return `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt)}"${classAttr}>`;
}

/**
 * Restores normal team section labels.
 */
function resetTeamHeaders() {
    const alliesTitle = document.querySelector('#section-allies .team-title');
    const enemiesTitle = document.querySelector('#section-enemies .team-title');
    if (alliesTitle) {
        alliesTitle.innerHTML = '<span class="title-prefix"></span>ALLIES';
    }
    if (enemiesTitle) {
        enemiesTitle.innerHTML = '<span class="title-prefix"></span>ENEMIES';
    }
}

/**
 * Toggles the one-column post-match layout.
 *
 * @param {boolean} enabled True when showing the last match summary.
 */
function setPostMatchLayout(enabled) {
    const dashboard = document.querySelector('.dashboard-main');
    if (dashboard) {
        dashboard.classList.toggle('post-match-mode', enabled);
    }
}

/**
 * Returns the CSS class name for a given tracker score.
 * 
 * @param {number} score The player's tracker score.
 * @return {string} The CSS class name.
 */
function getScoreClass(score) {
    if (score >= 800) {
        return 'score-excellent';
    }
    if (score >= 600) {
        return 'score-good';
    }
    if (score >= 400) {
        return 'score-average';
    }
    return 'score-low';
}

/**
 * Renders a card displaying a custom text message inside a team list.
 * 
 * @param {boolean} isAllies True if allies column, false if enemies.
 * @param {string} message The message to show in the card.
 */
function renderMessageState(isAllies, message) {
    const listContainer = document.getElementById(isAllies ? 'allies-player-list' : 'enemies-player-list');
    const avgStatsEl = document.getElementById(isAllies ? 'allies-avg-stats' : 'enemies-avg-stats');
    
    if (listContainer) {
        listContainer.innerHTML = `
            <div class="empty-state-card">
                <span class="empty-state-text">${message}</span>
            </div>
        `;
    }
    if (avgStatsEl) {
        avgStatsEl.textContent = 'AVG ACS: -- | AVG KD: --';
    }
}

/**
 * Renders the local player's completed match summary.
 *
 * @param {Object|null} summary Last match summary.
 * @param {string} status Backend loading status.
 */
function renderPostMatchSummary(summary, status) {
    setPostMatchLayout(true);
    const alliesTitle = document.querySelector('#section-allies .team-title');
    const alliesAvg = document.getElementById('allies-avg-stats');
    const alliesList = document.getElementById('allies-player-list');

    if (alliesTitle) {
        alliesTitle.innerHTML = '<span class="title-prefix"></span>LAST MATCH';
    }

    if (!alliesList) {
        return;
    }

    if (!summary) {
        if (alliesAvg) {
            alliesAvg.textContent = status === 'loading' ? 'FETCHING MATCH DETAILS' : 'MATCH ENDED';
        }
        alliesList.innerHTML = `
            <div class="empty-state-card">
                <span class="empty-state-text">Loading match stats...</span>
            </div>
        `;
        return;
    }

    const resultClass = summary.won ? 'victory' : 'defeat';
    const mapLabel = formatMapLabel(summary.map_id);
    const queueLabel = formatGameMode(summary.queue_id) || 'Unknown queue';
    const rrChange = Number(summary.rr_change || 0);
    const mapStyle = summary.map_banner_url ? ` style="background-image: url('${escapeHtml(summary.map_banner_url)}')"` : '';
    const rankupHtml = summary.rankup ? `
        <span class="rankup-badge">
            ${renderImage(summary.rank_before_icon_url, summary.rank_before || 'Rank before')}
            ${escapeHtml(summary.rank_before || 'Previous')}
            <span class="rankup-arrow">↑</span>
            ${renderImage(summary.rank_after_icon_url, summary.rank_after || 'Rank after')}
            ${escapeHtml(summary.rank_after || 'Next')}
        </span>
    ` : '';
    if (alliesAvg) {
        alliesAvg.textContent = `${summary.result} | ${summary.scoreline} | ${queueLabel} | ${rrChange >= 0 ? '+' : ''}${rrChange} RR`;
    }

    alliesList.innerHTML = `
        <div class="post-match-card ${resultClass} ${summary.map_banner_url ? 'has-map-banner' : ''}"${mapStyle}>
            <div class="post-match-header">
                <div>
                    <span class="post-match-kicker">YOUR GAME</span>
                    <h3 class="post-match-result">${escapeHtml(summary.result)}</h3>
                </div>
                <div class="post-match-scoreline">${escapeHtml(summary.scoreline)}</div>
            </div>
            <div class="post-match-meta">
                ${summary.agent_icon_url ? `<span>${renderImage(summary.agent_icon_url, summary.agent)}${escapeHtml(summary.agent)}</span>` : `<span>${escapeHtml(summary.agent)}</span>`}
                <span>${escapeHtml(mapLabel)}</span>
                <span>${escapeHtml(queueLabel)}</span>
                ${rankupHtml}
            </div>
            <div class="post-match-stats">
                <div class="post-match-stat">
                    <span class="stat-label">K / D / A</span>
                    <span class="stat-value">${summary.kills || 0} / ${summary.deaths || 0} / ${summary.assists || 0}</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">KD</span>
                    <span class="stat-value">${Number(summary.kd || 0).toFixed(2)}</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">KDA</span>
                    <span class="stat-value">${Number(summary.kda || 0).toFixed(2)}</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">ACS</span>
                    <span class="stat-value">${summary.acs || 0}</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">HS%</span>
                    <span class="stat-value">${Number(summary.hs_percent || 0).toFixed(1)}%</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">SCORE</span>
                    <span class="stat-value">${summary.score || 0}</span>
                </div>
                <div class="post-match-stat">
                    <span class="stat-label">RR</span>
                    <span class="stat-value">${rrChange >= 0 ? '+' : ''}${rrChange}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders the current dashboard view from session data.
 *
 * @param {Object} data The backend session data.
 */
function renderDashboard(data) {
    if (data.status !== 'connected') {
        restorePlaceholders();
        return;
    }

    if (data.game_phase === 'PREGAME') {
        setPostMatchLayout(false);
        resetTeamHeaders();
        if (data.allies && data.allies.length > 0) {
            renderPlayerList(data.allies, true);
        } else {
            renderMessageState(true, 'Loading draft allies...');
        }
        renderMessageState(false, 'Enemies hidden during Agent Select');
    } else if (data.game_phase === 'CORE-GAME') {
        setPostMatchLayout(false);
        resetTeamHeaders();
        if (data.allies && data.allies.length > 0) {
            renderPlayerList(data.allies, true);
        } else {
            renderMessageState(true, 'Loading allies...');
        }

        if (data.enemies && data.enemies.length > 0) {
            renderPlayerList(data.enemies, false);
        } else {
            renderMessageState(false, 'Loading enemies...');
        }
    } else if (data.last_match || data.last_match_status === 'loading') {
        renderPostMatchSummary(data.last_match, data.last_match_status);
    } else {
        setPostMatchLayout(false);
        resetTeamHeaders();
        const mapLower = data.map_id ? data.map_id.toLowerCase() : '';
        if (mapLower.includes('range') || mapLower.includes('poveglia')) {
            renderMessageState(true, 'Practice Range Active');
            renderMessageState(false, 'No enemies in Range');
        } else {
            renderMessageState(true, 'Waiting for match pre-game...');
            renderMessageState(false, 'Waiting for match core-game...');
        }
    }
}

/**
 * Fetches the current session status from the FastAPI backend.
 * 
 * @return {Promise<void>} Resolves when status is fetched and UI is updated.
 */
async function fetchSessionStatus() {
    try {
        const response = await fetch('/api/session-status');
        if (response.ok) {
            const data = await response.json();
            currentPuuid = data.puuid;
            updateConnectionUI(data);
            updateSessionWidget(data.session_summary);
            renderDashboard(data);
            fetchCareer();
        } else {
            updateConnectionUI({ status: 'offline', game_phase: 'OFFLINE' });
            restorePlaceholders();
        }
    } catch (error) {
        updateConnectionUI({ status: 'offline', game_phase: 'OFFLINE' });
        restorePlaceholders();
    }
}

/**
 * Fetches career stats for the current account.
 */
async function fetchCareer() {
    try {
        const response = await fetch('/api/career');
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        renderCareer(data);
    } catch (error) {
        // Keep the last career render if a polling tick fails.
    }
}

/**
 * Imports recent competitive matches into the local database.
 */
async function importCompetitiveHistory() {
    const button = document.getElementById('career-import-button');
    const status = document.getElementById('career-import-status');
    if (button) {
        button.disabled = true;
    }
    if (status) {
        status.textContent = 'Importing...';
    }

    try {
        const response = await fetch('/api/backfill/competitive?limit=20', { method: 'POST' });
        const result = await response.json();
        if (!response.ok || result.status !== 'ok') {
            throw new Error(result.message || 'Import failed');
        }
        if (status) {
            status.textContent = `${result.imported} imported · ${result.updated || 0} updated · ${result.skipped} skipped`;
        }
        updateSessionWidget(result.session_summary);
        await fetchCareer();
    } catch (error) {
        if (status) {
            status.textContent = 'Import failed';
        }
    } finally {
        if (button) {
            button.disabled = false;
        }
    }
}

/**
 * Renders career aggregate stats and match history.
 *
 * @param {Object} career Career payload.
 */
/**
 * Applies the career game mode filter and updates the UI accordingly.
 */
async function applyCareerFilter() {
    if (!lastCareerData) return;
    
    const filterSelect = document.getElementById('career-mode-filter');
    const activeFilter = filterSelect ? filterSelect.value : 'all';
    
    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    };
    
    const matches = lastCareerData.recent_matches || [];
    
    // Filter matches
    const filteredMatches = matches.filter(match => {
        if (activeFilter === 'all') return true;
        return (match.gamemode || '').trim().toLowerCase() === activeFilter;
    });
    
    // Update Stats Card Grid
    if (activeFilter === 'all') {
        const rrDelta = Number(lastCareerData.rr_delta || 0);
        setText('career-player', lastCareerData.player_name || 'No account loaded');
        setText('career-matches', lastCareerData.matches || 0);
        setText('career-winrate', `${Number(lastCareerData.win_rate || 0).toFixed(1)}%`);
        setText('career-kd', Number(lastCareerData.avg_kd || 0).toFixed(2));
        setText('career-hs', `${Number(lastCareerData.avg_hs_percent || 0).toFixed(1)}%`);
        setText('career-acs', lastCareerData.avg_acs || 0);
        setText('career-score', lastCareerData.tracker_score || 0);
        setText('career-rr', `${rrDelta >= 0 ? '+' : ''}${rrDelta}`);
    } else {
        const count = filteredMatches.length;
        let wins = 0;
        let rrDelta = 0;
        let totalACS = 0;
        let totalKD = 0;
        let totalHS = 0;
        
        filteredMatches.forEach(m => {
            if (m.win_loss === 'WIN' || m.won) {
                wins++;
            }
            rrDelta += Number(m.rr_change || 0);
            totalACS += Number(m.acs || 0);
            totalKD += Number(m.kd || 0);
            totalHS += Number(m.hs_percent || 0);
        });
        
        const winRate = count ? ((wins / count) * 100).toFixed(1) : '0.0';
        const avgACS = count ? Math.round(totalACS / count) : 0;
        const avgKD = count ? (totalKD / count).toFixed(2) : '0.00';
        const avgHS = count ? (totalHS / count).toFixed(1) : '0.0';
        
        let trackerScore = 0;
        if (count) {
            const currentRank = lastCareerData.current_rank || 'Unranked';
            trackerScore = await calculateTrackerScore(Number(avgKD), Number(avgHS), avgACS, currentRank, currentRank);
        }
        
        setText('career-player', lastCareerData.player_name || 'No account loaded');
        setText('career-matches', count);
        setText('career-winrate', `${winRate}%`);
        setText('career-kd', avgKD);
        setText('career-hs', `${avgHS}%`);
        setText('career-acs', avgACS);
        setText('career-score', trackerScore);
        setText('career-rr', `${rrDelta >= 0 ? '+' : ''}${rrDelta}`);
    }
    
    // Update player rank in UI
    const rankEl = document.getElementById('career-rank');
    if (rankEl) {
        rankEl.innerHTML = `
            ${renderImage(lastCareerData.current_rank_icon_url, lastCareerData.current_rank || 'Rank')}
            <span class="career-rank-name">${escapeHtml(lastCareerData.current_rank || 'Unranked')}</span>
        `;
    }
    
    // Update History List
    const historyEl = document.getElementById('career-history');
    if (!historyEl) return;
    
    if (filteredMatches.length === 0) {
        historyEl.innerHTML = `
            <div class="empty-state-card">
                <span class="empty-state-text">No matches found for this mode</span>
            </div>
        `;
    } else {
        historyEl.innerHTML = filteredMatches.map(match => renderCareerMatch(match)).join('');
    }
}

/**
 * Renders career aggregate stats and match history.
 *
 * @param {Object} career Career payload.
 */
function renderCareer(career) {
    lastCareerData = career;
    
    // 1. Gather unique modes from the recent matches to populate the filter dropdown
    const uniqueModes = new Set();
    const matches = career.recent_matches || [];
    matches.forEach(match => {
        if (match.gamemode) {
            uniqueModes.add(match.gamemode.trim().toLowerCase());
        }
    });

    const filterSelect = document.getElementById('career-mode-filter');
    if (filterSelect) {
        const previousSelection = filterSelect.value || 'all';
        
        // Rebuild select options only if the unique modes list has changed
        const currentOptions = Array.from(filterSelect.options).map(o => o.value);
        const newOptions = ['all', ...Array.from(uniqueModes).sort()];
        
        if (JSON.stringify(currentOptions) !== JSON.stringify(newOptions)) {
            filterSelect.innerHTML = '';
            
            const allOpt = document.createElement('option');
            allOpt.value = 'all';
            allOpt.textContent = 'ALL MODES';
            filterSelect.appendChild(allOpt);
            
            Array.from(uniqueModes).sort().forEach(mode => {
                const opt = document.createElement('option');
                opt.value = mode;
                opt.textContent = formatGameMode(mode);
                filterSelect.appendChild(opt);
            });
        }
        
        if (newOptions.includes(previousSelection)) {
            filterSelect.value = previousSelection;
        } else {
            filterSelect.value = 'all';
        }
    }
    
    // 2. Apply the current filter and render stats & history
    applyCareerFilter();
}

/**
 * Renders a single career match row.
 *
 * @param {Object} match Match payload.
 * @return {string} HTML string.
 */
function renderCareerMatch(match) {
    const won = match.win_loss === 'WIN' || match.won;
    const resultClass = won ? 'victory' : 'defeat';
    const resultText = won ? 'VICTORY' : 'DEFEAT';
    const rr = Number(match.rr_change || 0);
    const bannerStyle = match.map_banner_url ? ` style="background-image: url('${escapeHtml(match.map_banner_url)}')"` : '';
    const rankHtml = match.rankup ? `
        <div class="career-match-rank">
            ${renderImage(match.rank_before_icon_url, match.rank_before || 'Before')}
            <span>${escapeHtml(match.rank_before || 'Before')}</span>
            <span class="rankup-arrow">↑</span>
            ${renderImage(match.rank_after_icon_url, match.rank_after || 'After')}
            <span>${escapeHtml(match.rank_after || 'After')}</span>
        </div>
    ` : match.rank_after ? `
        <div class="career-match-rank">
            ${renderImage(match.rank_after_icon_url, match.rank_after)}
            <span>${escapeHtml(match.rank_after)}</span>
        </div>
    ` : '';

    return `
        <div class="career-match-card" data-match-id="${escapeHtml(match.match_id)}">
            <div class="career-map-banner"${bannerStyle}></div>
            <div class="career-match-body">
                <div class="career-match-main">
                    <span class="career-match-result ${resultClass}">${resultText}</span>
                    <span class="career-match-meta">${escapeHtml(match.map_name || formatMapLabel(match.map || match.map_id))} · ${escapeHtml(formatGameMode(match.gamemode))} · ${rr >= 0 ? '+' : ''}${rr} RR</span>
                    ${rankHtml}
                </div>
                <div class="career-match-agent">
                    ${renderImage(match.agent_icon_url, match.agent || 'Agent')}
                    <span>${escapeHtml(match.agent || 'Unknown Agent')}</span>
                </div>
                <div class="career-match-stats">
                    <span class="stat-box"><span class="stat-label">KDA</span><span class="stat-value">${match.kills || 0}/${match.deaths || 0}/${match.assists || 0}</span></span>
                    <span class="stat-box"><span class="stat-label">KD</span><span class="stat-value">${Number(match.kd || 0).toFixed(2)}</span></span>
                    <span class="stat-box"><span class="stat-label">HS%</span><span class="stat-value">${Number(match.hs_percent || 0).toFixed(1)}%</span></span>
                    <span class="stat-box"><span class="stat-label">ACS</span><span class="stat-value">${match.acs || 0}</span></span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Opens the Match details modal and renders the player leaderboard.
 * 
 * @param {string} matchId The ID of the match to display.
 */
async function openMatchDetailsModal(matchId) {
    const modal = document.getElementById('match-modal');
    if (!modal) return;
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Render loading state in lists
    const alliesList = document.getElementById('modal-allies-list');
    const enemiesList = document.getElementById('modal-enemies-list');
    
    if (alliesList) alliesList.innerHTML = '<div class="empty-state-card"><span class="empty-state-text">Chargement des détails...</span></div>';
    if (enemiesList) enemiesList.innerHTML = '<div class="empty-state-card"><span class="empty-state-text">Chargement des détails...</span></div>';
    
    // Reset metadata
    const resultEl = document.getElementById('modal-match-result');
    if (resultEl) {
        resultEl.textContent = 'CHARGEMENT...';
        resultEl.className = 'modal-match-result';
    }
    
    const banner = document.getElementById('modal-header-banner');
    if (banner) banner.style.backgroundImage = '';
    
    const mapEl = document.getElementById('modal-match-map');
    const modeEl = document.getElementById('modal-match-mode');
    const scorelineEl = document.getElementById('modal-match-scoreline');
    
    if (mapEl) mapEl.textContent = '--';
    if (modeEl) modeEl.textContent = '--';
    if (scorelineEl) scorelineEl.textContent = '--';
    
    try {
        const response = await fetch(`/api/match-leaderboard/${matchId}`);
        const data = await response.json();
        
        if (!response.ok || data.status !== 'ok') {
            const errorMsg = data.message || 'Une erreur est survenue lors de la récupération des détails.';
            if (alliesList) alliesList.innerHTML = `<div class="empty-state-card"><span class="empty-state-text" style="color: var(--valorant-red);">${escapeHtml(errorMsg)}</span></div>`;
            if (enemiesList) enemiesList.innerHTML = '';
            if (resultEl) {
                resultEl.textContent = 'ERREUR';
                resultEl.className = 'modal-match-result defeat';
            }
            return;
        }
        
        // Render header details
        if (banner && data.map_banner_url) {
            banner.style.backgroundImage = `url('${escapeHtml(data.map_banner_url)}')`;
        }
        
        if (resultEl) {
            resultEl.textContent = data.result;
            resultEl.className = `modal-match-result ${data.result.toLowerCase()}`;
        }
        
        if (mapEl) mapEl.textContent = formatMapLabel(data.map_id);
        if (modeEl) modeEl.textContent = formatGameMode(data.queue_id) || 'CUSTOM';
        if (scorelineEl) scorelineEl.textContent = data.scoreline;
        
        // Render allies & enemies lists
        if (alliesList) {
            alliesList.innerHTML = data.allies.map(p => renderLeaderboardPlayerCard(p)).join('');
        }
        if (enemiesList) {
            enemiesList.innerHTML = data.enemies.map(p => renderLeaderboardPlayerCard(p)).join('');
        }
    } catch (error) {
        if (alliesList) alliesList.innerHTML = `<div class="empty-state-card"><span class="empty-state-text" style="color: var(--valorant-red);">Erreur réseau</span></div>`;
        if (enemiesList) enemiesList.innerHTML = '';
        if (resultEl) {
            resultEl.textContent = 'ERREUR';
            resultEl.className = 'modal-match-result defeat';
        }
    }
}

/**
 * Generates HTML for a player card in the leaderboard modal.
 * 
 * @param {Object} player The player data.
 * @return {string} HTML markup.
 */
function renderLeaderboardPlayerCard(player) {
    const scoreClass = getScoreClass(player.score);
    const selfClass = player.is_self ? ' self-card' : '';
    const agentInitial = player.agent ? player.agent.charAt(0) : 'U';
    
    const agentAvatarHtml = player.agent_icon_url
        ? renderImage(player.agent_icon_url, player.agent || 'Agent')
        : `<span class="placeholder-avatar">${agentInitial}</span>`;
    const rankIconHtml = renderImage(player.rank_icon_url, player.rank || 'Rank', 'rank-icon');
    
    return `
        <div class="player-card${selfClass}">
            <div class="player-identity">
                <div class="agent-avatar">
                    ${agentAvatarHtml}
                </div>
                <div class="player-names">
                    <span class="player-tag">${escapeHtml(player.agent)}</span>
                    <span class="player-name-id">${escapeHtml(player.name)}</span>
                </div>
            </div>
            <div class="player-rank">
                <div class="rank-name">${rankIconHtml}${escapeHtml(player.rank)}</div>
            </div>
            <div class="player-stats" style="grid-column: span 2; justify-content: flex-end;">
                <div class="stat-box">
                    <span class="stat-label">K/D/A</span>
                    <span class="stat-value" style="font-size: 0.85rem;">${player.kills}/${player.deaths}/${player.assists}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">KD</span>
                    <span class="stat-value">${Number(player.kd || 0).toFixed(2)}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">HS%</span>
                    <span class="stat-value">${Number(player.hs_percent || 0).toFixed(1)}%</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">ACS</span>
                    <span class="stat-value">${player.acs}</span>
                </div>
                <div class="stat-box tracker-score-box">
                    <span class="stat-label">SCORE</span>
                    <span class="stat-value ${scoreClass}">${player.score}</span>
                </div>
            </div>
        </div>
    `;
}

function getAllMatchPlayers() {
    if (!currentMatchDetailsData) return [];
    return [...(currentMatchDetailsData.allies || []), ...(currentMatchDetailsData.enemies || [])];
}

function signedValue(value) {
    const numeric = Number(value || 0);
    return `${numeric >= 0 ? '+' : ''}${numeric}`;
}

function signedClass(value) {
    const numeric = Number(value || 0);
    if (numeric > 0) return 'positive';
    if (numeric < 0) return 'negative';
    return '';
}

function setActiveMatchTab(tabName) {
    currentMatchDetailsTab = tabName;
    document.querySelectorAll('.modal-tab').forEach(button => {
        button.classList.toggle('active', button.dataset.matchTab === tabName);
    });
}

function renderMatchDetailsTab() {
    const contentEl = document.getElementById('modal-tab-content');
    if (!contentEl || !currentMatchDetailsData) return;

    if (currentMatchDetailsTab === 'performance') {
        contentEl.innerHTML = renderPerformanceTab();
    } else if (currentMatchDetailsTab === 'economy') {
        contentEl.innerHTML = renderEconomyTab();
    } else if (currentMatchDetailsTab === 'rounds') {
        contentEl.innerHTML = renderRoundsTab();
    } else if (currentMatchDetailsTab === 'duels') {
        contentEl.innerHTML = renderDuelsTab();
    } else {
        contentEl.innerHTML = renderScoreboardTab();
    }
}

function renderMatchTeamStrip() {
    const allies = currentMatchDetailsData?.allies || [];
    const enemies = currentMatchDetailsData?.enemies || [];
    const teamIcons = players => players.map(player => `
        <button class="match-agent-chip ${player.is_self ? 'self' : ''}" type="button" data-performance-puuid="${escapeHtml(player.puuid)}" title="${escapeHtml(player.name)}">
            ${player.agent_icon_url ? renderImage(player.agent_icon_url, player.agent || 'Agent') : `<span>${escapeHtml((player.agent || '?').charAt(0))}</span>`}
        </button>
    `).join('');

    return `
        <div class="match-team-strip">
            <div class="team-strip-side allies"><span>Team A</span>${teamIcons(allies)}</div>
            <div class="team-strip-vs">VS</div>
            <div class="team-strip-side enemies">${teamIcons(enemies)}<span>Team B</span></div>
        </div>
    `;
}

function renderScoreboardTab() {
    return `
        ${renderRoundOutcomeStrip()}
        <div class="match-table-wrap">
            ${renderScoreboardTeam('Team A', currentMatchDetailsData.allies || [], 'allies')}
            ${renderScoreboardTeam('Team B', currentMatchDetailsData.enemies || [], 'enemies')}
        </div>
    `;
}

function renderScoreboardTeam(label, players, side) {
    const avgRank = averageRankName(players);
    const rows = players.map(player => `
        <tr class="${player.is_self ? 'self-row' : ''}">
            <td class="score-player-cell">
                <div class="score-player-avatar">${player.agent_icon_url ? renderImage(player.agent_icon_url, player.agent || 'Agent') : ''}</div>
                <div>
                    <div class="score-player-name">${escapeHtml(player.name)}</div>
                    <div class="score-player-sub">${escapeHtml(player.agent)} / ${escapeHtml(player.rank)}</div>
                </div>
            </td>
            <td>${player.rank_icon_url ? renderImage(player.rank_icon_url, player.rank || 'Rank', 'rank-icon') : ''}</td>
            <td>${player.score || 0}</td>
            <td class="highlight-cell">${player.acs || 0}</td>
            <td>${player.kills || 0}</td>
            <td>${player.deaths || 0}</td>
            <td>${player.assists || 0}</td>
            <td class="${signedClass((player.kills || 0) - (player.deaths || 0))}">${signedValue((player.kills || 0) - (player.deaths || 0))}</td>
            <td class="${signedClass(player.dda)}">${signedValue(player.dda)}</td>
            <td>${Number(player.adr || 0).toFixed(1)}</td>
            <td>${Number(player.hs_percent || 0).toFixed(0)}%</td>
            <td>${Number(player.kast || 0).toFixed(0)}%</td>
            <td>${player.fk || 0}</td>
            <td>${player.fd || 0}</td>
            <td>${player.mk || 0}</td>
        </tr>
    `).join('');

    return `
        <section class="scoreboard-team ${side}">
            <div class="scoreboard-team-header">
                <span>${label}</span>
                <span>Avg. Rank: ${escapeHtml(avgRank)}</span>
            </div>
            <table class="match-score-table">
                <thead>
                    <tr>
                        <th>Player</th><th>Rank</th><th>TRS</th><th>ACS</th><th>K</th><th>D</th><th>A</th><th>+/-</th><th>DDA</th><th>ADR</th><th>HS%</th><th>KAST</th><th>FK</th><th>FD</th><th>MK</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>
    `;
}

function renderRoundOutcomeStrip() {
    const rounds = currentMatchDetailsData?.rounds || [];
    if (!rounds.length) return '';
    return `
        <div class="round-outcome-strip">
            ${rounds.map(round => `
                <div class="round-outcome ${round.ally_won ? 'ally' : 'enemy'}" title="${escapeHtml(round.result)}">
                    <span>${round.round}</span>
                    <strong>${round.ally_won ? 'A' : 'B'}</strong>
                </div>
            `).join('')}
        </div>
    `;
}

function renderPerformanceTab() {
    const players = getAllMatchPlayers();
    const selected = players.find(player => player.puuid === currentPerformancePuuid) || players[0];
    if (!selected) return '<div class="empty-state-card"><span class="empty-state-text">No player data</span></div>';
    const rounds = currentMatchDetailsData.rounds || [];
    const killBars = rounds.map(round => {
        const involved = round.events || [];
        const kills = involved.filter(event => event.killer === selected.puuid).length;
        const deaths = involved.filter(event => event.victim === selected.puuid).length;
        return `<div class="performance-round ${kills ? 'has-kill' : ''} ${deaths ? 'has-death' : ''}"><span>${round.round}</span><strong>${kills || '-'}</strong></div>`;
    }).join('');

    return `
        ${renderMatchTeamStrip()}
        <section class="performance-hero">
            <div class="performance-agent-art">${selected.agent_full_url ? renderImage(selected.agent_full_url, selected.agent || 'Agent') : ''}</div>
            <div class="performance-main">
                <div class="performance-name">${selected.rank_icon_url ? renderImage(selected.rank_icon_url, selected.rank || 'Rank', 'rank-icon') : ''}${escapeHtml(selected.name)}</div>
                <div class="performance-agent">${escapeHtml(selected.agent)} / ${escapeHtml(selected.rank)}</div>
                <div class="performance-stats">
                    <span><small>K/D/A</small><strong>${selected.kills}/${selected.deaths}/${selected.assists}</strong></span>
                    <span><small>K/D</small><strong>${Number(selected.kd || 0).toFixed(2)}</strong></span>
                    <span><small>ADR</small><strong>${Number(selected.adr || 0).toFixed(1)}</strong></span>
                    <span><small>ACS</small><strong>${selected.acs || 0}</strong></span>
                    <span><small>HS%</small><strong>${Number(selected.hs_percent || 0).toFixed(1)}%</strong></span>
                    <span><small>KAST</small><strong>${Number(selected.kast || 0).toFixed(0)}%</strong></span>
                </div>
            </div>
        </section>
        <div class="performance-rounds">${killBars}</div>
        <div class="performance-splits">
            <div class="split-panel"><h3>Damage</h3><p>Dealt <strong>${selected.damage_dealt || 0}</strong></p><p>Received <strong>${selected.damage_received || 0}</strong></p></div>
            <div class="split-panel"><h3>Openers</h3><p>First Kills <strong>${selected.fk || 0}</strong></p><p>First Deaths <strong>${selected.fd || 0}</strong></p></div>
            <div class="split-panel"><h3>Economy</h3><p>Avg. Loadout <strong>${selected.avg_loadout || 0}</strong></p><p>Avg. Bank <strong>${selected.avg_bank || 0}</strong></p></div>
        </div>
    `;
}

function renderEconomyTab() {
    const rounds = currentMatchDetailsData?.rounds || [];
    const maxValue = Math.max(1, ...rounds.flatMap(round => [round.ally_loadout || 0, round.enemy_loadout || 0]));
    return `
        <section class="economy-panel">
            <div class="economy-header">
                <h3>Economy</h3>
                <span>Loadout value by round</span>
            </div>
            <div class="economy-chart">
                ${rounds.map(round => `
                    <div class="economy-round">
                        <div class="economy-bars">
                            <span class="ally-bar" style="height:${Math.max(4, ((round.ally_loadout || 0) / maxValue) * 100)}%"></span>
                            <span class="enemy-bar" style="height:${Math.max(4, ((round.enemy_loadout || 0) / maxValue) * 100)}%"></span>
                        </div>
                        <small>${round.round}</small>
                    </div>
                `).join('')}
            </div>
            ${renderRoundOutcomeStrip()}
        </section>
        ${renderScoreboardTab()}
    `;
}

function renderRoundsTab() {
    const rounds = currentMatchDetailsData?.rounds || [];
    return `
        <div class="rounds-grid">
            ${rounds.map(round => `
                <section class="round-card ${round.ally_won ? 'ally' : 'enemy'}">
                    <div class="round-card-head">
                        <span>Round ${round.round}</span>
                        <strong>${round.ally_won ? 'Team A Win' : 'Team B Win'}</strong>
                    </div>
                    <div class="round-card-stats">
                        <span>A kills <strong>${round.ally_kills}</strong></span>
                        <span>B kills <strong>${round.enemy_kills}</strong></span>
                        <span>A loadout <strong>${round.ally_loadout}</strong></span>
                        <span>B loadout <strong>${round.enemy_loadout}</strong></span>
                    </div>
                    <div class="round-events">
                        ${(round.events || []).slice(0, 5).map(event => renderRoundEvent(event)).join('') || '<span class="muted">No kills recorded</span>'}
                    </div>
                </section>
            `).join('')}
        </div>
    `;
}

function renderRoundEvent(event) {
    const players = getAllMatchPlayers();
    const killer = players.find(player => player.puuid === event.killer);
    const victim = players.find(player => player.puuid === event.victim);
    return `
        <div class="round-event">
            <span>${Math.round(Number(event.round_time || 0) / 1000)}s</span>
            <strong>${escapeHtml(killer?.name || 'Unknown')}</strong>
            <span>vs</span>
            <strong>${escapeHtml(victim?.name || 'Unknown')}</strong>
        </div>
    `;
}

function renderDuelsTab() {
    const allies = currentMatchDetailsData?.allies || [];
    const enemies = currentMatchDetailsData?.enemies || [];
    const duels = currentMatchDetailsData?.duels || {};
    return `
        <div class="duels-summary">
            ${renderDuelHighlight('Top Rivalry', allies, enemies, duels, 'balanced')}
            ${renderDuelHighlight('Mismatch A', allies, enemies, duels, 'ally')}
            ${renderDuelHighlight('Mismatch B', allies, enemies, duels, 'enemy')}
        </div>
        <div class="duel-matrix-wrap">
            <table class="duel-matrix">
                <thead>
                    <tr>
                        <th>Team A vs Team B</th>
                        ${enemies.map(enemy => `<th>${renderDuelPlayerHeader(enemy)}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${allies.map(ally => `
                        <tr>
                            <th>${renderDuelPlayerHeader(ally)}</th>
                            ${enemies.map(enemy => {
                                const cell = duels?.[ally.puuid]?.[enemy.puuid] || { kills: 0, deaths: 0 };
                                return `<td><span class="duel-score ally">${cell.kills}</span><span class="duel-score enemy">${cell.deaths}</span></td>`;
                            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderDuelPlayerHeader(player) {
    return `
        <div class="duel-player-head">
            ${player.agent_icon_url ? renderImage(player.agent_icon_url, player.agent || 'Agent') : ''}
            <span>${escapeHtml((player.name || '').split('#')[0] || 'Unknown')}</span>
        </div>
    `;
}

function renderDuelHighlight(title, allies, enemies, duels, mode) {
    let best = null;
    allies.forEach(ally => {
        enemies.forEach(enemy => {
            const cell = duels?.[ally.puuid]?.[enemy.puuid] || { kills: 0, deaths: 0 };
            const diff = cell.kills - cell.deaths;
            const total = cell.kills + cell.deaths;
            let score = total;
            if (mode === 'ally') score = diff;
            if (mode === 'enemy') score = -diff;
            if (!best || score > best.score) {
                best = { ally, enemy, cell, score, total };
            }
        });
    });
    if (!best) return '';
    return `
        <section class="duel-highlight">
            <div>${renderDuelPlayerHeader(best.ally)}</div>
            <strong>${escapeHtml(title)}<span>VS</span></strong>
            <div>${renderDuelPlayerHeader(best.enemy)}</div>
            <p>${best.cell.kills} - ${best.cell.deaths}</p>
        </section>
    `;
}

async function openMatchDetailsModal(matchId) {
    const modal = document.getElementById('match-modal');
    if (!modal) return;

    currentMatchDetailsData = null;
    currentMatchDetailsTab = 'scoreboard';
    currentPerformancePuuid = '';
    modal.classList.remove('hidden');
    setActiveMatchTab('scoreboard');

    const contentEl = document.getElementById('modal-tab-content');
    if (contentEl) {
        contentEl.innerHTML = '<div class="empty-state-card"><span class="empty-state-text">Loading match details...</span></div>';
    }

    const resultEl = document.getElementById('modal-match-result');
    const banner = document.getElementById('modal-header-banner');
    const mapEl = document.getElementById('modal-match-map');
    const modeEl = document.getElementById('modal-match-mode');
    const durationEl = document.getElementById('modal-match-duration');
    const scorelineEl = document.getElementById('modal-match-scoreline');

    if (resultEl) {
        resultEl.textContent = 'LOADING...';
        resultEl.className = 'modal-match-result';
    }
    if (banner) banner.style.backgroundImage = '';
    if (mapEl) mapEl.textContent = '--';
    if (modeEl) modeEl.textContent = '--';
    if (durationEl) durationEl.textContent = '--';
    if (scorelineEl) scorelineEl.textContent = '--';

    try {
        const response = await fetch(`/api/match-leaderboard/${matchId}`);
        const data = await response.json();

        if (!response.ok || data.status !== 'ok') {
            const errorMsg = data.message || 'Unable to load match details.';
            if (contentEl) {
                contentEl.innerHTML = `<div class="empty-state-card"><span class="empty-state-text" style="color: var(--valorant-red);">${escapeHtml(errorMsg)}</span></div>`;
            }
            if (resultEl) {
                resultEl.textContent = 'ERROR';
                resultEl.className = 'modal-match-result defeat';
            }
            return;
        }

        if (banner && data.map_banner_url) {
            banner.style.backgroundImage = `url('${escapeHtml(data.map_banner_url)}')`;
        }
        if (resultEl) {
            resultEl.textContent = data.result;
            resultEl.className = `modal-match-result ${String(data.result || '').toLowerCase()}`;
        }
        if (mapEl) mapEl.textContent = data.map_name || formatMapLabel(data.map_id);
        if (modeEl) modeEl.textContent = formatGameMode(data.queue_id) || 'CUSTOM';
        if (durationEl) durationEl.textContent = data.duration || '--';
        if (scorelineEl) scorelineEl.textContent = data.scoreline || '--';

        currentMatchDetailsData = data;
        const selfPlayer = getAllMatchPlayers().find(player => player.is_self);
        currentPerformancePuuid = selfPlayer?.puuid || data.allies?.[0]?.puuid || data.enemies?.[0]?.puuid || '';
        renderMatchDetailsTab();
    } catch (error) {
        if (contentEl) {
            contentEl.innerHTML = '<div class="empty-state-card"><span class="empty-state-text" style="color: var(--valorant-red);">Network error</span></div>';
        }
        if (resultEl) {
            resultEl.textContent = 'ERROR';
            resultEl.className = 'modal-match-result defeat';
        }
    }
}

/**
 * Updates the session RR widget in the header.
 *
 * @param {Object} summary Session summary from the backend.
 */
function updateSessionWidget(summary) {
    const winsEl = document.getElementById('session-wins');
    const lossesEl = document.getElementById('session-losses');
    const rrEl = document.getElementById('session-rr-delta');

    if (!winsEl || !lossesEl || !rrEl) {
        return;
    }

    const wins = Number(summary?.wins || 0);
    const losses = Number(summary?.losses || 0);
    const rrDelta = Number(summary?.rr_delta || 0);

    winsEl.textContent = `${wins} W`;
    lossesEl.textContent = `${losses} L`;
    rrEl.textContent = `${rrDelta >= 0 ? '+' : ''}${rrDelta} RR`;
    rrEl.classList.toggle('positive', rrDelta >= 0);
    rrEl.classList.toggle('negative', rrDelta < 0);
}

/**
 * Updates the connection status indicator and text in the header.
 * 
 * @param {Object} data The state data from the backend.
 */
function updateConnectionUI(data) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    if (!indicator || !text) {
        return;
    }
    
    indicator.className = 'status-indicator';
    
    if (data.status === 'searching_game') {
        indicator.classList.add('searching');
        text.textContent = 'Searching Client...';
    } else if (data.status === 'connected') {
        indicator.classList.add('connected');
        
        let statusString = `VALORANT: ${data.game_phase}`;
        if (data.map_id) {
            const mapLower = data.map_id.toLowerCase();
            if (mapLower.includes('range') || mapLower.includes('poveglia')) {
                statusString = 'VALORANT: IN THE RANGE';
            } else if (data.queue_id) {
                statusString = `VALORANT: ${data.game_phase} (${formatGameMode(data.queue_id)})`;
            }
        } else if (data.queue_id) {
            statusString = `VALORANT: ${data.game_phase} (${formatGameMode(data.queue_id)})`;
        }
        text.textContent = statusString;
        
        if (data.player_name && data.player_name !== 'Unknown') {
            const selfNameEl = document.querySelector('.self-card .player-name-id');
            if (selfNameEl) {
                selfNameEl.textContent = data.player_name;
            }
        }
    } else {
        indicator.classList.add('disconnected');
        text.textContent = 'Client Offline';
    }
}

/**
 * Renders a list of players in the specified team container.
 * 
 * @param {Array} players The array of player objects.
 * @param {boolean} isAllies True if allies column, false if enemies.
 */
function renderPlayerList(players, isAllies) {
    const listContainer = document.getElementById(isAllies ? 'allies-player-list' : 'enemies-player-list');
    const avgStatsEl = document.getElementById(isAllies ? 'allies-avg-stats' : 'enemies-avg-stats');
    
    if (!listContainer) {
        return;
    }
    
    if (!players || players.length === 0) {
        return;
    }
    
    listContainer.innerHTML = '';
    
    let totalACS = 0;
    let totalKD = 0;
    
    players.forEach(player => {
        totalACS += Number(player.acs || 0);
        totalKD += Number(player.kd || 0);
        
        const card = document.createElement('div');
        card.className = 'player-card';
        if (isAllies && player.puuid === currentPuuid) {
            card.classList.add('self-card');
        }
        
        const agentInitial = player.agent ? player.agent.charAt(0) : 'U';
        const agentAvatarHtml = player.agent_icon_url
            ? renderImage(player.agent_icon_url, player.agent || 'Agent')
            : `<span class="placeholder-avatar">${agentInitial}</span>`;
        const rankIconHtml = renderImage(player.rank_icon_url, player.rank || 'Rank', 'rank-icon');
        
        let badgeHtml = '';
        if (player.badge) {
            let badgeClass = player.badge.toLowerCase().replace(' ', '-');
            if (player.group_id) {
                badgeClass = `premade-group-${player.group_id}`;
            }
            badgeHtml = `<span class="badge ${badgeClass}">${player.badge}</span>`;
        }
        
        const scoreVal = player.score !== undefined ? player.score : 600;
        const scoreClass = getScoreClass(scoreVal);
        const statHtml = `
                <div class="stat-box">
                    <span class="stat-label">KD</span>
                    <span class="stat-value">${Number(player.kd || 0).toFixed(2)}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">HS%</span>
                    <span class="stat-value">${Number(player.hs_percent || 0).toFixed(1)}%</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">ACS</span>
                    <span class="stat-value">${player.acs || 0}</span>
                </div>
                <div class="stat-box tracker-score-box">
                    <span class="stat-label">SCORE</span>
                    <span class="stat-value ${scoreClass}">${scoreVal}</span>
                </div>
        `;
        
        card.innerHTML = `
            <div class="player-identity">
                <div class="agent-avatar">
                    ${agentAvatarHtml}
                </div>
                <div class="player-names">
                    <span class="player-tag">${player.agent}</span>
                    <span class="player-name-id">${player.name}</span>
                </div>
            </div>
            <div class="player-rank">
                <div class="rank-name">${rankIconHtml}${player.rank}</div>
                <div class="peak-rank">Peak: ${player.peak_rank}</div>
            </div>
            <div class="player-stats">
                ${statHtml}
            </div>
            <div class="player-badges">
                ${badgeHtml}
            </div>
        `;
        listContainer.appendChild(card);
    });
    
    if (avgStatsEl) {
        const avgACS = Math.round(totalACS / players.length);
        const avgKD = (totalKD / players.length).toFixed(2);
        avgStatsEl.textContent = `AVG ACS: ${avgACS} | AVG KD: ${avgKD}`;
    }
}

/**
 * Initializes the dashboard application.
 */
function init() {
    const importButton = document.getElementById('career-import-button');
    if (importButton) {
        importButton.addEventListener('click', importCompetitiveHistory);
    }
    const filterSelect = document.getElementById('career-mode-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', applyCareerFilter);
    }
    
    // Career match card click listener
    const careerHistory = document.getElementById('career-history');
    if (careerHistory) {
        careerHistory.addEventListener('click', (e) => {
            const card = e.target.closest('.career-match-card');
            if (card) {
                const matchId = card.dataset.matchId;
                if (matchId) {
                    openMatchDetailsModal(matchId);
                }
            }
        });
    }
    
    // Modal close listeners
    const closeBtn = document.getElementById('modal-close-button');
    const modal = document.getElementById('match-modal');
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        
        // Close modal when clicking outside content
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }

    const modalTabs = document.getElementById('modal-tabs');
    if (modalTabs) {
        modalTabs.addEventListener('click', (event) => {
            const button = event.target.closest('[data-match-tab]');
            if (!button) return;
            setActiveMatchTab(button.dataset.matchTab);
            renderMatchDetailsTab();
        });
    }

    const modalContent = document.getElementById('modal-tab-content');
    if (modalContent) {
        modalContent.addEventListener('click', (event) => {
            const button = event.target.closest('[data-performance-puuid]');
            if (!button) return;
            currentPerformancePuuid = button.dataset.performancePuuid;
            setActiveMatchTab('performance');
            renderMatchDetailsTab();
        });
    }
    
    fetchSessionStatus();
    setInterval(fetchSessionStatus, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    const alliesList = document.getElementById('allies-player-list');
    const enemiesList = document.getElementById('enemies-player-list');
    const alliesAvg = document.getElementById('allies-avg-stats');
    const enemiesAvg = document.getElementById('enemies-avg-stats');
    if (alliesList) {
        initialAlliesHtml = alliesList.innerHTML;
    }
    if (enemiesList) {
        initialEnemiesHtml = enemiesList.innerHTML;
    }
    if (alliesAvg) {
        initialAlliesAvgHtml = alliesAvg.innerHTML;
    }
    if (enemiesAvg) {
        initialEnemiesAvgHtml = enemiesAvg.innerHTML;
    }
    init();
});
