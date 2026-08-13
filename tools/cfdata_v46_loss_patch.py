#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "combined_refactor" / "index.html"
PROTOCOL = ROOT / "combined_refactor" / "protocol.go"
SERVER = ROOT / "combined_refactor" / "server.go"
TASKS = ROOT / "combined_refactor" / "tasks_nsb.go"
CLI = ROOT / "combined_refactor" / "cli.go"

html = INDEX.read_text(encoding="utf-8")
protocol = PROTOCOL.read_text(encoding="utf-8")
server = SERVER.read_text(encoding="utf-8")
go = TASKS.read_text(encoding="utf-8")
cli = CLI.read_text(encoding="utf-8")
changed = []

def rep(text, old, new, name, count=1):
    if old not in text:
        raise SystemExit(f"[v4.6-loss] 找不到目标: {name}")
    out = text.replace(old, new, count)
    changed.append(name)
    return out

if "lossLimit: parseFloat(document.getElementById('nsbLossLimit')" not in html:
    html = rep(
        html,
        '''                    cidrSamples,
                    dc: targetDC,
''',
        '''                    cidrSamples,
                    lossLimit: parseFloat(document.getElementById('nsbLossLimit')?.value || '100'),
                    dc: targetDC,
''',
        "前端发送最大丢包率",
    )

if 'LossLimit' not in protocol:
    protocol = rep(
        protocol,
        '''\tCIDRSamples  int     `json:"cidrSamples"`
''',
        '''\tCIDRSamples  int      `json:"cidrSamples"`
\tLossLimit    *float64 `json:"lossLimit,omitempty"`
''',
        "协议增加最大丢包率",
    )

if "lossLimit := 100.0" not in server:
    server = rep(
        server,
        '''\t\t\tif params.CIDRSamples > 256 {
\t\t\t\tparams.CIDRSamples = 256
\t\t\t}
''',
        '''\t\t\tif params.CIDRSamples > 256 {
\t\t\t\tparams.CIDRSamples = 256
\t\t\t}
\t\t\tlossLimit := 100.0
\t\t\tif params.LossLimit != nil {
\t\t\t\tlossLimit = *params.LossLimit
\t\t\t\tif lossLimit < 0 {
\t\t\t\t\tlossLimit = 0
\t\t\t\t}
\t\t\t\tif lossLimit > 100 {
\t\t\t\t\tlossLimit = 100
\t\t\t\t}
\t\t\t}
''',
        "服务端解析最大丢包率",
    )

if '"lossLimit": lossLimit' not in server:
    server = rep(
        server,
        '''"resultLimit": params.ResultLimit, "cidrSamples": params.CIDRSamples, "dc": params.DC''',
        '''"resultLimit": params.ResultLimit, "cidrSamples": params.CIDRSamples, "lossLimit": lossLimit, "dc": params.DC''',
        "后台任务记录最大丢包率",
    )

if "params.ResultLimit, params.CIDRSamples, lossLimit, params.DC" not in server:
    server = rep(
        server,
        '''params.ResultLimit, params.CIDRSamples, params.DC, params.SpeedMin''',
        '''params.ResultLimit, params.CIDRSamples, lossLimit, params.DC, params.SpeedMin''',
        "服务端传递最大丢包率",
    )

old_sig = '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, cidrSamples int, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {'''
new_sig = '''func runNSBTask(ctx context.Context, session *appSession, fileName, fileContent, outFile string, maxThreads, fallbackPort, speedTest int, speedURL string, enableTLS bool, delay int, resultLimit int, cidrSamples int, lossLimit float64, targetDC string, speedMin float64, speedLimit int, compact bool, scanMode string) {'''
if old_sig in go:
    go = go.replace(old_sig,new_sig,1); changed.append("runNSBTask接收最大丢包率")
elif new_sig not in go:
    raise SystemExit("[v4.6-loss] runNSBTask 签名不匹配")

