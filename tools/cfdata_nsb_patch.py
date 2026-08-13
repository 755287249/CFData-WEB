#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "combined_refactor" / "index.html"
TASKS = ROOT / "combined_refactor" / "tasks_nsb.go"
UTILS = ROOT / "combined_refactor" / "utils.go"
PROTOCOL = ROOT / "combined_refactor" / "protocol.go"
SERVER = ROOT / "combined_refactor" / "server.go"

html = INDEX.read_text(encoding="utf-8")
go = TASKS.read_text(encoding="utf-8")
utils = UTILS.read_text(encoding="utf-8")
protocol = PROTOCOL.read_text(encoding="utf-8")
server = SERVER.read_text(encoding="utf-8")
changed = []


def h_replace(old, new, name, count=1):
    global html
    if old not in html:
        raise SystemExit(f"[nsb-patch] HTML 找不到目标片段: {name}")
    html = html.replace(old, new, count)
    changed.append(name)


def h_sub(pattern, repl, name, count=1):
    global html
    html2, n = re.subn(pattern, lambda _m: repl, html, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f"[nsb-patch] HTML {name} 期望替换 {count} 次，实际 {n} 次")
    html = html2
    changed.append(name)


def g_replace(old, new, name, count=1):
    global go
    if old not in go:
        raise SystemExit(f"[nsb-patch] Go 找不到目标片段: {name}")
    go = go.replace(old, new, count)
    changed.append(name)


def u_replace(old, new, name, count=1):
    global utils
    if old not in utils:
        raise SystemExit(f"[nsb-patch] utils.go 找不到目标片段: {name}")
    utils = utils.replace(old, new, count)
    changed.append(name)


def p_replace(old, new, name, count=1):
    global protocol
    if old not in protocol:
        raise SystemExit(f"[nsb-patch] protocol.go 找不到目标片段: {name}")
    protocol = protocol.replace(old, new, count)
    changed.append(name)


def s_replace(old, new, name, count=1):
    global server
    if old not in server:
        raise SystemExit(f"[nsb-patch] server.go 找不到目标片段: {name}")
    server = server.replace(old, new, count)
    changed.append(name)


# ---------------------------------------------------------------------------
# 1) 非标模式：IP 文件 / URL / 手动输入 三选一
# ---------------------------------------------------------------------------
if "支持上传 txt/csv 文件、填写网络 URL 或手动输入" not in html:
    html = html.replace(
        "支持上传 txt/csv 文件或填写网络\n                        URL（二选一）",
        "支持上传 txt/csv 文件、填写网络 URL 或手动输入（三选一）",
        1,
    )

if 'id="nsbManualInput"' not in html:
    h_replace(
        '''                <div class="option-item full-width">\n                    <span class="label" title="从网络地址获取 IP 列表">🌐 网络 URL</span>\n                    <input id="nsbSourceUrl" type="url" placeholder="https://example.com/ip-list.txt"\n                        oninput="syncNSBInputMode('url')">\n                </div>\n''',
        '''                <div class="option-item full-width">\n                    <span class="label" title="从网络地址获取 IP 列表">🌐 网络 URL</span>\n                    <input id="nsbSourceUrl" type="url" placeholder="https://example.com/ip-list.txt"\n                        oninput="syncNSBInputMode('url')">\n                </div>\n                <div class="option-item full-width">\n                    <span class="label" title="每行一个；兼容 CIDR、完整 IPv4/IPv6、[IPv6]、[IPv6]:端口、IP 空格 端口">✍️ 手动输入</span>\n                    <textarea id="nsbManualInput"\n                        placeholder="每行一个目标，例如：&#10;2400:cb00:2048::/48&#10;2400:cb00:2049::/48&#10;[2606:4700:57:b2a2:dd58:8f45:ba2:78ea]:443&#10;1.1.1.1 443"\n                        oninput="syncNSBInputMode('manual')"\n                        style="width:100%;min-height:120px;resize:vertical;"></textarea>\n                </div>\n''',
        "新增手动输入入口",
    )

if "const nsbManualInput = document.getElementById('nsbManualInput');" not in html:
    h_replace(
        '''        const fileInput = document.getElementById('nsbFileInput');\n        const nsbSourceUrlInput = document.getElementById('nsbSourceUrl');\n''',
        '''        const fileInput = document.getElementById('nsbFileInput');\n        const nsbSourceUrlInput = document.getElementById('nsbSourceUrl');\n        const nsbManualInput = document.getElementById('nsbManualInput');\n''',
        "手动输入 DOM 引用",
    )

if "preferred === 'manual'" not in html:
    h_sub(
        r'''        function syncNSBInputMode\(preferred\) \{.*?\n        \}\n\n        function applyTheme''',
        '''        function syncNSBInputMode(preferred) {\n            const hasFile = !!(fileInput && fileInput.files && fileInput.files.length);\n            const hasURL = !!(nsbSourceUrlInput && nsbSourceUrlInput.value.trim());\n            const hasManual = !!(nsbManualInput && nsbManualInput.value.trim());\n\n            if (preferred === 'file' && hasFile) {\n                if (nsbSourceUrlInput) nsbSourceUrlInput.value = '';\n                if (nsbManualInput) nsbManualInput.value = '';\n            } else if (preferred === 'url' && hasURL) {\n                if (fileInput) fileInput.value = '';\n                uploadedFileName = '';\n                uploadedFileContent = '';\n                if (nsbManualInput) nsbManualInput.value = '';\n            } else if (preferred === 'manual' && hasManual) {\n                if (fileInput) fileInput.value = '';\n                uploadedFileName = '';\n                uploadedFileContent = '';\n                if (nsbSourceUrlInput) nsbSourceUrlInput.value = '';\n            }\n        }\n\n        function applyTheme''',
        "三选一输入联动",
    )

if "manualInput: val('nsbManualInput')" not in html:
    h_replace(
        '''                    sourceUrl: val('nsbSourceUrl'),\n''',
        '''                    sourceUrl: val('nsbSourceUrl'),\n                    manualInput: val('nsbManualInput'),\n''',
        "保存手动输入配置",
    )

if "setValue('nsbManualInput', n.manualInput);" not in html:
    h_replace(
        '''            setValue('nsbSourceUrl', n.sourceUrl);\n''',
        '''            setValue('nsbSourceUrl', n.sourceUrl);\n            setValue('nsbManualInput', n.manualInput);\n''',
        "恢复手动输入配置",
    )

if "function normalizeNSBManualInput(content)" not in html:
    h_replace(
        '''        function startNSBTask() {\n''',
        '''        function normalizeNSBManualInput(content) {\n            const raw = String(content || '').replace(/\\r\\n/g, '\\n').trim();\n            if (!raw) return '';\n            const lines = [];\n            const isPort = (token) => /^\\d{1,5}$/.test(token) && Number(token) >= 1 && Number(token) <= 65535;\n            const looksTarget = (token) => {\n                const t = String(token || '').trim();\n                if (!t) return false;\n                if (t.includes('/') || t.includes(':')) return true;\n                return /^(?:\\d{1,3}\\.){3}\\d{1,3}$/.test(t) || /^[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$/.test(t);\n            };\n            for (const sourceLine of raw.split(/\\n+/)) {\n                const line = sourceLine.trim();\n                if (!line) continue;\n                const tokens = line.replace(/[，,；;]/g, ' ').split(/\\s+/).filter(Boolean);\n                if (tokens.length <= 1) {\n                    lines.push(line);\n                    continue;\n                }\n                let parsed = [];\n                let ok = true;\n                for (let i = 0; i < tokens.length;) {\n                    const target = tokens[i];\n                    if (!looksTarget(target)) { ok = false; break; }\n                    if (i + 1 < tokens.length && isPort(tokens[i + 1])) {\n                        parsed.push(`${target} ${tokens[i + 1]}`);\n                        i += 2;\n                    } else {\n                        parsed.push(target);\n                        i += 1;\n                    }\n                }\n                lines.push(...(ok ? parsed : [line]));\n            }\n            return lines.join('\\n');\n        }\n\n        function startNSBTask() {\n''',
        "手动输入兼容空格/逗号多目标",
    )

