import json

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.pipeline import JRecognitionType, JTemplateMatch


@AgentServer.custom_recognition("find_smallest_number")
class SmallestNumberRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        param = json.loads(argv.custom_recognition_param or "{}") or {}
        rois = param.get("candidate_rois")
        if not isinstance(rois, list) or not rois:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={"error": "candidate_rois 不能为空"},
            )

        res = []

        for roi in rois:
            # 找到 pipeline 中名为 "RecognizeNumber" 的节点，并执行它的识别逻辑
            reco_detail = context.run_recognition(
                "RecognizeNumber",
                argv.image,  # 使用当前获取到的图片
                pipeline_override={  # 临时覆盖节点参数
                    "RecognizeNumber": {  # 要覆盖的节点的名称
                        "roi": roi,  # 覆盖识别区域
                        "only_rec": True,  # 不进行文本检测，直接进行识别
                    }
                },
            )

            if reco_detail is None or not reco_detail.hit:
                print(f"无法读取到内容 {roi}")
                res.append(None)
                continue

            text = str(reco_detail.best_result.text)
            try:
                number = float(text)
            except ValueError:
                print(f"{text} 不是数字!")
                res.append(None)
                continue

            res.append(number)

        if not res or None in res:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={"error": "存在无法读取到内容"},
            )

        min_index = res.index(min(res))
        return CustomRecognition.AnalyzeResult(
            box=rois[min_index],
            detail={"smallest_number": res[min_index]},
        )


@AgentServer.custom_recognition("template_multi_match")
class TemplateMultiMatchRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:

        param = json.loads(argv.custom_recognition_param or "{}") or {}
        template = param.get("template")
        if not isinstance(template, str) or not template:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={"error": "template 不能为空，需要传模板图片名，例如 icon.png"},
            )

        threshold = float(param.get("threshold", 0.8))
        order_by = str(param.get("order_by", "Score"))  # Score / Horizontal / Vertical / Random
        roi = param.get("roi")  # 可选，限制搜索区域 [x, y, w, h]

        tm_param = JTemplateMatch(
            template=[template],
            threshold=[threshold],
            order_by=order_by,
        )
        if isinstance(roi, list) and len(roi) == 4:
            tm_param.roi = roi

        # 直接对截图执行模板匹配，返回所有命中结果（不依赖预置 pipeline 节点）
        reco_detail = context.run_recognition_direct(
            JRecognitionType.TemplateMatch,
            tm_param,
            argv.image,
        )

        if reco_detail is None or not reco_detail.hit:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={"error": f"未匹配到模板 {template}"},
            )

        # 所有命中框 [x, y, w, h]（已按 order_by 排序）
        boxes = [list(r.box) for r in reco_detail.all_results]
        # 转成点击用的中心点坐标
        points = [[x + w // 2, y + h // 2] for (x, y, w, h) in boxes]

        return CustomRecognition.AnalyzeResult(
            box=boxes[0],
            detail={
                "template": template,
                "count": len(boxes),
                "boxes": boxes,
                "points": points,
            },
        )
