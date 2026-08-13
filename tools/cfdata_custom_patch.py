#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "combined_refactor" / "index.html"
text = INDEX.read_text(encoding="utf-8")
changed = []

def must_replace(old, new, name, count=1):
    global text
    if old not in text:
        raise SystemExit(f"[patch] 找不到目标片段: {name}")
    text = text.replace(old, new, count)
    changed.append(name)

def must_sub(pattern, repl, name, count=1):
    global text
    # Use a callable replacement so backslashes inside JavaScript regexes
    # (for example \d and \.) are not re-interpreted by Python re.sub.
    text2, n = re.subn(pattern, lambda _m: repl, text, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f"[patch] {name} 期望替换 {count} 次，实际 {n} 次")
    text = text2
    changed.append(name)

if ".ip-prefix-emphasis" not in text:
    must_replace(
        "        .ip-cell {\n            display: inline-flex;\n            align-items: center;\n            gap: 6px;\n        }\n",
        "        .ip-prefix-emphasis {\n            color: #ef4444;\n            font-weight: 800;\n        }\n\n        .ip-host-emphasis {\n            color: inherit;\n            font-weight: 600;\n        }\n\n        .ip-cell {\n            display: inline-flex;\n            align-items: center;\n            gap: 6px;\n            white-space: nowrap;\n        }\n",
        "IP号段红色强调样式"
    )

if "function renderIPPrefixEmphasis(" not in text:
    must_sub(
        r"        function renderIPCell\(ip, originalInput\) \{.*?\n        \}\n\n        function renderNSBRowFromCSV",
        """        function renderIPPrefixEmphasis(ip) {
            const raw = String(ip ?? '').trim();
            const safe = escapeHTML(raw);
            if (!raw) return safe;

            if (raw.includes(':')) {
                const m = raw.match(/^((?:[0-9A-Fa-f]{1,4}:){2}[0-9A-Fa-f]{1,4})(.*)$/);
                if (m) {
                    return `<span class="ip-prefix-emphasis">${escapeHTML(m[1])}</span><span class="ip-host-emphasis">${escapeHTML(m[2])}</span>`;
                }
                return safe;
            }

            const m = raw.match(/^(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})(\\.\\d{1,3})$/);
            if (m) {
                return `<span class="ip-prefix-emphasis">${escapeHTML(m[1])}</span><span class="ip-host-emphasis">${escapeHTML(m[2])}</span>`;
            }
            return safe;
        }

        function renderIPCell(ip, originalInput) {
            const rawIP = String(ip ?? '');
            const displayIP = renderIPPrefixEmphasis(rawIP);
            const jsIP = escapeJSString(rawIP);
            const hrefIP = encodeURIComponent(rawIP);
            let domainIcon = '';
            if (originalInput && originalInput !== rawIP) {
                const isDomain = /[a-zA-Z]/.test(originalInput);
                if (isDomain && !String(originalInput).includes('/')) {
                    const safeSource = escapeHTML(originalInput);
                    domainIcon = `<span class="ip-detail-link" title="来源域名: ${safeSource}" onclick="event.stopPropagation()" style="cursor:default;">ⓗ</span>`;
                }
            }
            return `<span class="ip-cell"><span class="copy-ip" title="${escapeHTML(rawIP)}" onclick="copyToClipboard('${jsIP}', event)">${displayIP}</span>${domainIcon}<a class="ip-detail-link" href="https://ippure.com/?ip=${hrefIP}" target="_blank" rel="noopener noreferrer" title="前往 ippure.com 查看 IP 详情" onclick="event.stopPropagation()">ⓘ</a></span>`;
        }

        function renderNSBRowFromCSV""",
        "完整IP显示+号段红色强调"
    )

if "ui: { mode: currentMode }" not in text:
    must_replace(
        "            return {\n                official: {\n",
        "            return {\n                ui: { mode: currentMode },\n                official: {\n",
        "配置保存当前模式"
    )

if "const ui = config.ui || {};" not in text:
    must_replace(
        "        function applyConfigValues(config) {\n            const o = config.official || {};\n            const n = config.nsb || {};\n",
        "        function applyConfigValues(config) {\n            const ui = config.ui || {};\n            const o = config.official || {};\n            const n = config.nsb || {};\n",
        "配置读取当前模式"
    )
    must_replace(
        "            updateNSBSpeedControls();\n            updateNSBCompactToggle();\n        }\n\n        function saveConfigToLS() {\n",
        "            updateNSBSpeedControls();\n            updateNSBCompactToggle();\n            if (ui.mode === 'official' || ui.mode === 'nsb') switchMode(ui.mode);\n        }\n\n        function saveConfigToLS() {\n",
        "配置恢复当前模式"
    )

if "LAST_COMPLETED_CONFIG_KEY" not in text:
    must_replace(
        "        const githubAccountStorageKey = 'cfdata-github-accounts';\n",
        "        const githubAccountStorageKey = 'cfdata-github-accounts';\n        const LAST_COMPLETED_CONFIG_KEY = 'cfdata-last-completed-config';\n        const LAST_COMPLETED_CONFIG_META_KEY = 'cfdata-last-completed-config-meta';\n",
        "最后完成配置键"
    )

