#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "combined_refactor" / "index.html"
TASKS = ROOT / "combined_refactor" / "tasks_nsb.go"

html = INDEX.read_text(encoding="utf-8")
go = TASKS.read_text(encoding="utf-8")
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

INDEX.write_text(html, encoding="utf-8")
TASKS.write_text(go, encoding="utf-8")

print("[nsb-patch] 已应用:")
for item in changed:
    print(" -", item)
print("[nsb-patch] 完成")
