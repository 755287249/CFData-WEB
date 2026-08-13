#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "combined_refactor" / "index.html"
TASKS = ROOT / "combined_refactor" / "tasks_nsb.go"

html = INDEX.read_text(encoding="utf-8")
go = TASKS.read_text(encoding="utf-8")
changed = []

# 1) 参数语义：
# nsbResultLimit = 延迟合格数量
# nsbSpeedLimit  = 测速合格数量

html2, n = re.subn(
    r'<span class="label" title="[^"]*">🎯 扫描合格数量</span>',
    '<span class="label" title="通过扫描合格延迟、丢包、数据中心等条件后，最终希望保留的 IP 数量；网段模式会自动随机补足到这个延迟合格目标">🎯 延迟合格数量</span>',
    html,
    count=1,
)
if n != 1:
    raise SystemExit(f"[speed-target-fix] 找不到“扫描合格数量”标签，匹配数={n}")
html = html2
changed.append("扫描合格数量重命名为延迟合格数量")

html = html.replace(
    "showNoticeCard('扫描合格数量必须填写非 0 正整数');",
    "showNoticeCard('延迟合格数量必须填写非 0 正整数');",
    1,
)

html2, n = re.subn(
    r'<span class="label" title="[^"]*">🏁 测速结果数量</span>',
    '<span class="label" title="最终希望达到“测试合格速度”的结果数量；程序会从延迟合格池继续测试后续 IP，直到凑够此数量或候选耗尽">🏁 测速合格数量</span>',
    html,
    count=1,
)
if n != 1:
    raise SystemExit(f"[speed-target-fix] 找不到“测速结果数量”标签，匹配数={n}")
html = html2
changed.append("测速结果数量重命名为测速合格数量")

html2, n = re.subn(
    r'(<input id="nsbSpeedLimit" type="number" value=")[^"]*(" placeholder=")[^"]*(">)',
    r'\g<1>10\g<2>默认 10；0 关闭测速\g<3>',
    html,
    count=1,
)
if n != 1:
    raise SystemExit(f"[speed-target-fix] 找不到 nsbSpeedLimit 输入框，匹配数={n}")
html = html2
changed.append("测速合格数量默认10")

html = html.replace(
    "            nsbSpeedEnabledForResults = speedTest > 0;\n",
    "            nsbSpeedEnabledForResults = speedTest > 0 && (parseInt(document.getElementById('nsbSpeedLimit').value) || 0) > 0;\n",
    1,
)
changed.append("测速启用状态重新受测速合格数量控制")

# 2) V4 网段逻辑只负责生成 resultLimit 个延迟合格 IP；
# 测速交回标准 runNSBSpeedWorkers，目标数 = speedLimit。

start_marker = "\t\t\t// 第二阶段：自动测速开启时，测试合格速度成为网段内的替换门槛。\n"
end_marker = "\n\tif wasCanceled || ctx.Err() != nil {"

start = go.find(start_marker)
if start < 0:
    raise SystemExit("[speed-target-fix] 找不到 V4 智能测速开始标记")
end = go.find(end_marker, start)
if end < 0:
    raise SystemExit("[speed-target-fix] 找不到 V4 智能测速结束标记")

replacement = """\t\t\t// 第二阶段改为独立测速：
\t\t\t// 此处只整理 resultLimit 个“延迟合格 IP”。
\t\t\t// 后面的标准非标测速流程再以 speedLimit（测速合格数量）为目标，
\t\t\t// 测速失败或低于 speedMin 时会继续测试下一个延迟合格 IP。
\t\t\tfinalResults := append([]iptestResult(nil), nonCIDR...)
\t\t\tfor groupIndex := range groupPools {
\t\t\t\tquota := targets[groupIndex]
\t\t\t\tsortNSBLatencyPool(groupPools[groupIndex])
\t\t\t\tif len(groupPools[groupIndex]) > quota {
\t\t\t\t\tgroupPools[groupIndex] = groupPools[groupIndex][:quota]
\t\t\t\t}
\t\t\t\tfinalResults = append(finalResults, groupPools[groupIndex]...)
\t\t\t}
\t\t\tnsbResults = finalResults
\t\t\tsession.sendWSMessage("log", fmt.Sprintf("网段延迟筛选完成：最终得到 %d/%d 个延迟合格IP；测速阶段将单独以测速合格数量=%d 为目标", len(nsbResults), resultLimit, speedLimit))
\t\t}
\t}
"""

go = go[:start] + replacement + go[end:]
changed.append("网段扫描目标与测速目标彻底分离")

go = go.replace(
    '"网段V4：扫描合格数量=%d 作为最终具体IP目标；首轮每网段随机=%d；首轮CIDR合格=%d，存活网段=%d，目标CIDR名额=%d"',
    '"网段V4：延迟合格数量=%d；首轮每网段随机=%d；首轮CIDR合格=%d，存活网段=%d，目标CIDR名额=%d"',
    1,
)
go = go.replace(
    '"延迟结果上限必须是非 0 正整数"',
    '"延迟合格数量必须是非 0 正整数"',
    1,
)
go = go.replace(
    '"开始测速：%d 条记录，线程数=%d，目标上限=%d，测速阈值=%.2fMB/s"',
    '"开始测速：延迟合格池=%d 条，线程数=%d，测速合格目标=%d，测速阈值=%.2fMB/s"',
    1,
)

if "&& !smartCIDRSpeedDone" not in go:
    raise SystemExit("[speed-target-fix] 标准测速流程缺少 smartCIDRSpeedDone 保护")
if "runNSBSpeedWorkers(ctx, nsbResults, speedTest, speedLimit, speedMin" not in go:
    raise SystemExit("[speed-target-fix] 找不到以 speedLimit 为目标的标准非标测速流程")

INDEX.write_text(html, encoding="utf-8")
TASKS.write_text(go, encoding="utf-8")

print("[speed-target-fix] 已应用:")
for item in changed:
    print(" -", item)