if "const manualContent = normalizeNSBManualInput(nsbManualInput ? nsbManualInput.value : '');" not in html:
    h_replace(
        '''            const sourceURL = nsbSourceUrlInput ? nsbSourceUrlInput.value.trim() : '';\n            const hasFile = !!uploadedFileContent.trim();\n            const hasURL = !!sourceURL;\n            if (hasFile === hasURL) {\n                showNoticeCard('请选择本地文件或填写网络 URL（二选一）');\n                return;\n            }\n\n            const maxThreads = parseInt(document.getElementById('nsbThreads').value) || 100;\n''',
        '''            const sourceURL = nsbSourceUrlInput ? nsbSourceUrlInput.value.trim() : '';\n            const manualContent = normalizeNSBManualInput(nsbManualInput ? nsbManualInput.value : '');\n            const hasFile = !!uploadedFileContent.trim();\n            const hasURL = !!sourceURL;\n            const hasManual = !!manualContent;\n            const inputCount = (hasFile ? 1 : 0) + (hasURL ? 1 : 0) + (hasManual ? 1 : 0);\n            if (inputCount !== 1) {\n                showNoticeCard('请选择一种输入方式：IP 文件 / 网络 URL / 手动输入（三选一）');\n                return;\n            }\n\n            const maxThreads = parseInt(document.getElementById('nsbThreads').value) || 100;\n''',
        "非标开始任务支持手动输入",
    )

if "fileName: hasManual ? 'manual-input.txt'" not in html:
    h_replace(
        '''                    fileName: uploadedFileName,\n                    fileContent: hasFile ? uploadedFileContent : '',\n                    sourceURL: hasURL ? sourceURL : '',\n''',
        '''                    fileName: hasManual ? 'manual-input.txt' : uploadedFileName,\n                    fileContent: hasFile ? uploadedFileContent : (hasManual ? manualContent : ''),\n                    sourceURL: hasURL ? sourceURL : '',\n''',
        "手动输入发送给后端",
    )


# ---------------------------------------------------------------------------
# 2) 复制 / 导出 / GitHub 上传：IPv6 可选择 [IPv6]:PORT
# ---------------------------------------------------------------------------
if 'id="resultIPOutputFormat"' not in html:
    h_replace(
        '''                    <div class="modal-field" id="resultQualifiedFilterField">\n                        <label>导出合格结果</label>\n''',
        '''                    <div class="modal-field">\n                        <label>IP 输出格式</label>\n                        <select id="resultIPOutputFormat" onchange="updateResultPreview()">\n                            <option value="plain" selected>原始格式</option>\n                            <option value="bracket">IPv6 加 [ ]（如 [IPv6]:443）</option>\n                        </select>\n                    </div>\n                    <div class="modal-field" id="resultQualifiedFilterField">\n                        <label>导出合格结果</label>\n''',
        "结果操作增加方括号格式",
    )

if 'id="copyIPOutputFormat"' not in html:
    h_replace(
        '''                    <div class="modal-field" id="copyQualifiedFilterField">\n                        <label>复制合格结果</label>\n''',
        '''                    <div class="modal-field">\n                        <label>IP 输出格式</label>\n                        <select id="copyIPOutputFormat" onchange="updateCopyPreview()">\n                            <option value="plain" selected>原始格式</option>\n                            <option value="bracket">IPv6 加 [ ]（如 [IPv6]:443）</option>\n                        </select>\n                    </div>\n                    <div class="modal-field" id="copyQualifiedFilterField">\n                        <label>复制合格结果</label>\n''',
        "一键复制增加方括号格式",
    )

if "function getOutputIPFormat(prefix)" not in html:
    h_replace(
        '''        function buildCopyContent() {\n''',
        '''        function getOutputIPFormat(prefix) {\n            return document.getElementById(`${prefix}IPOutputFormat`)?.value || 'plain';\n        }\n\n        function formatOutputIP(ip, mode = 'plain') {\n            const raw = String(ip ?? '').trim();\n            if (mode === 'bracket' && raw.includes(':') && !(raw.startsWith('[') && raw.endsWith(']'))) {\n                return `[${raw}]`;\n            }\n            return raw;\n        }\n\n        function formatOutputRow(row, mode = 'plain') {\n            const next = { ...row };\n            const formattedIP = formatOutputIP(next.ip || '', mode);\n            next.ip = formattedIP;\n            const port = String(next.port ?? '').trim();\n            next.ipport = port ? `${formattedIP}:${port}` : formattedIP;\n            return next;\n        }\n\n        function buildCopyContent() {\n''',
        "输出IP格式化函数",
    )

if "getOutputIPFormat('copy')" not in html:
    h_replace(
        '''            return buildResultContent('txt', rows, fields, getTextSeparator('copy'));\n''',
        '''            return buildResultContent('txt', rows, fields, getTextSeparator('copy'), getOutputIPFormat('copy'));\n''',
        "复制内容应用方括号格式",
    )

if "const first = formatOutputRow(rows[0], getOutputIPFormat('copy'));" not in html:
    h_replace(
        '''        function buildCopyPreview() {\n            const rows = getSelectedCopyRows();\n            if (!rows.length) return '暂无预览';\n            const fields = copyFieldOrder.length ? copyFieldOrder : getDefaultResultFieldOrderFor(copyModalMode, 'txt');\n            const first = rows[0];\n''',
        '''        function buildCopyPreview() {\n            const rows = getSelectedCopyRows();\n            if (!rows.length) return '暂无预览';\n            const fields = copyFieldOrder.length ? copyFieldOrder : getDefaultResultFieldOrderFor(copyModalMode, 'txt');\n            const first = formatOutputRow(rows[0], getOutputIPFormat('copy'));\n''',
        "复制预览应用方括号格式",
    )

if "getOutputIPFormat('result')" not in html:
    h_replace(
        '''            return buildResultContent(format, rows, fields, getTextSeparator('result'));\n''',
        '''            return buildResultContent(format, rows, fields, getTextSeparator('result'), getOutputIPFormat('result'));\n''',
        "结果导出上传应用方括号格式",
    )

if "const first = formatOutputRow(rows[0], getOutputIPFormat('result'));" not in html:
    h_replace(
        '''        function buildResultPreview(format) {\n            const rows = getSelectedResultRows();\n            if (!rows.length) return '暂无预览';\n            const fields = resultFieldOrder.length ? resultFieldOrder : getDefaultResultFieldOrder(format);\n            const first = rows[0];\n''',
        '''        function buildResultPreview(format) {\n            const rows = getSelectedResultRows();\n            if (!rows.length) return '暂无预览';\n            const fields = resultFieldOrder.length ? resultFieldOrder : getDefaultResultFieldOrder(format);\n            const first = formatOutputRow(rows[0], getOutputIPFormat('result'));\n''',
        "结果预览应用方括号格式",
    )

