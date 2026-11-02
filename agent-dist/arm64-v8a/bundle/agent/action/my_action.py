import json
import time

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("click_target")
class ClickTargetAction(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        print("ClickTargetAction is running!")

        param = json.loads(argv.custom_action_param or "{}") or {}
        target = param.get("target")
        if not isinstance(target, list) or len(target) != 2:
            return False

        # 执行点击
        click_job = context.tasker.controller.post_click(target[0], target[1])
        # 等待点击完成，这一步必须有！
        click_job.wait()

        return True


@AgentServer.custom_action("click_multi_targets")
class ClickMultiTargetsAction(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:

        print("ClickMultiTargetsAction is running!")

        param = json.loads(argv.custom_action_param or "{}") or {}
        interval = float(param.get("click_interval", 300))  # 相邻两次点击间隔，毫秒

        # 从上一节点自定义识别返回的 detail 里取坐标
        reco = argv.reco_detail

        detail = None
        if reco.best_result is not None:
            detail = getattr(reco.best_result, "detail", None)
        if detail is None and reco.all_results:
            detail = getattr(reco.all_results[0], "detail", None)
        if isinstance(detail, str):
            detail = json.loads(detail)

        detail = detail or {}
        points = detail.get("points")
        if not points:
            boxes = detail.get("boxes")
            if boxes:
                points = [[x + w // 2, y + h // 2] for (x, y, w, h) in boxes]

        if not points:
            print("没有拿到坐标，前序识别未命中或 detail 中缺少 boxes/points")
            return False

        # 遍历点击所有坐标
        for point in points:
            click_job = context.tasker.controller.post_click(int(point[0]), int(point[1]))
            click_job.wait()
            if interval > 0:
                time.sleep(interval / 1000)

        print(f"共点击 {len(points)} 个坐标: {points}")
        return True
