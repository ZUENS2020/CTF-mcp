---
name: ctf-crypto
description: Crypto 题专项方法。用于经典密码、RSA/ECC、PRNG、格攻击与协议误用类题目，并要求在 CTF-mcp 项目中仅通过远端 Kali API 执行分析和求解脚本。
---

# Crypto 解题（项目版）

## 执行约束

1. 所有求解脚本在远端 Kali 运行。
2. 本地不执行解密、爆破、数学求解脚本。
3. 优先产出可复现 solver，不只给理论说明。

## 工具准备（远端执行）

```bash
apt-get update && apt-get install -y python3 python3-pip
python3 -m pip install --upgrade pycryptodome sympy gmpy2
```

## 标准流程

1. 识别模型：分组/流密码、非对称、签名、随机数。
2. 寻找误用：nonce 重用、参数弱化、泄露位、可预测随机性。
3. 建立攻击：推导可计算路径并脚本化。
4. 验证输出：明文/密钥/flag 候选一致性检查。

## 常见分支

1. RSA：共模、低指数量、CRT、Wiener、泄露位恢复。
2. 对称：模式误用、填充 Oracle、流复用。
3. PRNG：状态恢复与预测。
4. 混合题：先还原协议再落地解密链路。

## 内置参考

1. `classic-ciphers.md`
2. `rsa-attacks.md`
3. `modern-ciphers.md`
4. `prng-attacks.md`
5. `advanced-math.md`