if "const outputRows = rows.map((row) => formatOutputRow(row, ipFormat));" not in html:
    h_replace(
        '''        function buildResultContent(format, rows, fields, textSeparator = '-') {\n            if (!rows.length) throw new Error('暂无可操作结果');\n            if (format === 'txt') {\n                return rows.map((r) => {\n                    const ipport = r.ipport || `${r.ip || ''}:${r.port || ''}`;\n                    const extras = fields.filter((k) => k !== 'ipport').map((k) => r[k]).filter((v) => String(v ?? '').trim() !== '');\n                    return extras.length ? `${ipport}#${extras.join(textSeparator)}` : ipport;\n                }).join('\\n') + '\\n';\n            }\n            const byKey = Object.fromEntries(RESULT_FIELDS.concat(resultCustomFields).map((f) => [f.key, f]));\n            const headers = fields.map((k) => byKey[k]?.label || k);\n            const body = rows.map((r) => fields.map((k) => formatCSVCell(r[k])).join(',')).join('\\n');\n            return headers.join(',') + '\\n' + body + '\\n';\n        }\n''',
        '''        function buildResultContent(format, rows, fields, textSeparator = '-', ipFormat = 'plain') {\n            if (!rows.length) throw new Error('暂无可操作结果');\n            const outputRows = rows.map((row) => formatOutputRow(row, ipFormat));\n            if (format === 'txt') {\n                return outputRows.map((r) => {\n                    const ipport = r.ipport || `${r.ip || ''}:${r.port || ''}`;\n                    const extras = fields.filter((k) => k !== 'ipport').map((k) => r[k]).filter((v) => String(v ?? '').trim() !== '');\n                    return extras.length ? `${ipport}#${extras.join(textSeparator)}` : ipport;\n                }).join('\\n') + '\\n';\n            }\n            const byKey = Object.fromEntries(RESULT_FIELDS.concat(resultCustomFields).map((f) => [f.key, f]));\n            const headers = fields.map((k) => byKey[k]?.label || k);\n            const body = outputRows.map((r) => fields.map((k) => formatCSVCell(r[k])).join(',')).join('\\n');\n            return headers.join(',') + '\\n' + body + '\\n';\n        }\n''',
        "统一输出内容方括号格式",
    )

# 自动上传仍默认原始格式；手动 GitHub 上传会跟随“结果操作”的格式选择。


# ---------------------------------------------------------------------------
# 3) 非标模式：扫描合格延迟直接淘汰，CIDR 名额智能重分配
#    例：8 个 /48 * 每段 4 个 = 32；若 30 个淘汰，只剩 2 个合格号段，
#    则 30 个空缺平均分给存活号段；余数优先给最佳延迟更低的号段。
# ---------------------------------------------------------------------------
if "effectiveDelay := delay" not in go:
    g_replace(
        '''\tmul := latencyMultiplier(scanModeHTTPing, enableTLS)\n\teffectiveDelay := int(float64(delay) * mul)\n''',
        '''\teffectiveDelay := delay\n''',
        "HTTPing直接使用扫描合格延迟",
    )

if "type nsbCIDRGroup struct" not in go:
    helper = r'''type nsbCIDRGroup struct {
	cidr        string
	prefix      netip.Prefix
	port        int
	used        map[string]struct{}
	accepted    int
	bestLatency time.Duration
	order       int
}

type nsbAdaptiveEntry struct {
	ip            string
	port          int
	originalInput string
	groupIndex    int
}

func parseNSBCIDRGroups(content string, fallbackPort int) []nsbCIDRGroup {
	lines := strings.Split(strings.ReplaceAll(content, "\r\n", "\n"), "\n")
	groups := make([]nsbCIDRGroup, 0)
	seen := make(map[string]struct{})
	order := 0
	replacer := strings.NewReplacer(",", " ", "，", " ", ";", " ", "；", " ")

	for _, line := range lines {
		line = strings.TrimSpace(strings.TrimPrefix(line, "\ufeff"))
		if line == "" {
			continue
		}
		if comment := strings.Index(line, "#"); comment >= 0 {
			line = strings.TrimSpace(line[:comment])
		}
		fields := strings.Fields(replacer.Replace(line))
		if len(fields) == 0 {
			continue
		}

		for i := 0; i < len(fields); i++ {
			token := cleanNSBToken(fields[i])
			prefix, err := netip.ParsePrefix(token)
			if err != nil {
				continue
			}
			prefix = prefix.Masked()
			port := fallbackPort
			if i+1 < len(fields) {
				next := cleanNSBToken(fields[i+1])
				if _, err := netip.ParsePrefix(next); err != nil {
					if parsedPort, ok := parsePort(next); ok {
						port = parsedPort
						i++
					}
				}
			}

			var cidrs []string
			if prefix.Addr().Is4() {
				cidrs = expandCIDRTo24s(prefix.String())
			} else {
				cidrs = expandCIDRTo48s(prefix.String())
			}
			for _, cidr := range cidrs {
				leaf, err := netip.ParsePrefix(cidr)
				if err != nil {
					continue
				}
				leaf = leaf.Masked()
				key := leaf.String() + "|" + strconv.Itoa(port)
				if _, exists := seen[key]; exists {
					continue
				}
				seen[key] = struct{}{}
				groups = append(groups, nsbCIDRGroup{
					cidr:   leaf.String(),
					prefix: leaf,
					port:   port,
					used:   make(map[string]struct{}),
					order:  order,
				})
				order++
			}
		}
	}
	return groups
}

func findNSBCIDRGroup(ip string, port int, groups []nsbCIDRGroup) int {
	addr, err := netip.ParseAddr(strings.TrimSpace(ip))
	if err != nil {
		return -1
	}
	for i := range groups {
		if groups[i].port == port && groups[i].prefix.Contains(addr) {
			return i
		}
	}
	return -1
}

func resetNSBCIDRStats(groups []nsbCIDRGroup, results []iptestResult) int {
	for i := range groups {
		groups[i].accepted = 0
		groups[i].bestLatency = 0
	}
	accepted := 0
	for i := range results {
		idx := findNSBCIDRGroup(results[i].ipAddr, results[i].port, groups)
		if idx < 0 {
			continue
		}
		accepted++
		groups[idx].accepted++
		if groups[idx].bestLatency == 0 || results[i].tcpDuration < groups[idx].bestLatency {
			groups[idx].bestLatency = results[i].tcpDuration
		}
	}
	return accepted
}

func allocateNSBRefill(groups []nsbCIDRGroup, missing int) []int {
	alloc := make([]int, len(groups))
	if missing <= 0 {
		return alloc
	}
	survivors := make([]int, 0, len(groups))
	for i := range groups {
		if groups[i].accepted > 0 {
			survivors = append(survivors, i)
		}
	}
	if len(survivors) == 0 {
		return alloc
	}
	sort.SliceStable(survivors, func(i, j int) bool {
		a := groups[survivors[i]]
		b := groups[survivors[j]]
		if a.bestLatency != b.bestLatency {
			if a.bestLatency == 0 {
				return false
			}
			if b.bestLatency == 0 {
				return true
			}
			return a.bestLatency < b.bestLatency
		}
		return a.order < b.order
	})
	base := missing / len(survivors)
	remainder := missing % len(survivors)
	for rank, idx := range survivors {
		alloc[idx] = base
		if rank < remainder {
			alloc[idx]++
		}
	}
	return alloc
}

func generateNSBUniqueCIDRIPs(group *nsbCIDRGroup, count int) []string {
	if group == nil || count <= 0 {
		return nil
	}
	result := make([]string, 0, count)
	maxAttempts := count*128 + 512
	for attempts := 0; len(result) < count && attempts < maxAttempts; attempts++ {
		ip, ok := randomIPFromCIDR(group.cidr)
		if !ok {
			break
		}
		if _, used := group.used[ip]; used {
			continue
		}
		addr, err := netip.ParseAddr(ip)
		if err != nil || !group.prefix.Contains(addr) {
			continue
		}
		group.used[ip] = struct{}{}
		result = append(result, ip)
	}
	return result
}

'''
    g_replace(
        '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {\n''',
        helper + '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {\n''',
        "CIDR智能重分配辅助函数",
    )