if "function saveCompletedConfigSnapshot(" not in text:
    must_replace(
        "        function loadConfigFromLS() {\n",
        """        function saveCompletedConfigSnapshot(reason = '测速完成') {
            const config = readFormValues();
            try {
                const raw = JSON.stringify(config);
                localStorage.setItem(LAST_COMPLETED_CONFIG_KEY, raw);
                localStorage.setItem('cfdata-config', raw);
                localStorage.setItem(LAST_COMPLETED_CONFIG_META_KEY, JSON.stringify({
                    savedAt: new Date().toISOString(),
                    reason: String(reason || '测速完成'),
                }));
                log(`已自动保存本次完成配置：${reason}`);
                return true;
            } catch (e) {
                log('自动保存完成配置失败: ' + (e.message || String(e)));
                return false;
            }
        }

        function loadCompletedConfigSnapshot() {
            try {
                const raw = localStorage.getItem(LAST_COMPLETED_CONFIG_KEY);
                if (!raw) return false;
                applyConfigValues(JSON.parse(raw));
                log('已恢复上一次测速完成时的配置');
                return true;
            } catch (e) {
                console.error('[cfdata] loadCompletedConfigSnapshot failed:', e);
                return false;
            }
        }

        function loadConfigFromLS() {
""",
        "自动保存/恢复完成配置"
    )

if "localStorage.removeItem(LAST_COMPLETED_CONFIG_KEY);" not in text:
    must_replace(
        "                localStorage.removeItem('cfdata-config');\n                localStorage.removeItem('cfdata-autoload');\n",
        "                localStorage.removeItem('cfdata-config');\n                localStorage.removeItem('cfdata-autoload');\n                localStorage.removeItem(LAST_COMPLETED_CONFIG_KEY);\n                localStorage.removeItem(LAST_COMPLETED_CONFIG_META_KEY);\n",
        "删除完成配置快照"
    )

must_sub(
    r"        function autoLoadConfig\(\) \{.*?\n        \}\n\n        function loadConfigFromServer",
    """        function autoLoadConfig() {
            if (loadCompletedConfigSnapshot()) return;

            let pref;
            try {
                pref = localStorage.getItem('cfdata-autoload');
            } catch (e) {
                return;
            }
            if (!pref || pref === 'off') return;
            try {
                if (pref === 'localStorage') {
                    const raw = localStorage.getItem('cfdata-config');
                    if (raw) applyConfigValues(JSON.parse(raw));
                } else if (pref === 'configFile') {
                    wsSend({ type: 'get_config' });
                }
            } catch (e) {
                console.error('[cfdata] autoLoadConfig failed:', e);
            }
        }

        function loadConfigFromServer""",
    "启动优先恢复最后完成配置"
)

if "saveCompletedConfigSnapshot('官方详细测试完成');" not in text:
    must_replace(
        "                        onTestComplete();\n                        officialTestCompletePending = true;\n",
        "                        onTestComplete();\n                        saveCompletedConfigSnapshot('官方详细测试完成');\n                        officialTestCompletePending = true;\n",
        "官方详细测试完成自动保存"
    )

if "saveCompletedConfigSnapshot('官方测速完成');" not in text:
    must_replace(
        "                    autoUploadOfficialResults();\n                    break;\n                case 'github_upload_result':\n",
        "                    saveCompletedConfigSnapshot('官方测速完成');\n                    autoUploadOfficialResults();\n                    break;\n                case 'github_upload_result':\n",
        "官方测速完成自动保存"
    )

if "saveCompletedConfigSnapshot('非标测速完成');" not in text:
    must_replace(
        "                    updateProgress(msg.data?.qualified || 0, msg.data?.limit || 1, '测速完成');\n                    autoUploadNSBResults();\n                    break;\n\n                case 'nsb_csv_ready':\n",
        "                    updateProgress(msg.data?.qualified || 0, msg.data?.limit || 1, '测速完成');\n                    saveCompletedConfigSnapshot('非标测速完成');\n                    autoUploadNSBResults();\n                    break;\n\n                case 'nsb_csv_ready':\n",
        "非标测速完成自动保存"
    )

if "saveCompletedConfigSnapshot('非标任务完成');" not in text:
    must_replace(
        "                    } else {\n                        log(`非标优选完成，已生成: ${msg.data.file}`);\n                    }\n                    autoUploadNSBResults();\n                    break;\n",
        "                    } else {\n                        log(`非标优选完成，已生成: ${msg.data.file}`);\n                        if (!wasStoppingNSB) saveCompletedConfigSnapshot('非标任务完成');\n                    }\n                    autoUploadNSBResults();\n                    break;\n",
        "非标完整任务完成自动保存"
    )

INDEX.write_text(text, encoding="utf-8")
print("[patch] 已应用:")
for item in changed:
    print(" -", item)
print("[patch] index.html 更新完成")
