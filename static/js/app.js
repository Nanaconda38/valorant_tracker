let currentPuuid = "";
let initialAlliesHtml = "";
let initialEnemiesHtml = "";
let initialAlliesAvgHtml = "";
let initialEnemiesAvgHtml = "";
let lastCareerData = null;
let currentMatchDetailsData = null;
let currentMatchDetailsTab = 'scoreboard';
let currentPerformancePuuid = '';
let appSettings = null;
let configStatus = null;

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
 * Updates an element's text content when it exists.
 *
 * @param {string} elementId Element id.
 * @param {string|number} value Text value.
 */
function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = value;
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

const TRACKER_SCORE_BADGES = {
    low: '/static/assets/tracker-score/trs-0-199.png',
    bronze: '/static/assets/tracker-score/trs-200-399.png',
    silver: '/static/assets/tracker-score/trs-400-599.png',
    teal: '/static/assets/tracker-score/trs-600-799.png',
    elite: '/static/assets/tracker-score/trs-800-999.png',
    perfect: '/static/assets/tracker-score/trs-1000.png'
};

function getTrackerScoreBadge(score) {
    const value = Number(score || 0);
    if (value >= 1000) {
        return { src: TRACKER_SCORE_BADGES.perfect, label: 'Perfect Tracker Score' };
    }
    if (value >= 800) {
        return { src: TRACKER_SCORE_BADGES.elite, label: '800-999 Tracker Score' };
    }
    if (value >= 600) {
        return { src: TRACKER_SCORE_BADGES.teal, label: '600-799 Tracker Score' };
    }
    if (value >= 400) {
        return { src: TRACKER_SCORE_BADGES.silver, label: '400-599 Tracker Score' };
    }
    if (value >= 200) {
        return { src: TRACKER_SCORE_BADGES.bronze, label: '200-399 Tracker Score' };
    }
    return { src: TRACKER_SCORE_BADGES.low, label: '0-199 Tracker Score' };
}