if "cidrInitialCount := 0" not in go:
    g_replace(
        '''\tif len(expandedEntries) == 0 {\n\t\tsession.sendWSMessage("error", "没有可扫描的有效地址")\n\t\treturn\n\t}\n\n\tsession.sendWSMessage("log", fmt.Sprintf("输入 %d 条记录，解析为 %d 个地址", len(ips), len(expandedEntries)))\n''',
        '''\tif len(expandedEntries) == 0 {\n\t\tsession.sendWSMessage("error", "没有可扫描的有效地址")\n\t\treturn\n\t}\n\n\tcidrGroups := parseNSBCIDRGroups(fileContent, fallbackPort)\n\tcidrInitialCount := 0\n\tfor i := range expandedEntries {\n\t\tgroupIndex := findNSBCIDRGroup(expandedEntries[i].ip, expandedEntries[i].port, cidrGroups)\n\t\tif groupIndex < 0 {\n\t\t\tcontinue\n\t\t}\n\t\tcidrGroups[groupIndex].used[expandedEntries[i].ip] = struct{}{}\n\t\tcidrInitialCount++\n\t}\n\n\tsession.sendWSMessage("log", fmt.Sprintf("输入 %d 条记录，解析为 %d 个地址", len(ips), len(expandedEntries)))\n\tif delay > 0 && cidrInitialCount > 0 {\n\t\tsession.sendWSMessage("log", fmt.Sprintf("智能号段模式：扫描合格延迟=%dms；CIDR首轮名额=%d，超过阈值或失败的地址直接淘汰，不参与结果计数", delay, cidrInitialCount))\n\t}\n''',
        "初始化CIDR智能名额",
    )

if "智能补扫第 %d 轮" not in go:
    old = '''\t\tsession.sendWSMessage("nsb_scan_result", res.toNSBLiveMessage("", compact))\n\t\treturn accepted\n\t})\n\n\tif wasCanceled || ctx.Err() != nil {\n'''
    adaptive = r'''		session.sendWSMessage("nsb_scan_result", res.toNSBLiveMessage("", compact))
		return accepted
	})

	if !wasCanceled && ctx.Err() == nil && delay > 0 && cidrInitialCount > 0 && len(cidrGroups) > 0 {
		acceptedCIDR := resetNSBCIDRStats(cidrGroups, nsbResults)
		nonCIDRAccepted := len(nsbResults) - acceptedCIDR
		targetCIDR := cidrInitialCount
		if resultLimit > 0 {
			capacity := resultLimit - nonCIDRAccepted
			if capacity < 0 {
				capacity = 0
			}
			if targetCIDR > capacity {
				targetCIDR = capacity
			}
		}

		const maxAdaptiveRounds = 6
		zeroSuccessRounds := 0
		for round := 1; round <= maxAdaptiveRounds && acceptedCIDR < targetCIDR; round++ {
			missing := targetCIDR - acceptedCIDR
			allocations := allocateNSBRefill(cidrGroups, missing)
			refillEntries := make([]nsbAdaptiveEntry, 0, missing)
			survivorCount := 0
			for groupIndex, quota := range allocations {
				if cidrGroups[groupIndex].accepted > 0 {
					survivorCount++
				}
				if quota <= 0 {
					continue
				}
				for _, ip := range generateNSBUniqueCIDRIPs(&cidrGroups[groupIndex], quota) {
					refillEntries = append(refillEntries, nsbAdaptiveEntry{
						ip:            ip,
						port:          cidrGroups[groupIndex].port,
						originalInput: cidrGroups[groupIndex].cidr,
						groupIndex:    groupIndex,
					})
				}
			}

			if len(refillEntries) == 0 {
				if survivorCount == 0 {
					session.sendWSMessage("log", fmt.Sprintf("智能补扫停止：首轮 CIDR 合格=%d/%d，没有存活号段可接收空缺名额", acceptedCIDR, targetCIDR))
				} else {
					session.sendWSMessage("log", "智能补扫停止：无法继续生成不重复地址")
				}
				break
			}

			session.sendWSMessage("log", fmt.Sprintf("智能补扫第 %d 轮：当前 CIDR 合格=%d/%d，空缺=%d，存活号段=%d，本轮随机补充=%d（不重复）", round, acceptedCIDR, targetCIDR, missing, survivorCount, len(refillEntries)))
			reportNSBProgress(session, "scan", 0, len(refillEntries), "智能补扫中")

			refillSucceeded := 0
			processed := 0
			var refillMutex sync.Mutex
			refillCanceled := runNSBScanWorkers(ctx, len(refillEntries), maxThreads, 0, func(current int) {
				reportNSBProgress(session, "scan", min(current, len(refillEntries)), len(refillEntries), "智能补扫中")
			}, func(idx int) int {
				finishOne := func() int {
					refillMutex.Lock()
					processed++
					current := processed
					refillMutex.Unlock()
					return current
				}

				itemCtx, itemCancel := context.WithTimeout(ctx, 10*time.Second)
				defer itemCancel()
				entry := refillEntries[idx]
				item := fmt.Sprintf("%s %d", entry.ip, entry.port)
				var res *iptestResult
				var failure *nsbFailureRecord
				if scanMode == scanModeHTTPing {
					res, failure = scanNSBEntryHTTP(itemCtx, item, fallbackPort, enableTLS, delay, targetDC, idx)
				} else {
					res, failure = scanNSBEntry(itemCtx, item, fallbackPort, enableTLS, delay, targetDC, idx)
				}
				if debugMode && failure != nil {
					failMutex.Lock()
					failures = append(failures, *failure)
					failMutex.Unlock()
				}
				if res == nil {
					return finishOne()
				}

				res.originalInput = entry.originalInput
				resMutex.Lock()
				nsbResults = append(nsbResults, *res)
				resMutex.Unlock()

				refillMutex.Lock()
				refillSucceeded++
				refillMutex.Unlock()
				session.sendWSMessage("nsb_scan_result", res.toNSBLiveMessage("", compact))
				return finishOne()
			})

			if refillCanceled || ctx.Err() != nil {
				wasCanceled = true
				break
			}

			acceptedCIDR = resetNSBCIDRStats(cidrGroups, nsbResults)
			session.sendWSMessage("log", fmt.Sprintf("智能补扫第 %d 轮完成：新增合格 %d/%d，CIDR 当前合格=%d/%d", round, refillSucceeded, len(refillEntries), acceptedCIDR, targetCIDR))
			if refillSucceeded == 0 {
				zeroSuccessRounds++
				if zeroSuccessRounds >= 2 {
					session.sendWSMessage("log", "智能补扫连续两轮没有新增合格地址，停止补扫")
					break
				}
			} else {
				zeroSuccessRounds = 0
			}
		}
	}

	if wasCanceled || ctx.Err() != nil {
'''
    g_replace(old, adaptive, "延迟淘汰后智能重分配补扫")

# ---------------------------------------------------------------------------
# 4) V4：网段首轮随机数可配置；扫描合格数量 = 网段最终目标数量；
#         测速不合格则在同网段最多换 10 轮，仍不合格取最高速度兜底。
# ---------------------------------------------------------------------------
if 'id="nsbCIDRSamples"' not in html:
    h_replace(
        '''                <div class="option-item">\n                    <span class="label" title="延迟测试通过的结果数量上限">🎯 扫描合格数量</span>\n                    <input id="nsbResultLimit" type="number" value="1000" placeholder="非 0 正整数">\n                </div>\n''',
        '''                <div class="option-item">\n                    <span class="label" title="网段模式最终希望得到的具体 IP 总数；会在通过延迟筛选的 /24 或 /48 之间平均分配，余数优先给最低延迟网段">🎯 扫描合格数量</span>\n                    <input id="nsbResultLimit" type="number" value="1000" placeholder="网段模式最终总数">\n                </div>\n                <div class="option-item">\n                    <span class="label" title="仅网段输入生效：每个 /24 或 /48 第一轮先随机抽多少个具体 IP，用于判断这个网段是否值得继续深挖">🎲 网段首轮随机数</span>\n                    <input id="nsbCIDRSamples" type="number" value="4" min="1" max="256" placeholder="默认 4">\n                </div>\n''',
        "新增网段首轮随机数设置",
    )

if "cidrSamples: val('nsbCIDRSamples')" not in html:
    h_replace(
        '''                    resultLimit: val('nsbResultLimit'),\n''',
        '''                    resultLimit: val('nsbResultLimit'),\n                    cidrSamples: val('nsbCIDRSamples'),\n''',
        "保存网段首轮随机数配置",
    )

