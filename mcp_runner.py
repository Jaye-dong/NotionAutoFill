#!/usr/bin/env python3
"""
MCP Runner - delegates the entire classification workflow to the Claude CLI,
which has access to Notion via MCP tools.

Used automatically when direct Notion API access is unavailable.
"""

import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

DATABASE_ID = "59a5de8061074356904624b920c0b849"

CLASSIFICATION_RULES = """
分类规则：
- 深度工作（蓝色）：需要专注思考的工作，如写代码、调试、技术攻坚、方案设计
- 浅层工作（紫色）：必要但不需深度思考，如开会、写文档、提交代码、打包编译、回邮件
- 被动工作（黄色）：被打断或被迫做的工作，如救火、传包、处理突发
- 主动学习（橙色）：有目的的学习，如看书、刷课、做笔记
- 假装学习（黄色）：看似学习但没投入，如打开书但走神、报了课没学
- 恢复休息（绿色）：真正恢复精力，如睡觉、运动、高质量社交
- 生活必须（灰色）：日常必需，如通勤、做饭、吃饭、洗澡、家务
- 无效拖延（红色）：既没产出也没恢复，如刷手机、看无聊视频、发呆逃避
"""

PROMPT_TEMPLATE = """你需要完成 Notion 时间记录数据库的自动分类任务。数据库 URL：https://www.notion.so/{db_id}

{rules}

请按以下步骤操作：

1. 用 notion-fetch 获取数据库，确认分类字段的可选值
2. 用 notion-search 在该数据库（data_source_url = collection://ccd7f1d7-4dc7-4dff-90ad-b9785604a3e9）中搜索近期记录，重复多次不同关键词搜索（如"工作 代码 会议"、"吃饭 睡觉 运动"、"学习 休息 通勤"等），尽量找到所有分类为空的条目
3. 用 notion-fetch 逐条获取候选记录，检查其「分类」属性是否为空（properties 中没有「分类」字段，或其值为 null）
4. 对每条分类为空的记录，根据「记录」字段内容和上述规则判断分类，然后用 notion-update-page 的 update_properties 命令写入「分类」字段
5. 最后汇总：处理了哪些记录、分配了什么分类

注意：
- 只处理「分类」字段真正为空的记录，不要修改已有分类的记录
- 「未记录 @日期」这类占位条目已有「未记录」分类，跳过它们
- 每次搜索最多返回 25 条，需多轮搜索才能覆盖全部未分类记录
""".format(db_id=DATABASE_ID, rules=CLASSIFICATION_RULES)


def run():
    """Run the full classification workflow via Claude CLI + MCP."""
    logger.info("Starting MCP-based classification via claude CLI")
    print("正在通过 Claude MCP 工具执行分类任务...\n")

    result = subprocess.run(
        ["claude", "-p", PROMPT_TEMPLATE],
        capture_output=False,   # stream output directly to terminal
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error(f"claude CLI exited with code {result.returncode}")
        return False

    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    success = run()
    sys.exit(0 if success else 1)
