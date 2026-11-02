import json
from datetime import datetime
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction

# MaaFramework 默认在项目根目录输出 debug 目录：
# debug/maafw.log、debug/maafw.bak.*.log、debug/custom/、debug/on_error/、debug/vision/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEBUG_DIR = PROJECT_ROOT / "debug"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}


def cleanup_maafw_bak_logs(keep_count: int) -> datetime | None:
    """清理旧的 maafw.bak.*.log 文件，保留最新的 keep_count 个。

    返回保留日志中最旧一份的修改时间，作为后续日志/图片清理的基准；
    无法确定时返回 None，调用方应跳过后续清理。
    """
    log_files = list(DEBUG_DIR.glob("maafw.bak.*.log"))
    if not log_files:
        print("[日志清理] 未找到备份日志,跳过")
        return None

    logs_with_time = []
    for log_path in log_files:
        try:
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
        except OSError as e:
            print(f"[日志清理] 读取日志时间失败,跳过: {log_path.name}: {e}")
            return None
        logs_with_time.append((mtime, log_path))

    logs_with_time.sort(key=lambda x: x[0], reverse=True)
    to_delete = logs_with_time[keep_count:]

    if not to_delete:
        print("[日志清理] 没有需要删除的旧日志")
        return None

    deleted = 0
    for _mtime, log_path in to_delete:
        try:
            log_path.unlink()
            deleted += 1
            print(f"[日志清理] 已删除: {log_path.name}")
        except Exception as e:
            print(f"[日志清理] 删除失败 {log_path.name}: {e}")

    if deleted == 0:
        return None

    retained = logs_with_time[:keep_count]
    oldest_time = retained[-1][0]
    print(f"[日志清理] 保留 {len(retained)} 个,最旧日志时间: {oldest_time}")
    return oldest_time


def clean_files_older_than(directory: Path, base_time: datetime, extensions: set) -> None:
    """删除 directory 下修改时间早于 base_time 且后缀在 extensions 中的文件"""
    if not directory.exists():
        return
    for f in directory.iterdir():
        if not f.is_file() or f.suffix.lower() not in extensions:
            continue
        try:
            if datetime.fromtimestamp(f.stat().st_mtime) < base_time:
                f.unlink()
                print(f"[日志清理] 已删除: {f.name}")
        except OSError as e:
            print(f"[日志清理] 删除失败 {f.name}: {e}")


@AgentServer.custom_action("CleanupAgentDebug")
class CleanupAgentDebug(CustomAction):
    """清理 maafw 备份日志,以及 debug/custom、on_error、vision 下的日志和截图"""

    def run(self, context, argv):
        keep_count = 3
        if argv.custom_action_param:
            try:
                param = json.loads(argv.custom_action_param)
                count_val = param.get("save_log_count", "")
                if count_val and str(count_val).isdigit():
                    keep_count = max(int(count_val), 1)
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

        if not DEBUG_DIR.exists():
            print("[日志清理] debug 目录不存在,跳过")
            return CustomAction.RunResult(success=True)

        try:
            cutoff = cleanup_maafw_bak_logs(keep_count)
            if cutoff is None:
                print("[日志清理] 无法确定最旧日志,跳过日志/图片清理")
                return CustomAction.RunResult(success=True)
            clean_files_older_than(DEBUG_DIR / "custom", cutoff, IMAGE_EXTENSIONS | {".log"})
            clean_files_older_than(DEBUG_DIR / "on_error", cutoff, IMAGE_EXTENSIONS)
            clean_files_older_than(DEBUG_DIR / "vision", cutoff, IMAGE_EXTENSIONS)
            return CustomAction.RunResult(success=True)
        except Exception as e:
            print(f"[日志清理] 执行异常: {e}")
            return CustomAction.RunResult(success=False)