if "setValue('nsbCIDRSamples', n.cidrSamples);" not in html:
    h_replace(
        '''            setValue('nsbResultLimit', n.resultLimit);\n''',
        '''            setValue('nsbResultLimit', n.resultLimit);\n            setValue('nsbCIDRSamples', n.cidrSamples);\n''',
        "恢复网段首轮随机数配置",
    )

if "const cidrSamples = Math.min(256" not in html:
    h_replace(
        '''            const resultLimit = parseInt(document.getElementById('nsbResultLimit').value) || 0;\n''',
        '''            const resultLimit = parseInt(document.getElementById('nsbResultLimit').value) || 0;\n            const cidrSamples = Math.min(256, Math.max(1, parseInt(document.getElementById('nsbCIDRSamples')?.value || '4', 10) || 4));\n''',
        "读取网段首轮随机数",
    )

if "if (cidrSamples <= 0 || cidrSamples > 256)" not in html:
    h_replace(
        '''            if (resultLimit <= 0) {\n                showNoticeCard('延迟结果上限必须填写非 0 正整数');\n                return;\n            }\n''',
        '''            if (resultLimit <= 0) {\n                showNoticeCard('扫描合格数量必须填写非 0 正整数');\n                return;\n            }\n            if (cidrSamples <= 0 || cidrSamples > 256) {\n                showNoticeCard('网段首轮随机数必须在 1-256 之间');\n                return;\n            }\n''',
        "校验网段首轮随机数",
    )

if "                    cidrSamples," not in html:
    h_replace(
        '''                    resultLimit,\n                    dc: targetDC,\n''',
        '''                    resultLimit,\n                    cidrSamples,\n                    dc: targetDC,\n''',
        "发送网段首轮随机数",
    )

if "nsbSpeedEnabledForResults = speedTest > 0;" not in html:
    h_replace(
        '''            nsbSpeedEnabledForResults = speedTest > 0 && (parseInt(document.getElementById('nsbSpeedLimit').value) || 0) > 0;\n''',
        '''            nsbSpeedEnabledForResults = speedTest > 0;\n''',
        "网段智能测速不再依赖测速结果数量开关",
    )

if "网段智能模式下最终数量由“扫描合格数量”控制" not in html:
    html = html.replace(
        '<span class="label" title="测速达标结果的最大数量，关闭测速填 0">🏁 测速结果数量</span>',
        '<span class="label" title="完整 IP 模式的一键测速上限；网段智能模式下最终数量由“扫描合格数量”控制">🏁 测速结果数量</span>',
        1,
    )

# protocol.go: transport the new setting.
if 'CIDRSamples' not in protocol:
    p_replace(
        '''\tResultLimit  int     `json:"resultLimit"`\n''',
        '''\tResultLimit  int     `json:"resultLimit"`\n\tCIDRSamples  int     `json:"cidrSamples"`\n''',
        "协议增加CIDR首轮随机数",
    )

# server.go: default/clamp and pass through.
if "params.CIDRSamples <= 0" not in server:
    s_replace(
        '''\t\t\tif params.ResultLimit < 0 {\n\t\t\t\tparams.ResultLimit = 0\n\t\t\t}\n''',
        '''\t\t\tif params.ResultLimit < 0 {\n\t\t\t\tparams.ResultLimit = 0\n\t\t\t}\n\t\t\tif params.CIDRSamples <= 0 {\n\t\t\t\tparams.CIDRSamples = 4\n\t\t\t}\n\t\t\tif params.CIDRSamples > 256 {\n\t\t\t\tparams.CIDRSamples = 256\n\t\t\t}\n''',
        "服务端默认CIDR首轮随机数",
    )

if '"cidrSamples": params.CIDRSamples' not in server:
    s_replace(
        '''"delay": params.Delay, "resultLimit": params.ResultLimit, "dc": params.DC''',
        '''"delay": params.Delay, "resultLimit": params.ResultLimit, "cidrSamples": params.CIDRSamples, "dc": params.DC''',
        "后台任务记录CIDR首轮随机数",
    )

if "params.ResultLimit, params.CIDRSamples, params.DC" not in server:
    s_replace(
        '''params.Delay, params.ResultLimit, params.DC, params.SpeedMin''',
        '''params.Delay, params.ResultLimit, params.CIDRSamples, params.DC, params.SpeedMin''',
        "服务端传递CIDR首轮随机数",
    )

# utils.go: non-standard CIDR sampling count is independent from official mode.
if '"sync"' not in utils:
    u_replace(
        '''\t"strings"\n)''',
        '''\t"strings"\n\t"sync"\n)''',
        "utils加入sync导入",
    )

if "func readIPsWithFallbackPortNSBSamples(" not in utils:
    u_replace(
        '''// parseNSBCIDRLine turns a CIDR-only input line into concrete random IP endpoints.\n''',
        '''const defaultNSBCIDRSamplesPerPrefix = 4\n\nvar (\n\tnsbCIDRParseMu            sync.Mutex\n\tnsbCIDRSamplesPerPrefix   = defaultNSBCIDRSamplesPerPrefix\n)\n\nfunc readIPsWithFallbackPortNSBSamples(path string, fallbackPort int, samples int) ([]string, error) {\n\tif samples <= 0 {\n\t\tsamples = defaultNSBCIDRSamplesPerPrefix\n\t}\n\tif samples > 256 {\n\t\tsamples = 256\n\t}\n\tnsbCIDRParseMu.Lock()\n\told := nsbCIDRSamplesPerPrefix\n\tnsbCIDRSamplesPerPrefix = samples\n\tips, err := readIPsWithFallbackPort(path, fallbackPort)\n\tnsbCIDRSamplesPerPrefix = old\n\tnsbCIDRParseMu.Unlock()\n\treturn ips, err\n}\n\n// parseNSBCIDRLine turns a CIDR-only input line into concrete random IP endpoints.\n''',
        "非标CIDR随机数上下文",
    )

if "getRandomIPv4sN([]string{cidr}, nsbCIDRSamplesPerPrefix)" not in utils:
    u_replace(
        '''\t\tips = getRandomIPv4sN([]string{cidr}, officialIPv4SamplesPer24)\n\t} else {\n\t\tips = getRandomIPv6sN([]string{cidr}, officialIPv6SamplesPer48)\n''',
        '''\t\tips = getRandomIPv4sN([]string{cidr}, nsbCIDRSamplesPerPrefix)\n\t} else {\n\t\tips = getRandomIPv6sN([]string{cidr}, nsbCIDRSamplesPerPrefix)\n''',
        "非标CIDR使用独立首轮随机数",
    )

# tasks_nsb.go: configurable parser count.
if "resultLimit int, cidrSamples int, targetDC" not in go:
    g_replace(
        '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {''',
        '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, cidrSamples int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {''',
        "runNSBTask接收CIDR首轮随机数",
    )

if "readIPsWithFallbackPortNSBSamples(tmpPath, fallbackPort, cidrSamples)" not in go:
    g_replace(
        '''\tips, err := readIPsWithFallbackPort(tmpPath, fallbackPort)\n''',
        '''\tips, err := readIPsWithFallbackPortNSBSamples(tmpPath, fallbackPort, cidrSamples)\n''',
        "非标解析使用可配置CIDR随机数",
    )

