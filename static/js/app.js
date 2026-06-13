let currentPuuid = "";
let initialAlliesHtml = "";
let initialEnemiesHtml = "";
let initialAlliesAvgHtml = "";
let initialEnemiesAvgHtml = "";
let lastCareerData = null;

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
    for (let i = 0; i < RANKS.length; i++) {
        if (rankName.toLowerCase().includes(RANKS[i].toLowerCase())) {
            return i;
        }
    }
    return 0;
}

/**
 * Calculates a player's tracker score out of 1000.
 */
function calculateTrackerScore(kd, hsPercent, acs, rank, peakRank) {
    const acsPts = Math.min(200, Math.round((acs / 300) * 200));
    const kdPts = Math.min(200, Math.round((kd / 1.5) * 200));
    const hsPts = Math.min(200, Math.round((hsPercent / 35) * 200));
    const formPts = 125;
    const currIdx = getRankIndex(rank);
    const peakIdx = getRankIndex(peakRank);
    const gap = Math.max(0, peakIdx - currIdx);
    const gapPts = Math.max(50, 150 - (gap * 15));
    return acsPts + kdPts + hsPts + formPts + gapPts;
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
function applyCareerFilter() {
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
            trackerScore = calculateTrackerScore(Number(avgKD), Number(avgHS), avgACS, currentRank, currentRank);
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
        <div class="career-match-card">
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
