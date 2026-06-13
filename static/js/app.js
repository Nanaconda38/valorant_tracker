let currentPuuid = "";
let initialAlliesHtml = "";
let initialEnemiesHtml = "";
let initialAlliesAvgHtml = "";
let initialEnemiesAvgHtml = "";

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
    const queueLabel = summary.queue_id || 'Unknown queue';
    const rrChange = Number(summary.rr_change || 0);
    if (alliesAvg) {
        alliesAvg.textContent = `${summary.result} | ${summary.scoreline} | ${queueLabel} | ${rrChange >= 0 ? '+' : ''}${rrChange} RR`;
    }

    alliesList.innerHTML = `
        <div class="post-match-card ${resultClass}">
            <div class="post-match-header">
                <div>
                    <span class="post-match-kicker">YOUR GAME</span>
                    <h3 class="post-match-result">${escapeHtml(summary.result)}</h3>
                </div>
                <div class="post-match-scoreline">${escapeHtml(summary.scoreline)}</div>
            </div>
            <div class="post-match-meta">
                <span>${escapeHtml(summary.agent)}</span>
                <span>${escapeHtml(mapLabel)}</span>
                <span>${escapeHtml(queueLabel)}</span>
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
                statusString = `VALORANT: ${data.game_phase} (${data.queue_id})`;
            }
        } else if (data.queue_id) {
            statusString = `VALORANT: ${data.game_phase} (${data.queue_id})`;
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
                    <span class="placeholder-avatar">${agentInitial}</span>
                </div>
                <div class="player-names">
                    <span class="player-tag">${player.agent}</span>
                    <span class="player-name-id">${player.name}</span>
                </div>
            </div>
            <div class="player-rank">
                <div class="rank-name">${player.rank}</div>
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