# Additional V4 helpers are inserted before runNSBTask after V3 helpers already exist.
if "func allocateNSBTargetQuotas(" not in go:
    v4_helpers = r'''func allocateNSBTargetQuotas(groups []nsbCIDRGroup, total int) []int {
	targets := make([]int, len(groups))
	if total <= 0 {
		return targets
	}
	survivors := make([]int, 0, len(groups))
	for i := range groups {
		if groups[i].accepted > 0 {
			survivors = append(survivors, i)
		}
	}
	if len(survivors) == 0 {
		return targets
	}
	sort.SliceStable(survivors, func(i, j int) bool {
		a := groups[survivors[i]]
		b := groups[survivors[j]]
		if a.bestLatency != b.bestLatency {
			if a.bestLatency == 0 {
				return false
			}
			if b.bestLatency == 0 {
				return true
			}
			return a.bestLatency < b.bestLatency
		}
		return a.order < b.order
	})
	base := total / len(survivors)
	remainder := total % len(survivors)
	for rank, idx := range survivors {
		targets[idx] = base
		if rank < remainder {
			targets[idx]++
		}
	}
	return targets
}

func allocateNSBOverflow(groups []nsbCIDRGroup, eligible []bool, missing int) []int {
	alloc := make([]int, len(groups))
	if missing <= 0 {
		return alloc
	}
	indices := make([]int, 0, len(groups))
	for i := range groups {
		if i < len(eligible) && eligible[i] && groups[i].accepted > 0 {
			indices = append(indices, i)
		}
	}
	if len(indices) == 0 {
		for i := range groups {
			if groups[i].accepted > 0 {
				indices = append(indices, i)
			}
		}
	}
	if len(indices) == 0 {
		return alloc
	}
	sort.SliceStable(indices, func(i, j int) bool {
		a := groups[indices[i]]
		b := groups[indices[j]]
		if a.bestLatency != b.bestLatency {
			if a.bestLatency == 0 {
				return false
			}
			if b.bestLatency == 0 {
				return true
			}
			return a.bestLatency < b.bestLatency
		}
		return a.order < b.order
	})
	base := missing / len(indices)
	remainder := missing % len(indices)
	for rank, idx := range indices {
		alloc[idx] = base
		if rank < remainder {
			alloc[idx]++
		}
	}
	return alloc
}

func splitNSBResultsByCIDR(results []iptestResult, groups []nsbCIDRGroup) ([]iptestResult, [][]iptestResult) {
	nonCIDR := make([]iptestResult, 0)
	pools := make([][]iptestResult, len(groups))
	for i := range results {
		idx := findNSBCIDRGroup(results[i].ipAddr, results[i].port, groups)
		if idx < 0 {
			nonCIDR = append(nonCIDR, results[i])
			continue
		}
		pools[idx] = append(pools[idx], results[i])
	}
	return nonCIDR, pools
}

func sortNSBLatencyPool(pool []iptestResult) {
	sort.SliceStable(pool, func(i, j int) bool {
		if pool[i].lossRate != pool[j].lossRate {
			return pool[i].lossRate < pool[j].lossRate
		}
		return pool[i].tcpDuration < pool[j].tcpDuration
	})
}

func sortNSBSpeedBest(pool []iptestResult) {
	sort.SliceStable(pool, func(i, j int) bool {
		if pool[i].speedQualified != pool[j].speedQualified {
			return pool[i].speedQualified
		}
		if pool[i].downloadSpeed != pool[j].downloadSpeed {
			return pool[i].downloadSpeed > pool[j].downloadSpeed
		}
		if pool[i].lossRate != pool[j].lossRate {
			return pool[i].lossRate < pool[j].lossRate
		}
		return pool[i].tcpDuration < pool[j].tcpDuration
	})
}

func countNSBSpeedQualified(pool []iptestResult) int {
	count := 0
	for i := range pool {
		if pool[i].speedTested && pool[i].speedQualified {
			count++
		}
	}
	return count
}

func runNSBAdaptiveScanBatch(ctx context.Context, session *appSession, entries []nsbAdaptiveEntry, maxThreads, fallbackPort int, enableTLS bool, delay int, targetDC string, compact bool, scanMode string, label string) ([]iptestResult, bool) {
	if len(entries) == 0 {
		return nil, false
	}
	results := make([]iptestResult, 0, len(entries))
	var resultsMu sync.Mutex
	processed := 0
	var progressMu sync.Mutex
	reportNSBProgress(session, "scan", 0, len(entries), label)
	canceled := runNSBScanWorkers(ctx, len(entries), maxThreads, 0, func(current int) {
		reportNSBProgress(session, "scan", min(current, len(entries)), len(entries), label)
	}, func(idx int) int {
		itemCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()
		entry := entries[idx]
		item := fmt.Sprintf("%s %d", entry.ip, entry.port)
		var res *iptestResult
		if scanMode == scanModeHTTPing {
			res, _ = scanNSBEntryHTTP(itemCtx, item, fallbackPort, enableTLS, delay, targetDC, idx)
		} else {
			res, _ = scanNSBEntry(itemCtx, item, fallbackPort, enableTLS, delay, targetDC, idx)
		}
		if res != nil {
			res.originalInput = entry.originalInput
			resultsMu.Lock()
			results = append(results, *res)
			resultsMu.Unlock()
			session.sendWSMessage("nsb_scan_result", res.toNSBLiveMessage("", compact))
		}
		progressMu.Lock()
		processed++
		current := processed
		progressMu.Unlock()
		return current
	})
	return results, canceled
}

func runNSBAdaptiveSpeedBatch(ctx context.Context, session *appSession, candidates []iptestResult, maxWorkers int, speedURL string, enableTLS bool, speedMin float64, compact bool, label string) ([]iptestResult, bool) {
	if len(candidates) == 0 {
		return nil, false
	}
	results := append([]iptestResult(nil), candidates...)
	reportNSBProgress(session, "speed", 0, len(results), label)
	canceled := runNSBSpeedWorkers(ctx, results, maxWorkers, len(results), speedMin, func(tested, qualified int) {
		reportNSBProgress(session, "speed", min(tested, len(results)), len(results), label)
	}, func(idx int, speedErr string) {
		res := &results[idx]
		if res.speedTested && res.speedText == "" {
			res.speedText = fmt.Sprintf("%.2fMB/s", res.downloadSpeed/1024)
		}
		session.sendWSMessage("nsb_scan_result", res.toNSBLiveMessage(res.speedText, compact))
	}, func(idx int) (float64, string) {
		res := &results[idx]
		return runNSBDownloadSpeed(ctx, res.ipAddr, res.port, enableTLS, speedURL)
	})
	for i := range results {
		if results[i].speedTested && results[i].speedText == "" {
			results[i].speedText = fmt.Sprintf("%.2fMB/s", results[i].downloadSpeed/1024)
		}
	}
	return results, canceled
}

'''
    old_sig = '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, cidrSamples int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {'''
    g_replace(old_sig, v4_helpers + old_sig, "增加V4网段目标/测速辅助函数")

# Initial CIDR probing must inspect every prefix, instead of stopping when resultLimit is reached.
if "scanResultLimit := resultLimit" not in go:
    g_replace(
        '''\ttotal := len(expandedEntries)\n\tif resultLimit > 0 && resultLimit < total {\n\t\ttotal = resultLimit\n\t}\n''',
        '''\ttotal := len(expandedEntries)\n\tif cidrInitialCount == 0 && resultLimit > 0 && resultLimit < total {\n\t\ttotal = resultLimit\n\t}\n\tscanResultLimit := resultLimit\n\tif cidrInitialCount > 0 {\n\t\t// 网段模式首轮必须先给每个网段相同的探测机会，不能被最终结果数量提前截断。\n\t\tscanResultLimit = 0\n\t}\n''',
        "网段首轮扫描全部样本",
    )
    g_replace(
        '''\twasCanceled := runNSBScanWorkers(ctx, len(expandedEntries), maxThreads, resultLimit, func(current int) {\n''',
        '''\twasCanceled := runNSBScanWorkers(ctx, len(expandedEntries), maxThreads, scanResultLimit, func(current int) {\n''',
        "网段首轮不被resultLimit提前停止",
    )