# V4 新增的自适应网段补扫 helper 也会调用 scanNSBEntry。
# lossLimit 必须继续传入 helper；否则 helper 内引用 lossLimit 会编译报 undefined。
old_adaptive_sig = """func runNSBAdaptiveScanBatch(ctx context.Context, session *appSession, entries []nsbAdaptiveEntry, maxThreads, fallbackPort int, enableTLS bool, delay int, targetDC string, compact bool, scanMode string, label string) ([]iptestResult, bool) {"""
new_adaptive_sig = """func runNSBAdaptiveScanBatch(ctx context.Context, session *appSession, entries []nsbAdaptiveEntry, maxThreads, fallbackPort int, enableTLS bool, delay int, lossLimit float64, targetDC string, compact bool, scanMode string, label string) ([]iptestResult, bool) {"""
if old_adaptive_sig in go:
    go = go.replace(old_adaptive_sig, new_adaptive_sig, 1)
    changed.append("自适应网段补扫接收最大丢包率")
elif new_adaptive_sig not in go:
    raise SystemExit("[v4.6-loss] runNSBAdaptiveScanBatch 签名不匹配")

old_adaptive_call = "runNSBAdaptiveScanBatch(ctx, session, entries, maxThreads, fallbackPort, enableTLS, delay, targetDC, compact, scanMode,"
new_adaptive_call = "runNSBAdaptiveScanBatch(ctx, session, entries, maxThreads, fallbackPort, enableTLS, delay, lossLimit, targetDC, compact, scanMode,"
adaptive_call_count = go.count(old_adaptive_call)
if adaptive_call_count:
    go = go.replace(old_adaptive_call, new_adaptive_call)
    changed.append(f"自适应补扫传递最大丢包率 x{adaptive_call_count}")
elif new_adaptive_call not in go:
    raise SystemExit("[v4.6-loss] 找不到 runNSBAdaptiveScanBatch 调用")

old_scan_sig = '''func scanNSBEntry(ctx context.Context, item string, fallbackPort int, enableTLS bool, delay int, targetDC string, inputIndex int) (*iptestResult, *nsbFailureRecord) {'''
new_scan_sig = '''func scanNSBEntry(ctx context.Context, item string, fallbackPort int, enableTLS bool, delay int, lossLimit float64, targetDC string, inputIndex int) (*iptestResult, *nsbFailureRecord) {'''
if old_scan_sig in go:
    go=go.replace(old_scan_sig,new_scan_sig,1); changed.append("TCPing扫描接收最大丢包率")
elif new_scan_sig not in go:
    raise SystemExit("[v4.6-loss] scanNSBEntry 签名不匹配")

old_call = "scanNSBEntry(itemCtx, item, fallbackPort, enableTLS, delay, targetDC, idx)"
new_call = "scanNSBEntry(itemCtx, item, fallbackPort, enableTLS, delay, lossLimit, targetDC, idx)"
call_count=go.count(old_call)
if call_count:
    go=go.replace(old_call,new_call); changed.append(f"TCPing调用传递最大丢包率 x{call_count}")
elif new_call not in go:
    raise SystemExit("[v4.6-loss] 找不到 scanNSBEntry 调用")

loss_line='''\tlossRate := float64(nsbLatencyAttempts-successCount) / float64(nsbLatencyAttempts)
'''
loss_check='''\tlossRate := float64(nsbLatencyAttempts-successCount) / float64(nsbLatencyAttempts)
\tlossPercent := lossRate * 100
\tif lossPercent > lossLimit+1e-9 {
\t\tif firstConn != nil {
\t\t\tfirstConn.Close()
\t\t}
\t\treturn nil, &nsbFailureRecord{
\t\t\tindex: inputIndex, ipAddr: ipAddr, port: portStr, phase: "scan",
\t\t\treason: "超过丢包阈值",
\t\t\tdetail: fmt.Sprintf("loss=%.0f%%, limit=%.0f%%, attempts=%d", lossPercent, lossLimit, nsbLatencyAttempts),
\t\t}
\t}
'''
if 'reason: "超过丢包阈值"' not in go:
    go=rep(go,loss_line,loss_check,"丢包不合格立即淘汰")

if "cfg.resultLimit, 4, 100, cfg.nsbDC" not in cli:
    cli=rep(cli,"cfg.resultLimit, 4, cfg.nsbDC","cfg.resultLimit, 4, 100, cfg.nsbDC","CLI默认最大丢包率100")

INDEX.write_text(html,encoding="utf-8")
PROTOCOL.write_text(protocol,encoding="utf-8")
SERVER.write_text(server,encoding="utf-8")
TASKS.write_text(go,encoding="utf-8")
CLI.write_text(cli,encoding="utf-8")

print("[v4.6-loss] 已应用:")
for item in changed:
    print(" -",item)
