#!/usr/bin/env python3
"""把 MaaFwApp 子模块的默认更新源从 MirrorChyan 改为 GitHub（幂等补丁）。

为什么需要它
-----------
MAA-hunDang 只通过 GitHub Release 发版（assets/interface.json 顶层 github 字段已配），
而 MaaFwApp 上游代码把默认更新源与非法值回落都写死为 MIRRORCHYAN，且没有任何
"未配置 Mirror 酱 rid 时自动落 GitHub" 的兜底。不 patch 的话，全新安装的 APK
启动自检会命中 MISSING_CONFIGURATION（"更新源配置缺失"），用户必须手动在首页
更新卡片点一下 GitHub 才能用；patch 后开箱即用 GitHub 更新。

为什么打补丁而不是改子模块指针
------------------------------
MaaFwApp 是上游 Aliothmoon/MaaFwApp 的只读子模块（MAA-hunDang 锁定提交 7e2dc7d）。
直接改子模块代码会产生一个上游不存在的提交，CI checkout submodules 时会因
"找不到该提交" 直接失败；改 .gitmodules 指向 fork 则需要在 GitHub 上维护一个
fork。折衷方案：CI 在全新 checkout 后跑本脚本打一次补丁，本地构建同样跑一次。
子模块指针保持 7e2dc7d 不变，工作树内的改动不会进入父仓库提交。

注意
----
- 在 MAA-hunDang 仓库根目录执行：python tools/patch_maafw_update_source.py
- 幂等：文件已是 GITHUB 时跳过，可重复执行。
- 期望字符串缺失时直接非零退出，让 CI 立即红掉而不是悄悄失效
  （上游子模块结构变化时需人工更新本脚本）。
- 若之后执行 `git submodule update` / `git checkout .` 会把本地补丁还原，
  重新跑一次本脚本即可。
"""

from pathlib import Path
import sys

APP_SETTINGS = Path(
    "Android/MaaFwApp/app/src/main/java/com/aliothmoon/maafw/settings/AppSettings.kt"
)
APP_SETTINGS_MANAGER = Path(
    "Android/MaaFwApp/app/src/main/java/com/aliothmoon/maafw/settings/AppSettingsManager.kt"
)

OLD_DEFAULT = b'val updateSource: String = "MIRRORCHYAN",'
NEW_DEFAULT = b'val updateSource: String = "GITHUB",'
OLD_FALLBACK = b"getOrDefault(UpdateSource.MIRRORCHYAN)"
NEW_FALLBACK = b"getOrDefault(UpdateSource.GITHUB)"


def patch_file(path: Path, old: bytes, new: bytes) -> bool:
    if not path.is_file():
        raise SystemExit(f"[fail] {path}: file not found，请在 MAA-hunDang 仓库根目录执行")
    data = path.read_bytes()
    if new in data:
        print(f"[skip] {path}: 已是 GITHUB 默认，无需改动")
        return False
    if old not in data:
        raise SystemExit(
            f"[fail] {path}: 找不到目标片段\n    {old.decode()}\n"
            "MaaFwApp 子模块结构可能已变化，请人工确认后更新本脚本"
        )
    path.write_bytes(data.replace(old, new))
    print(f"[patch] {path}: {old.decode()} -> {new.decode()}")
    return True


def main() -> int:
    changed = 0
    changed += patch_file(APP_SETTINGS, OLD_DEFAULT, NEW_DEFAULT)
    changed += patch_file(APP_SETTINGS_MANAGER, OLD_FALLBACK, NEW_FALLBACK)
    if changed:
        print("完成：MaaFwApp 默认更新源已改为 GitHub")
    else:
        print("完成：无需改动，默认更新源已是 GitHub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