# Replace V3's delay-only adaptive block with V4 quota + speed replacement logic.
if "网段V4：扫描合格数量=" not in go:
    pattern = r'''\tif !wasCanceled && ctx\.Err\(\) == nil && delay > 0 && cidrInitialCount > 0 && len\(cidrGroups\) > 0 \{.*?\n\t\}\n\n\tif wasCanceled \|\| ctx\.Err\(\) != nil \{'''
    replacement = '''\tsmartCIDRSpeedDone := false
\tsmartQualifiedCount := 0
\tsmartFallbackCount := 0

\tif !wasCanceled && ctx.Err() == nil && cidrInitialCount > 0 && len(cidrGroups) > 0 {
\t\tacceptedCIDR := resetNSBCIDRStats(cidrGroups, nsbResults)
\t\tnonCIDR, groupPools := splitNSBResultsByCIDR(nsbResults, cidrGroups)
\t\tif resultLimit > 0 && len(nonCIDR) > resultLimit {
\t\t\tsortNSBResults(nonCIDR, 0)
\t\t\tnonCIDR = nonCIDR[:resultLimit]
\t\t}
\t\ttargetCIDR := resultLimit - len(nonCIDR)
\t\tif targetCIDR < 0 {
\t\t\ttargetCIDR = 0
\t\t}
\t\ttargets := allocateNSBTargetQuotas(cidrGroups, targetCIDR)
\t\tsurvivors := 0
\t\tfor i := range targets {
\t\t\tif targets[i] > 0 {
\t\t\t\tsurvivors++
\t\t\t}
\t\t\tsortNSBLatencyPool(groupPools[i])
\t\t\tif targets[i] >= 0 && len(groupPools[i]) > targets[i] {
\t\t\t\tgroupPools[i] = groupPools[i][:targets[i]]
\t\t\t}
\t\t}
\t\tsession.sendWSMessage("log", fmt.Sprintf("网段V4：扫描合格数量=%d 作为最终具体IP目标；首轮每网段随机=%d；首轮CIDR合格=%d，存活网段=%d，目标CIDR名额=%d", resultLimit, cidrSamples, acceptedCIDR, survivors, targetCIDR))

\t\t// 第一阶段：按最终 quota 补足通过连接/延迟门槛的具体 IP。
\t\tconst maxCIDRRetryRounds = 10
\t\tfor round := 1; round <= maxCIDRRetryRounds; round++ {
\t\t\tentries := make([]nsbAdaptiveEntry, 0)
\t\t\tmissing := 0
\t\t\tfor groupIndex := range cidrGroups {
\t\t\t\tneed := targets[groupIndex] - len(groupPools[groupIndex])
\t\t\t\tif need <= 0 {
\t\t\t\t\tcontinue
\t\t\t\t}
\t\t\t\tmissing += need
\t\t\t\tfor _, ip := range generateNSBUniqueCIDRIPs(&cidrGroups[groupIndex], need) {
\t\t\t\t\tentries = append(entries, nsbAdaptiveEntry{ip: ip, port: cidrGroups[groupIndex].port, originalInput: cidrGroups[groupIndex].cidr, groupIndex: groupIndex})
\t\t\t\t}
\t\t\t}
\t\t\tif missing <= 0 || len(entries) == 0 {
\t\t\t\tbreak
\t\t\t}
\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段延迟补充第 %d/10 轮：缺 %d 个，本轮随机 %d 个不重复地址", round, missing, len(entries)))
\t\t\tbatch, canceled := runNSBAdaptiveScanBatch(ctx, session, entries, maxThreads, fallbackPort, enableTLS, delay, targetDC, compact, scanMode, "网段延迟补充")
\t\t\tif canceled || ctx.Err() != nil {
\t\t\t\twasCanceled = true
\t\t\t\tbreak
\t\t\t}
\t\t\tfor i := range batch {
\t\t\t\tidx := findNSBCIDRGroup(batch[i].ipAddr, batch[i].port, cidrGroups)
\t\t\t\tif idx >= 0 {
\t\t\t\t\tgroupPools[idx] = append(groupPools[idx], batch[i])
\t\t\t\t}
\t\t\t}
\t\t}

\t\t// 如果某个存活网段在 10 轮内仍填不满，把空缺让给已经能稳定填满的合格网段。
\t\tif !wasCanceled && ctx.Err() == nil {
\t\t\tdeficit := 0
\t\t\tfilled := make([]bool, len(cidrGroups))
\t\t\tfor i := range cidrGroups {
\t\t\t\tfilled[i] = targets[i] > 0 && len(groupPools[i]) >= targets[i]
\t\t\t\tif len(groupPools[i]) < targets[i] {
\t\t\t\t\tdeficit += targets[i] - len(groupPools[i])
\t\t\t\t\ttargets[i] = len(groupPools[i])
\t\t\t\t}
\t\t\t}
\t\t\tif deficit > 0 {
\t\t\t\textra := allocateNSBOverflow(cidrGroups, filled, deficit)
\t\t\t\tfor i := range targets {
\t\t\t\t\ttargets[i] += extra[i]
\t\t\t\t}
\t\t\t\tsession.sendWSMessage("log", fmt.Sprintf("有 %d 个延迟名额在原网段 10 轮内无法补足，已平均转移给可用网段，余数优先最低延迟网段", deficit))
\t\t\t\tfor round := 1; round <= maxCIDRRetryRounds; round++ {
\t\t\t\t\tentries := make([]nsbAdaptiveEntry, 0)
\t\t\t\t\tfor groupIndex := range cidrGroups {
\t\t\t\t\t\tneed := targets[groupIndex] - len(groupPools[groupIndex])
\t\t\t\t\t\tif need <= 0 {
\t\t\t\t\t\t\tcontinue
\t\t\t\t\t\t}
\t\t\t\t\t\tfor _, ip := range generateNSBUniqueCIDRIPs(&cidrGroups[groupIndex], need) {
\t\t\t\t\t\t\tentries = append(entries, nsbAdaptiveEntry{ip: ip, port: cidrGroups[groupIndex].port, originalInput: cidrGroups[groupIndex].cidr, groupIndex: groupIndex})
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tif len(entries) == 0 {
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t\tbatch, canceled := runNSBAdaptiveScanBatch(ctx, session, entries, maxThreads, fallbackPort, enableTLS, delay, targetDC, compact, scanMode, "转移名额补充")
\t\t\t\t\tif canceled || ctx.Err() != nil {
\t\t\t\t\t\twasCanceled = true
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t\tfor i := range batch {
\t\t\t\t\t\tidx := findNSBCIDRGroup(batch[i].ipAddr, batch[i].port, cidrGroups)
\t\t\t\t\t\tif idx >= 0 {
\t\t\t\t\t\t\tgroupPools[idx] = append(groupPools[idx], batch[i])
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}

\t\tif !wasCanceled && ctx.Err() == nil {
\t\t\tfor i := range groupPools {
\t\t\t\tsortNSBLatencyPool(groupPools[i])
\t\t\t\tif len(groupPools[i]) > targets[i] {
\t\t\t\t\tgroupPools[i] = groupPools[i][:targets[i]]
\t\t\t\t}
\t\t\t}

\t\t\t// 第二阶段：自动测速开启时，测试合格速度成为网段内的替换门槛。
\t\t\tif speedTest > 0 && targetCIDR > 0 {
\t\t\t\tsmartCIDRSpeedDone = true
\t\t\t\tif speedLimit > 0 && speedLimit != resultLimit {
\t\t\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段智能测速：忽略测速结果数量=%d；最终数量由扫描合格数量=%d 控制", speedLimit, resultLimit))
\t\t\t\t}
\t\t\t\tinitialCandidates := append([]iptestResult(nil), nonCIDR...)
\t\t\t\tfor i := range groupPools {
\t\t\t\t\tinitialCandidates = append(initialCandidates, groupPools[i]...)
\t\t\t\t}
\t\t\t\ttested, canceled := runNSBAdaptiveSpeedBatch(ctx, session, initialCandidates, speedTest, speedURL, enableTLS, speedMin, compact, "网段测速")
\t\t\t\tif canceled || ctx.Err() != nil {
\t\t\t\t\twasCanceled = true
\t\t\t\t} else {
\t\t\t\t\tnonCIDR, groupPools = splitNSBResultsByCIDR(tested, cidrGroups)
\t\t\t\t}

\t\t\t\tfor round := 1; round <= maxCIDRRetryRounds && !wasCanceled && ctx.Err() == nil; round++ {
\t\t\t\t\tentries := make([]nsbAdaptiveEntry, 0)
\t\t\t\t\tmissing := 0
\t\t\t\t\tfor groupIndex := range cidrGroups {
\t\t\t\t\t\tneed := targets[groupIndex] - countNSBSpeedQualified(groupPools[groupIndex])
\t\t\t\t\t\tif need <= 0 {
\t\t\t\t\t\t\tcontinue
\t\t\t\t\t\t}
\t\t\t\t\t\tmissing += need
\t\t\t\t\t\tfor _, ip := range generateNSBUniqueCIDRIPs(&cidrGroups[groupIndex], need) {
\t\t\t\t\t\t\tentries = append(entries, nsbAdaptiveEntry{ip: ip, port: cidrGroups[groupIndex].port, originalInput: cidrGroups[groupIndex].cidr, groupIndex: groupIndex})
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tif missing <= 0 || len(entries) == 0 {
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段速度替换第 %d/10 轮：还有 %d 个未达到 %.2fMB/s，本轮换 %d 个不重复地址", round, missing, speedMin, len(entries)))
\t\t\t\t\tscanned, scanCanceled := runNSBAdaptiveScanBatch(ctx, session, entries, maxThreads, fallbackPort, enableTLS, delay, targetDC, compact, scanMode, "速度替换-延迟筛选")
\t\t\t\t\tif scanCanceled || ctx.Err() != nil {
\t\t\t\t\t\twasCanceled = true
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t\tif len(scanned) == 0 {
\t\t\t\t\t\tcontinue
\t\t\t\t\t}
\t\t\t\t\tretested, speedCanceled := runNSBAdaptiveSpeedBatch(ctx, session, scanned, speedTest, speedURL, enableTLS, speedMin, compact, "速度替换-测速")
\t\t\t\t\tif speedCanceled || ctx.Err() != nil {
\t\t\t\t\t\twasCanceled = true
\t\t\t\t\t\tbreak
\t\t\t\t\t}
\t\t\t\t\tfor i := range retested {
\t\t\t\t\t\tidx := findNSBCIDRGroup(retested[i].ipAddr, retested[i].port, cidrGroups)
\t\t\t\t\t\tif idx >= 0 {
\t\t\t\t\t\t\tgroupPools[idx] = append(groupPools[idx], retested[i])
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}

\t\t\t\tif !wasCanceled && ctx.Err() == nil {
\t\t\t\t\tfinalResults := append([]iptestResult(nil), nonCIDR...)
\t\t\t\t\tfor i := range nonCIDR {
\t\t\t\t\t\tif nonCIDR[i].speedQualified {
\t\t\t\t\t\t\tsmartQualifiedCount++
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tfor groupIndex := range cidrGroups {
\t\t\t\t\t\tquota := targets[groupIndex]
\t\t\t\t\t\tif quota <= 0 {
\t\t\t\t\t\t\tcontinue
\t\t\t\t\t\t}
\t\t\t\t\t\tqualified := make([]iptestResult, 0)
\t\t\t\t\t\tfallback := make([]iptestResult, 0)
\t\t\t\t\t\tfor _, candidate := range groupPools[groupIndex] {
\t\t\t\t\t\t\tif candidate.speedTested && candidate.speedQualified {
\t\t\t\t\t\t\t\tqualified = append(qualified, candidate)
\t\t\t\t\t\t\t} else {
\t\t\t\t\t\t\t\tfallback = append(fallback, candidate)
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\tsortNSBSpeedBest(qualified)
\t\t\t\t\t\tsortNSBSpeedBest(fallback)
\t\t\t\t\t\tif len(qualified) > quota {
\t\t\t\t\t\t\tqualified = qualified[:quota]
\t\t\t\t\t\t}
\t\t\t\t\t\tchosen := append([]iptestResult(nil), qualified...)
\t\t\t\t\t\tsmartQualifiedCount += len(qualified)
\t\t\t\t\t\tneedFallback := quota - len(chosen)
\t\t\t\t\t\tif needFallback > len(fallback) {
\t\t\t\t\t\t\tneedFallback = len(fallback)
\t\t\t\t\t\t}
\t\t\t\t\t\tif needFallback > 0 {
\t\t\t\t\t\t\tchosen = append(chosen, fallback[:needFallback]...)
\t\t\t\t\t\t\tsmartFallbackCount += needFallback
\t\t\t\t\t\t}
\t\t\t\t\t\tfinalResults = append(finalResults, chosen...)
\t\t\t\t\t}
\t\t\t\t\tnsbResults = finalResults
\t\t\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段智能测速完成：最终 %d 个；达到 %.2fMB/s 的 %d 个；10轮后取最高速度兜底 %d 个", len(nsbResults), speedMin, smartQualifiedCount, smartFallbackCount))
\t\t\t\t}
\t\t\t} else {
\t\t\t\tfinalResults := append([]iptestResult(nil), nonCIDR...)
\t\t\t\tfor groupIndex := range groupPools {
\t\t\t\t\tquota := targets[groupIndex]
\t\t\t\t\tsortNSBLatencyPool(groupPools[groupIndex])
\t\t\t\t\tif len(groupPools[groupIndex]) > quota {
\t\t\t\t\t\tgroupPools[groupIndex] = groupPools[groupIndex][:quota]
\t\t\t\t\t}
\t\t\t\t\tfinalResults = append(finalResults, groupPools[groupIndex]...)
\t\t\t\t}
\t\t\t\tnsbResults = finalResults
\t\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段延迟筛选完成：最终得到 %d/%d 个具体IP", len(nsbResults), resultLimit))
\t\t\t}
\t\t}
\t}

\tif wasCanceled || ctx.Err() != nil {'''
    go2, n = re.subn(pattern, lambda _m: replacement, go, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"[nsb-patch] V4替换智能网段主流程失败，匹配数={n}")
    go = go2
    changed.append("V4网段目标总数+速度10轮替换")