function renderTrackerScore(score, variant = 'compact') {
    const value = Math.max(0, Math.min(1000, Math.round(Number(score || 0))));
    const scoreClass = getScoreClass(value);
    const badge = getTrackerScoreBadge(value);
    return `
        <span class="tracker-score-display tracker-score-${variant}">
            ${renderImage(badge.src, badge.label, 'tracker-score-badge')}
            <span class="tracker-score-number ${scoreClass}">${value}</span>
        </span>
    `;
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
                    <span class="stat-label">TRS</span>
                    <span class="stat-value tracker-score-slot">${renderTrackerScore(summary.tracker_score !== undefined && summary.tracker_score !== null ? summary.tracker_score : summary.score || 0, 'medium')}</span>
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
            status.textContent = error.message || 'Import failed';
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
    const actFilterSelect = document.getElementById('career-act-filter');
    const activeFilter = filterSelect ? filterSelect.value : 'all';
    const activeActFilter = actFilterSelect ? actFilterSelect.value : 'all';
    
    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    };
    const setTrackerScore = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = renderTrackerScore(value, 'medium');
        }
    };
    const STAT_PERCENTILE_CURVES = {
        winrate: [[35, 2], [40, 8], [45, 22], [50, 50], [55.2, 76], [60, 88], [66.7, 95], [80, 99.5]],
        kd: [[0.7, 5], [0.85, 18], [1, 50], [1.15, 72], [1.3, 85], [1.45, 94], [1.59, 98.7], [2, 99.7], [2.47, 99.9]],
        hs: [[10, 5], [15, 20], [20, 45], [25, 72], [29.1, 88], [35, 96], [40, 99]],
        acs: [[150, 8], [180, 25], [200, 45], [225, 65], [250, 80], [275, 92], [293.6, 97.1], [330, 99], [368.9, 99.8]],
        score: [[100, 1], [300, 15], [500, 40], [650, 62], [800, 80], [900, 92], [939, 97], [980, 99], [1000, 99.9]]
    };
    const percentileFromCurve = (value, curve) => {
        if (!Number.isFinite(value) || !curve?.length) {
            return null;
        }
        if (value <= curve[0][0]) {
            return curve[0][1];
        }
        for (let index = 1; index < curve.length; index++) {
            const [x1, y1] = curve[index - 1];
            const [x2, y2] = curve[index];
            if (value <= x2) {
                const t = (value - x1) / Math.max(x2 - x1, 0.0001);
                return y1 + ((y2 - y1) * t);
            }
        }
        return curve[curve.length - 1][1];
    };
    const formatPercentileRank = (percentile) => {
        if (!Number.isFinite(percentile)) {
            return 'N/A';
        }
        if (percentile >= 50) {
            const top = Math.max(0.1, 100 - percentile);
            return `Top ${top < 10 ? top.toFixed(1) : Math.round(top)}%`;
        }
        return `Bottom ${percentile < 10 ? percentile.toFixed(1) : Math.round(percentile)}%`;
    };
    const progressColorFromPercentile = (percentile) => {
        if (!Number.isFinite(percentile)) {
            return 'rgba(139, 155, 180, 0.35)';
        }
        const stops = [
            [0, [255, 70, 85]],
            [35, [255, 139, 76]],
            [55, [246, 211, 101]],
            [75, [78, 226, 184]],
            [100, [0, 240, 255]]
        ];
        const clamped = Math.max(0, Math.min(100, percentile));
        for (let index = 1; index < stops.length; index++) {
            const [prevPoint, prevColor] = stops[index - 1];
            const [nextPoint, nextColor] = stops[index];
            if (clamped <= nextPoint) {
                const t = (clamped - prevPoint) / Math.max(nextPoint - prevPoint, 0.0001);
                const color = prevColor.map((channel, channelIndex) => (
                    Math.round(channel + ((nextColor[channelIndex] - channel) * t))
                ));
                return `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            }
        }
        return 'rgb(0, 240, 255)';
    };
    const setStatPercentile = (prefix, metric, value) => {
        const labelEl = document.getElementById(`${prefix}-rank`);
        const progressEl = document.getElementById(`${prefix}-progress`);
        const percentile = percentileFromCurve(Number(value), STAT_PERCENTILE_CURVES[metric]);
        if (labelEl) {
            labelEl.textContent = formatPercentileRank(percentile);
        }
        if (progressEl) {
            const fill = Number.isFinite(percentile) ? Math.max(1, Math.min(100, percentile)) : 0;
            progressEl.style.height = `${fill}%`;
            progressEl.className = '';
            if (!Number.isFinite(percentile)) {
                progressEl.style.background = '';
                progressEl.style.color = '';
                return;
            }
            const progressColor = progressColorFromPercentile(percentile);
            progressEl.style.background = progressColor;
            progressEl.style.color = progressColor;
        }
    };
    const setProfileScoreBreakdown = (breakdown) => {
        const el = document.getElementById('career-score-breakdown');
        if (!el) {
            return;
        }
        if (!breakdown || !breakdown.available) {
            el.innerHTML = `
                <span><b>RW</b> N/A</span>
                <span><b>KAST</b> N/A</span>
                <span><b>ACS</b> N/A</span>
                <span><b>DDA</b> N/A</span>
            `;
            return;
        }
        el.innerHTML = `
            <span title="Round Win %"><b>RW</b> ${breakdown.roundWinPercent.toFixed(1)}%</span>
            <span title="Kill, Assist, Survive, Trade"><b>KAST</b> ${breakdown.avgKast.toFixed(1)}%</span>
            <span title="Average Combat Score"><b>ACS</b> ${Math.round(breakdown.avgAcs)}</span>
            <span title="Damage Delta / Round"><b>DDA</b> ${breakdown.avgDda >= 0 ? '+' : ''}${breakdown.avgDda.toFixed(1)}</span>
        `;
    };
    const averagePageTrackerScore = (pageMatches) => {
        const scores = pageMatches
            .map(match => match.tracker_score)
            .filter(score => score !== undefined && score !== null && Number.isFinite(Number(score)))
            .map(score => Number(score));
        if (!scores.length) {
            return 0;
        }
        return Math.round(scores.reduce((total, score) => total + score, 0) / scores.length);
    };
    const profileComponentScore = (value, points) => {
        if (!Number.isFinite(value)) {
            return null;
        }
        if (value <= points[0][0]) {
            return points[0][1];
        }
        for (let index = 1; index < points.length; index++) {
            const [x1, y1] = points[index - 1];
            const [x2, y2] = points[index];
            if (value <= x2) {
                const t = (value - x1) / Math.max(x2 - x1, 0.0001);
                return y1 + ((y2 - y1) * t);
            }
        }
        return points[points.length - 1][1];
    };
    const calculatePageProfileTrackerBreakdown = (pageMatches) => {
        const scoredMatches = pageMatches.filter(match => (
            match.tracker_score !== undefined
            && match.tracker_score !== null
            && Number.isFinite(Number(match.tracker_score))
        ));
        if (!scoredMatches.length) {
            return { score: 0, available: false, reason: 'no_scored_matches' };
        }

        const totalTeamRounds = scoredMatches.reduce((total, match) => total + Number(match.team_rounds || 0), 0);
        const totalEnemyRounds = scoredMatches.reduce((total, match) => total + Number(match.enemy_rounds || 0), 0);
        const roundWinPercent = (totalTeamRounds + totalEnemyRounds) > 0
            ? (totalTeamRounds / (totalTeamRounds + totalEnemyRounds)) * 100
            : (scoredMatches.filter(match => match.win_loss === 'WIN' || match.won).length / scoredMatches.length) * 100;

        const averageNumeric = (field) => {
            const values = scoredMatches
                .map(match => Number(match[field]))
                .filter(value => Number.isFinite(value));
            if (!values.length) {
                return null;
            }
            return values.reduce((total, value) => total + value, 0) / values.length;
        };

        const avgKast = averageNumeric('kast');
        const avgDda = averageNumeric('dda');
        const avgAcs = averageNumeric('acs');
        if (avgKast === null || avgDda === null || avgAcs === null) {
            return {
                score: averagePageTrackerScore(scoredMatches),
                available: false,
                reason: 'missing_profile_metrics'
            };
        }

        const roundWinScore = profileComponentScore(roundWinPercent, [
            [45, 250], [48, 430], [50, 580], [52, 740], [55, 900], [60, 980], [65, 1000]
        ]);
        const kastScore = profileComponentScore(avgKast, [
            [68, 250], [70, 420], [72, 620], [74, 780], [76, 880], [78, 950], [80, 990], [83, 1000]
        ]);
        const acsScore = profileComponentScore(avgAcs, [
            [180, 250], [200, 420], [215, 560], [240, 720], [265, 840], [295, 920], [330, 975], [370, 1000]
        ]);
        const ddaScore = profileComponentScore(avgDda, [
            [-25, 180], [-10, 400], [0, 520], [10, 660], [25, 780], [45, 860], [55, 920], [80, 970], [110, 995]
        ]);

        const rawScore = (
            (roundWinScore * 0.1)
            + (kastScore * 0.15)
            + (acsScore * 0.2)
            + (ddaScore * 0.55)
        );
        const calibratedScore = -49.4711601 + (1.08650119 * rawScore);
        return {
            score: Math.max(100, Math.min(1000, Math.round(calibratedScore))),
            available: true,
            matchCount: scoredMatches.length,
            roundWinPercent,
            avgKast,
            avgAcs,
            avgDda,
            components: {
                roundWinScore,
                kastScore,
                acsScore,
                ddaScore
            }
        };
    };
    
    const matches = lastCareerData.recent_matches || [];
    
    const filteredMatches = matches.filter(match => {
        const modeMatches = activeFilter === 'all'
            || (match.gamemode || '').trim().toLowerCase() === activeFilter;
        const actMatches = activeActFilter === 'all'
            || (match.season_id || '') === activeActFilter;
        return modeMatches && actMatches;
    });
    const rankedSummaryMatches = matches.filter(match => {
        const isCompetitive = (match.gamemode || '').trim().toLowerCase() === 'competitive';
        const actMatches = activeActFilter === 'all'
            || (match.season_id || '') === activeActFilter;
        return isCompetitive && actMatches;
    });
    const profileScoreBreakdown = calculatePageProfileTrackerBreakdown(rankedSummaryMatches);
    const rankedSummary = rankedSummaryMatches.reduce((summary, match) => {
        const kills = Number(match.kills || 0);
        const deaths = Number(match.deaths || 0);
        summary.matches += 1;
        summary.wins += (match.win_loss === 'WIN' || match.won) ? 1 : 0;
        summary.rrDelta += Number(match.rr_change || 0);
        summary.totalACS += Number(match.acs || 0);
        summary.totalHS += Number(match.hs_percent || 0);
        summary.totalKills += kills;
        summary.totalDeaths += deaths;
        return summary;
    }, {
        matches: 0,
        wins: 0,
        rrDelta: 0,
        totalACS: 0,
        totalHS: 0,
        totalKills: 0,
        totalDeaths: 0
    });
    const rankedCount = rankedSummary.matches;
    const rankedWinRate = rankedCount ? (rankedSummary.wins / rankedCount) * 100 : 0;
    const rankedACS = rankedCount ? Math.round(rankedSummary.totalACS / rankedCount) : 0;
    const rankedKD = rankedCount ? rankedSummary.totalKills / Math.max(rankedSummary.totalDeaths, 1) : 0;
    const rankedHS = rankedCount ? rankedSummary.totalHS / rankedCount : 0;
    
    setText('career-player', lastCareerData.player_name || 'No account loaded');
    setText('career-matches', rankedCount);
    setText('career-winrate', `${rankedWinRate.toFixed(1)}%`);
    setText('career-kd', rankedKD.toFixed(2));
    setText('career-hs', `${rankedHS.toFixed(1)}%`);
    setText('career-acs', rankedACS);
    setTrackerScore('career-score', profileScoreBreakdown.score);
    setProfileScoreBreakdown(profileScoreBreakdown);
    const rrEl = document.getElementById('career-rr');
    if (rrEl) {
        rrEl.textContent = `${rankedSummary.rrDelta >= 0 ? '+' : ''}${rankedSummary.rrDelta}`;
        rrEl.className = rankedSummary.rrDelta >= 0 ? 'win-text' : 'loss-text';
    }
    
    // Update Rank & RR Card details dynamically
    const currentIconEl = document.getElementById('career-card-current-icon');
    const currentNameEl = document.getElementById('career-card-current-name');
    const peakIconEl = document.getElementById('career-card-peak-icon');
    const peakNameEl = document.getElementById('career-card-peak-name');
    
    if (currentIconEl) {
        currentIconEl.src = lastCareerData.current_rank_icon_url || '/static/assets/valorant/ranks/unranked-large.png';
    }
    if (currentNameEl) {
        currentNameEl.textContent = lastCareerData.current_rank || 'Unranked';
    }
    if (peakIconEl) {
        peakIconEl.src = lastCareerData.peak_rank_icon_url || '/static/assets/valorant/ranks/unranked-large.png';
    }
    if (peakNameEl) {
        peakNameEl.textContent = lastCareerData.peak_rank || 'Unranked';
    }

    if (rankedCount) {
        setStatPercentile('career-winrate', 'winrate', rankedWinRate);
        setStatPercentile('career-kd', 'kd', rankedKD);
        setStatPercentile('career-hs', 'hs', rankedHS);
        setStatPercentile('career-acs', 'acs', rankedACS);
        setStatPercentile('career-score', 'score', profileScoreBreakdown.score);
    } else {
        ['career-winrate', 'career-kd', 'career-hs', 'career-acs', 'career-score'].forEach(prefix => {
            const labelEl = document.getElementById(`${prefix}-rank`);
            const progressEl = document.getElementById(`${prefix}-progress`);
            if (labelEl) labelEl.textContent = 'N/A';
            if (progressEl) {
                progressEl.style.height = '0%';
                progressEl.className = '';
            }
        });
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
                <span class="empty-state-text">No matches found for these filters</span>
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

    const actFilterSelect = document.getElementById('career-act-filter');
    if (actFilterSelect) {
        const previousSelection = actFilterSelect.value || 'all';
        const seasonOptions = Array.isArray(career.season_options) ? career.season_options : [];
        const fallbackSeasonMap = new Map();
        matches.forEach(match => {
            if (match.season_id && !fallbackSeasonMap.has(match.season_id)) {
                fallbackSeasonMap.set(match.season_id, {
                    id: match.season_id,
                    label: match.season_label || `ACT ${String(match.season_id).slice(0, 8).toUpperCase()}`,
                    count: 1
                });
            } else if (match.season_id) {
                const option = fallbackSeasonMap.get(match.season_id);
                option.count = Number(option.count || 0) + 1;
            }
        });
        const actOptions = seasonOptions.length ? seasonOptions : Array.from(fallbackSeasonMap.values());
        const newActValues = ['all', ...actOptions.map(option => option.id)];
        const currentActValues = Array.from(actFilterSelect.options).map(option => option.value);

        if (JSON.stringify(currentActValues) !== JSON.stringify(newActValues)) {
            actFilterSelect.innerHTML = '';

            const allOpt = document.createElement('option');
            allOpt.value = 'all';
            allOpt.textContent = 'ALL ACTS';
            actFilterSelect.appendChild(allOpt);

            actOptions.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.id;
                const count = Number(option.count || 0);
                opt.textContent = count ? `${option.label} (${count})` : option.label;
                actFilterSelect.appendChild(opt);
            });
        }

        if (newActValues.includes(previousSelection)) {
            actFilterSelect.value = previousSelection;
        } else {
            actFilterSelect.value = 'all';
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
    const matchScore = match.tracker_score;
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
        <div class="career-match-card ${resultClass}" data-match-id="${escapeHtml(match.match_id)}">
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
                    ${matchScore !== undefined && matchScore !== null ? `<span class="stat-box tracker-score-box"><span class="stat-label">TRS</span><span class="stat-value tracker-score-slot">${renderTrackerScore(matchScore, 'compact')}</span></span>` : ''}
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
                    <span class="stat-value tracker-score-slot">${renderTrackerScore(player.score || 0, 'compact')}</span>
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
                <div class="score-player-inner">
                    <div class="score-player-avatar">${player.agent_icon_url ? renderImage(player.agent_icon_url, player.agent || 'Agent') : ''}</div>
                    <div>
                        <div class="score-player-name">${escapeHtml(player.name)}</div>
                        <div class="score-player-sub">${escapeHtml(player.agent)} / ${escapeHtml(player.rank)}</div>
                    </div>
                </div>
            </td>
            <td>${player.rank_icon_url ? renderImage(player.rank_icon_url, player.rank || 'Rank', 'rank-icon') : ''}</td>
            <td class="score-trs-cell">${renderTrackerScore(player.score || 0, 'table')}</td>
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
                    <span class="stat-value tracker-score-slot">${renderTrackerScore(scoreVal, 'compact')}</span>
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
 * Sends a JSON request to the backend and returns the JSON payload.
 *
 * @param {string} url API endpoint.
 * @param {Object} options Fetch options.
 * @return {Promise<Object>} JSON payload.
 */
async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.message || `Request failed with ${response.status}`);
    }
    return data;
}

/**
 * Updates a status message element with an optional state class.
 *
 * @param {string} elementId Element id.
 * @param {string} message Message to display.
 * @param {string} state success, warning, error, or empty.
 */
function setConfigMessage(elementId, message, state = '') {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.className = 'config-status-message';
    if (state) {
        element.classList.add(state);
    }
    element.textContent = message || '';
}

/**
 * Shows or hides a modal-style overlay.
 *
 * @param {string} elementId Overlay id.
 * @param {boolean} visible Whether the overlay should be visible.
 */
function setOverlayVisible(elementId, visible) {
    const overlay = document.getElementById(elementId);
    if (!overlay) return;
    overlay.classList.toggle('hidden', !visible);
}

/**
 * Reads local settings and config status from the backend.
 */
async function refreshConfigState() {
    const [settings, status] = await Promise.all([
        fetchJson('/api/settings'),
        fetchJson('/api/config/status')
    ]);
    appSettings = settings;
    configStatus = status;
    renderSettingsState();
    return { settings, status };
}

/**
 * Initializes onboarding visibility and settings state.
 */
async function initConfigUi() {
    try {
        const { settings, status } = await refreshConfigState();
        const hasKey = Boolean(status?.henrik_api?.has_key);
        const firstLaunchDone = Boolean(settings?.app?.first_launch_completed);
        setOverlayVisible('onboarding-overlay', !hasKey && !firstLaunchDone);
    } catch (error) {
        setConfigMessage('onboarding-status', 'Unable to load local configuration.', 'error');
    }
}

/**
 * Renders settings controls from the latest settings/config payloads.
 */
function renderSettingsState() {
    if (!appSettings || !configStatus) return;
    const apiState = document.getElementById('settings-api-state');
    const hasKey = Boolean(configStatus?.henrik_api?.has_key);
    if (apiState) {
        apiState.textContent = hasKey ? 'Configured' : 'Missing';
        apiState.classList.toggle('connected', hasKey);
        apiState.classList.toggle('missing', !hasKey);
    }

    setText('settings-version', `v${appSettings?.app?.version || '0.1.0'}`);
    const debugToggle = document.getElementById('settings-debug');
    const launchWindowsToggle = document.getElementById('settings-launch-windows');
    const launchValorantToggle = document.getElementById('settings-launch-valorant');
    if (debugToggle) debugToggle.checked = Boolean(appSettings?.app?.debug);
    if (launchWindowsToggle) launchWindowsToggle.checked = Boolean(appSettings?.startup?.launch_on_windows_start);
    if (launchValorantToggle) launchValorantToggle.checked = Boolean(appSettings?.startup?.launch_when_valorant_starts);
}

/**
 * Verifies and optionally saves a HenrikDev API key.
 *
 * @param {string} inputId Input element id.
 * @param {string} statusId Status element id.
 * @param {boolean} save Whether the key should be saved after verification.
 */
async function handleHenrikKey(inputId, statusId, save) {
    const input = document.getElementById(inputId);
    const apiKey = input?.value?.trim() || '';
    if (!apiKey) {
        setConfigMessage(statusId, 'Paste a HenrikDev API key first.', 'warning');
        return;
    }
    const endpoint = save ? '/api/config/henrik-key' : '/api/config/henrik-key/verify';
    setConfigMessage(statusId, save ? 'Verifying and saving...' : 'Verifying key...');
    try {
        const result = await fetchJson(endpoint, {
            method: 'POST',
            body: JSON.stringify({ api_key: apiKey })
        });
        if (!result.valid) {
            setConfigMessage(statusId, result.message || 'HenrikDev key was rejected.', 'error');
            return;
        }
        if (save) {
            if (input) input.value = '';
            await fetchJson('/api/settings/first-launch-completed', { method: 'POST' });
            await refreshConfigState();
            setOverlayVisible('onboarding-overlay', false);
            setConfigMessage(statusId, 'HenrikDev key saved locally.', 'success');
        } else {
            setConfigMessage(statusId, result.message || 'HenrikDev key is valid.', 'success');
        }
    } catch (error) {
        setConfigMessage(statusId, error.message || 'Unable to verify HenrikDev key.', 'error');
    }
}

/**
 * Saves a small non-sensitive settings patch.
 *
 * @param {Object} patch Settings patch.
 * @param {string} statusId Optional status element id.
 */
async function updateLocalSettings(patch, statusId = '') {
    try {
        appSettings = await fetchJson('/api/settings', {
            method: 'PATCH',
            body: JSON.stringify(patch)
        });
        renderSettingsState();
        if (statusId) {
            if (appSettings?.startup_status?.error) {
                setConfigMessage(statusId, appSettings.startup_status.error, 'error');
            } else {
                setConfigMessage(statusId, 'Settings saved.', 'success');
            }
        }
    } catch (error) {
        if (statusId) {
            setConfigMessage(statusId, error.message || 'Unable to save settings.', 'error');
        }
    }
}

/**
 * Wires onboarding and settings controls.
 */
function bindConfigUi() {
    const settingsOpenButton = document.getElementById('settings-open-button');
    const settingsCloseButton = document.getElementById('settings-close-button');
    const settingsModal = document.getElementById('settings-modal');
    if (settingsOpenButton) {
        settingsOpenButton.addEventListener('click', async () => {
            await refreshConfigState();
            setOverlayVisible('settings-modal', true);
        });
    }
    if (settingsCloseButton) {
        settingsCloseButton.addEventListener('click', () => setOverlayVisible('settings-modal', false));
    }
    if (settingsModal) {
        settingsModal.addEventListener('click', (event) => {
            if (event.target === settingsModal) {
                setOverlayVisible('settings-modal', false);
            }
        });
    }

    const onboardingSaveButton = document.getElementById('onboarding-save-button');
    if (onboardingSaveButton) {
        onboardingSaveButton.addEventListener('click', () => handleHenrikKey('onboarding-api-key', 'onboarding-status', true));
    }
    const onboardingSkipButton = document.getElementById('onboarding-skip-button');
    if (onboardingSkipButton) {
        onboardingSkipButton.addEventListener('click', async () => {
            await fetchJson('/api/settings/first-launch-completed', { method: 'POST' });
            await refreshConfigState();
            setConfigMessage('onboarding-status', 'Continuing without HenrikDev. Live scouting stats will be limited.', 'warning');
            setOverlayVisible('onboarding-overlay', false);
        });
    }

    const settingsSaveKeyButton = document.getElementById('settings-save-key-button');
    if (settingsSaveKeyButton) {
        settingsSaveKeyButton.addEventListener('click', () => handleHenrikKey('settings-api-key', 'settings-key-status', true));
    }
    const settingsVerifyKeyButton = document.getElementById('settings-verify-key-button');
    if (settingsVerifyKeyButton) {
        settingsVerifyKeyButton.addEventListener('click', () => handleHenrikKey('settings-api-key', 'settings-key-status', false));
    }
    const settingsDeleteKeyButton = document.getElementById('settings-delete-key-button');
    if (settingsDeleteKeyButton) {
        settingsDeleteKeyButton.addEventListener('click', async () => {
            const confirmed = window.confirm('Delete the locally saved HenrikDev API key?');
            if (!confirmed) return;
            try {
                await fetchJson('/api/config/henrik-key', { method: 'DELETE' });
                await refreshConfigState();
                setConfigMessage('settings-key-status', 'HenrikDev key deleted.', 'success');
            } catch (error) {
                setConfigMessage('settings-key-status', error.message || 'Unable to delete key.', 'error');
            }
        });
    }

    const debugToggle = document.getElementById('settings-debug');
    if (debugToggle) {
        debugToggle.addEventListener('change', () => updateLocalSettings({ app: { debug: debugToggle.checked } }, 'settings-runtime-status'));
    }
    const launchWindowsToggle = document.getElementById('settings-launch-windows');
    if (launchWindowsToggle) {
        launchWindowsToggle.addEventListener('change', () => updateLocalSettings({ startup: { launch_on_windows_start: launchWindowsToggle.checked } }, 'settings-runtime-status'));
    }
    const launchValorantToggle = document.getElementById('settings-launch-valorant');
    if (launchValorantToggle) {
        launchValorantToggle.addEventListener('change', () => updateLocalSettings({ startup: { launch_when_valorant_starts: launchValorantToggle.checked } }, 'settings-runtime-status'));
    }

    const actionMap = [
        ['settings-open-data-button', '/api/settings/open-data-folder', 'Opening data folder...'],
        ['settings-open-logs-button', '/api/settings/open-logs-folder', 'Opening logs folder...'],
        ['settings-reload-cache-button', '/api/settings/reload-cache', 'Reloading cache...']
    ];
    actionMap.forEach(([buttonId, endpoint, pendingMessage]) => {
        const button = document.getElementById(buttonId);
        if (!button) return;
        button.addEventListener('click', async () => {
            setConfigMessage('settings-runtime-status', pendingMessage);
            try {
                await fetchJson(endpoint, { method: 'POST' });
                await refreshConfigState();
                setConfigMessage('settings-runtime-status', 'Done.', 'success');
            } catch (error) {
                setConfigMessage('settings-runtime-status', error.message || 'Action failed.', 'error');
            }
        });
    });
}

/**
 * Initializes the dashboard application.
 */
function init() {
    bindConfigUi();
    const importButton = document.getElementById('career-import-button');
    if (importButton) {
        importButton.addEventListener('click', importCompetitiveHistory);
    }
    const filterSelect = document.getElementById('career-mode-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', applyCareerFilter);
    }
    const actFilterSelect = document.getElementById('career-act-filter');
    if (actFilterSelect) {
        actFilterSelect.addEventListener('change', applyCareerFilter);
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
    initConfigUi();
    checkAppUpdates();
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

let updateDownloadUrl = null;

/**
 * Checks for updates on GitHub via the local backend.
 */
async function checkAppUpdates() {
    try {
        const response = await fetch('/api/updater/check');
        const data = await response.json();
        
        if (data.update_available && data.download_url) {
            updateDownloadUrl = data.download_url;
            
            // Show the header update notification widget
            const updaterWidget = document.getElementById('updater-header-widget');
            if (updaterWidget) {
                updaterWidget.classList.remove('hidden');
                
                // Add event listener to the update button in the header
                const triggerBtn = document.getElementById('updater-trigger-button');
                if (triggerBtn) {
                    triggerBtn.addEventListener('click', () => {
                        openUpdateModal(data);
                    });
                }
            }
        }
    } catch (e) {
        console.error("Failed to check for updates:", e);
    }
}

/**
 * Opens the Update Modal with release notes and version info.
 */
function openUpdateModal(releaseInfo) {
    const modal = document.getElementById('update-modal');
    if (!modal) return;
    
    // Set version info
    const versionLabel = document.getElementById('update-modal-version');
    if (versionLabel) {
        versionLabel.textContent = `v${releaseInfo.latest_version}`;
    }
    
    // Set release notes
    const notesContainer = document.getElementById('update-modal-notes');
    if (notesContainer) {
        notesContainer.textContent = releaseInfo.release_notes || "No release notes available.";
    }
    
    // Set up button listeners
    const startBtn = document.getElementById('update-start-button');
    const cancelBtn = document.getElementById('update-cancel-button');
    const closeBtn = document.getElementById('update-close-button');
    
    if (startBtn) {
        // Clear previous listeners by replacing the button
        const newStartBtn = startBtn.cloneNode(true);
        startBtn.parentNode.replaceChild(newStartBtn, startBtn);
        newStartBtn.addEventListener('click', () => startDownloadAndInstall(releaseInfo.download_url));
    }
    
    const closeModal = () => {
        modal.classList.add('hidden');
    };
    
    if (cancelBtn) {
        // Clear previous listeners by replacing the button
        const newCancelBtn = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        newCancelBtn.addEventListener('click', closeModal);
    }
    if (closeBtn) {
        // Clear previous listeners by replacing the button
        const newCloseBtn = closeBtn.cloneNode(true);
        closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
        newCloseBtn.addEventListener('click', closeModal);
    }
    
    modal.classList.remove('hidden');
}

/**
 * Triggers the installer download and polls progress, then launches installer.
 */
async function startDownloadAndInstall(downloadUrl) {
    const startBtn = document.getElementById('update-start-button');
    const cancelBtn = document.getElementById('update-cancel-button');
    const closeBtn = document.getElementById('update-close-button');
    const progressContainer = document.getElementById('update-download-progress-container');
    const progressPercent = document.getElementById('update-progress-percent');
    const progressFill = document.getElementById('update-progress-fill');
    
    if (startBtn) startBtn.disabled = true;
    if (cancelBtn) cancelBtn.disabled = true;
    if (closeBtn) closeBtn.style.display = 'none';
    
    if (progressContainer) progressContainer.classList.remove('hidden');
    
    try {
        // Trigger download
        const response = await fetch('/api/updater/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ download_url: downloadUrl })
        });
        const data = await response.json();
        
        if (data.error) {
            alert(`Download failed to start: ${data.error}`);
            resetUpdateModalState();
            return;
        }
        
        // Poll progress
        const pollInterval = setInterval(async () => {
            try {
                const pollResp = await fetch('/api/updater/progress');
                const status = await pollResp.json();
                
                if (status.progress < 0) {
                    clearInterval(pollInterval);
                    alert("An error occurred during download.");
                    resetUpdateModalState();
                    return;
                }
                
                const percent = status.progress || 0;
                if (progressPercent) progressPercent.textContent = `${percent}%`;
                if (progressFill) progressFill.style.width = `${percent}%`;
                
                if (status.completed) {
                    clearInterval(pollInterval);
                    if (startBtn) startBtn.textContent = "Installing...";
                    
                    // Trigger backend installer and exit
                    await fetch('/api/updater/install', { method: 'POST' });
                }
            } catch (err) {
                console.error("Error polling update progress:", err);
            }
        }, 1000);
        
    } catch (e) {
        alert(`Failed to execute update: ${e.message}`);
        resetUpdateModalState();
    }
}

/**
 * Resets the update modal buttons if download fails.
 */
function resetUpdateModalState() {
    const startBtn = document.getElementById('update-start-button');
    const cancelBtn = document.getElementById('update-cancel-button');
    const closeBtn = document.getElementById('update-close-button');
    const progressContainer = document.getElementById('update-download-progress-container');
    
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = "Download and Install";
    }
    if (cancelBtn) cancelBtn.disabled = false;
    if (closeBtn) closeBtn.style.display = 'block';
    if (progressContainer) progressContainer.classList.add('hidden');
}

// Toggle fullscreen on F11 when running in pywebview desktop shell
document.addEventListener('keydown', (event) => {
    if (event.key === 'F11') {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.toggle_fullscreen === 'function') {
            event.preventDefault();
            window.pywebview.api.toggle_fullscreen();
        }
    }
});
