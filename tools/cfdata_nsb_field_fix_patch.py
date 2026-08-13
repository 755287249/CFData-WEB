#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "combined_refactor" / "utils.go"
TASKS = ROOT / "combined_refactor" / "tasks_nsb.go"

utils = UTILS.read_text(encoding="utf-8")
tasks = TASKS.read_text(encoding="utf-8")
changed = []

if "func getRandomNSBIPsFromCIDR(" not in utils:
    anchor = "// parseNSBCIDRLine turns a CIDR-only input line into concrete random IP endpoints.\n"
    if anchor not in utils:
        raise SystemExit("[field-fix] utils.go 找不到 parseNSBCIDRLine 锚点")
    helper = r'''func getRandomNSBIPsFromCIDR(cidr string, samples int) []string {
	if samples <= 0 {
		samples = defaultNSBCIDRSamplesPerPrefix
	}
	if samples > 256 {
		samples = 256
	}

	_, ipNet, err := net.ParseCIDR(strings.TrimSpace(cidr))
	if err != nil || ipNet == nil {
		return nil
	}

	ones, bits := ipNet.Mask.Size()
	hostBits := bits - ones
	maxUnique := samples
	if hostBits >= 0 && hostBits < 20 {
		available := 1 << uint(hostBits)
		if available < maxUnique {
			maxUnique = available
		}
	}
	if maxUnique <= 0 {
		return nil
	}

	seen := make(map[string]struct{}, maxUnique)
	result := make([]string, 0, maxUnique)
	maxAttempts := maxUnique*64 + 256

	for attempts := 0; len(result) < maxUnique && attempts < maxAttempts; attempts++ {
		ip, ok := randomIPFromCIDR(cidr)
		if !ok {
			break
		}

		parsed := net.ParseIP(ip)
		if parsed == nil {
			continue
		}

		// IPv4 大网段随机时避开常见的 .0 / .255，
		// 减少抽到传统网络/广播尾号造成的无效探针。
		if v4 := parsed.To4(); v4 != nil && hostBits >= 8 {
			if v4[3] == 0 || v4[3] == 255 {
				continue
			}
		}

		if _, exists := seen[ip]; exists {
			continue
		}
		seen[ip] = struct{}{}
		result = append(result, ip)
	}
	return result
}

'''
    utils = utils.replace(anchor, helper + anchor, 1)
    changed.append("新增非标CIDR整段随机函数")

old = '''	var ips []string
	if ipNet.IP.To4() != nil {
		ips = getRandomIPv4sN([]string{cidr}, nsbCIDRSamplesPerPrefix)
	} else {
		ips = getRandomIPv6sN([]string{cidr}, nsbCIDRSamplesPerPrefix)
	}
'''
new = '''	// 非标模式按“用户输入的一行 CIDR = 一个字段”处理。
	// 直接从整个 CIDR 抽样，不再隐式拆 /24 或 /48。
	ips := getRandomNSBIPsFromCIDR(cidr, nsbCIDRSamplesPerPrefix)
'''
if old in utils:
    utils = utils.replace(old, new, 1)
    changed.append("非标解析改为每输入CIDR一个字段")
elif "ips := getRandomNSBIPsFromCIDR(cidr, nsbCIDRSamplesPerPrefix)" not in utils:
    raise SystemExit("[field-fix] utils.go 找不到旧的非标 CIDR 抽样逻辑")

old = '''			var cidrs []string
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
'''
new = '''			// 非标智能模式不再隐式拆成 /24 或 /48：
			// 用户输入的一行 CIDR 就是一个独立字段/配额组。
			leaf := prefix.Masked()
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
'''
if old in tasks:
    tasks = tasks.replace(old, new, 1)
    changed.append("智能配额改为每输入CIDR一个字段")
elif "用户输入的一行 CIDR 就是一个独立字段/配额组" not in tasks:
    raise SystemExit("[field-fix] tasks_nsb.go 找不到 CIDR group 拆分逻辑")

UTILS.write_text(utils, encoding="utf-8")
TASKS.write_text(tasks, encoding="utf-8")

print("[field-fix] 已应用:")
for item in changed:
    print(" -", item)