# Existing ordinary speed stage stays for exact-IP mode only.
if "qualifiedCount := smartQualifiedCount" not in go:
    g_replace(
        '''\tqualifiedCount := 0\n''',
        '''\tqualifiedCount := smartQualifiedCount\n''',
        "智能网段测速合格数接入最终结果",
    )

if "&& !smartCIDRSpeedDone" not in go:
    g_replace(
        '''\tif !wasCanceled && ctx.Err() == nil && speedTest > 0 && speedLimit > 0 {\n''',
        '''\tif !wasCanceled && ctx.Err() == nil && speedTest > 0 && speedLimit > 0 && !smartCIDRSpeedDone {\n''',
        "网段智能测速完成后跳过旧测速流程",
    )

if "10次最优兜底" not in go:
    raise SystemExit("[nsb-patch] V4速度兜底逻辑没有成功写入")

if "completionMessage = fmt.Sprintf(\"网段智能测速完成" not in go:
    g_replace(
        '''\tif wasCanceled || ctx.Err() != nil {\n\t\tsession.sendWSMessage("log", "非标测速任务已终止，正在整理当前可用测速结果...")\n''',
        '''\tif smartCIDRSpeedDone && !wasCanceled && ctx.Err() == nil {\n\t\tcompletionStatus = "complete"\n\t\tcompletionMessage = fmt.Sprintf("网段智能测速完成：速度合格 %d，10次最优兜底 %d", smartQualifiedCount, smartFallbackCount)\n\t}\n\n\tif wasCanceled || ctx.Err() != nil {\n\t\tsession.sendWSMessage("log", "非标测速任务已终止，正在整理当前可用测速结果...")\n''',
        "智能网段测速完成状态",
    )


INDEX.write_text(html, encoding="utf-8")
TASKS.write_text(go, encoding="utf-8")
UTILS.write_text(utils, encoding="utf-8")
PROTOCOL.write_text(protocol, encoding="utf-8")
SERVER.write_text(server, encoding="utf-8")

print("[nsb-patch] 已应用:")
for item in changed:
    print(" -", item)
print("[nsb-patch] 完成")
