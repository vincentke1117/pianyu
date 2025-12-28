"""
Transcript Rewriter Module
使用Claude API将字幕改写成结构化文档
"""

import os
import re
from typing import Dict, Optional


class TranscriptRewriter:
    """字幕内容改写器"""

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            print("警告: 未设置ANTHROPIC_API_KEY环境变量，改写功能将不可用")

        self.max_transcript_length = 50000  # 限制字幕长度避免超限
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 4000
        self.temperature = 0.7

    def rewrite(
        self,
        transcript: str,
        video_info: Dict,
        channel_info: Dict,
        prompt_template: str
    ) -> str:
        """改写字幕内容

        Args:
            transcript: 原始字幕文本
            video_info: 视频信息
            channel_info: 频道信息
            prompt_template: Prompt模板

        Returns:
            str: 改写后的内容
        """
        if not self.api_key:
            return "_错误: 未配置Claude API密钥_"

        # 限制字幕长度
        if len(transcript) > self.max_transcript_length:
            print(f"警告: 字幕长度超过限制({len(transcript)}字符)，已截断")
            transcript = transcript[:self.max_transcript_length] + "..."

        # 格式化时长
        duration_formatted = self._format_duration(video_info['duration'])

        # 构建完整prompt
        full_prompt = prompt_template.format(
            title=video_info['title'],
            duration=duration_formatted,
            channel_name=channel_info['name'],
            publish_date=video_info['published_at'],
            platform=video_info.get('platform', 'unknown'),
            transcript=transcript
        )

        try:
            return self._call_claude_api(full_prompt)

        except Exception as e:
            print(f"Claude API调用失败: {e}")
            return "_AI改写失败，请参考原始字幕_"

    def _call_claude_api(self, prompt: str) -> str:
        """调用Claude API

        Args:
            prompt: 完整的prompt文本

        Returns:
            str: API响应内容
        """
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text.strip()

        except anthropic.AuthenticationError:
            raise Exception("Claude API认证失败 - 请检查ANTHROPIC_API_KEY")
        except anthropic.RateLimitError:
            raise Exception("Claude API限流，请稍后再试")
        except anthropic.APIError as e:
            raise Exception(f"Claude API错误: {str(e)}")
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def _format_duration(self, seconds: int) -> str:
        """将秒数格式化为HH:MM:SS

        Args:
            seconds: 秒数

        Returns:
            str: 格式化后的时长
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def optimize_prompt(self, transcript: str, target_length: int = 3000) -> str:
        """优化prompt长度，确保在token限制内

        Args:
            transcript: 原始字幕
            target_length: 目标prompt长度

        Returns:
            str: 优化后的字幕
        """
        if len(transcript) <= target_length:
            return transcript

        # 简单的截断策略：保留开头和结尾
        keep_ratio = target_length / len(transcript)
        head_length = int(target_length * 0.6)
        tail_length = int(target_length * 0.4)

        head = transcript[:head_length]
        tail = transcript[-tail_length:]

        return f"{head}\n\n... [省略 {len(transcript) - target_length} 字符] ...\n\n{tail}"

    def extract_key_points(self, transcript: str, num_points: int = 5) -> list:
        """从字幕中提取关键点

        Args:
            transcript: 字幕文本
            num_points: 关键点数量

        Returns:
            list: 关键点列表
        """
        # 简单的启发式方法
        lines = transcript.split('\n')
        key_points = []

        for i, line in enumerate(lines):
            # 查找数字列表（可能表示要点）
            if re.match(r'^\d+\.\s', line.strip()):
                key_points.append(line.strip())

            # 查找冒号开头的句子
            if line.strip().startswith(('要点:', '重点:', '关键:', '核心:')):
                key_points.append(line.strip())

            # 限制数量
            if len(key_points) >= num_points:
                break

        return key_points[:num_points]


class PromptOptimizer:
    """Prompt优化器，根据内容动态调整prompt"""

    def __init__(self, base_template: str):
        self.base_template = base_template

    def optimize_for_length(self, transcript_length: int) -> str:
        """根据字幕长度优化prompt

        Args:
            transcript_length: 字幕长度

        Returns:
            str: 优化后的prompt模板
        """
        if transcript_length < 10000:
            # 短视频，可以详细处理
            return self.base_template

        elif transcript_length < 30000:
            # 中等长度
            return self.base_template.replace(
                "详细解释",
                "简要解释"
            )

        else:
            # 长视频，需要更精简
            return self.base_template.replace(
                "将以下视频信息改写成一篇结构清晰、易于理解的文章",
                "将以下视频信息改写成一篇简洁的摘要"
            )

    def optimize_for_type(self, video_type: str):
        """根据视频类型优化prompt

        Args:
            video_type: 视频类型（interview/tutorial/news/etc）

        Returns:
            str: 优化后的prompt模板
        """
        type_prompts = {
            "interview": "这是一段访谈内容，请整理成问答形式",
            "tutorial": "这是一段教程内容，请按步骤整理",
            "news": "这是一段新闻内容，请整理成新闻稿格式",
            "meeting": "这是一段会议内容，请整理成会议纪要",
        }

        type_desc = type_prompts.get(video_type, "这是一个视频内容")

        return self.base_template.replace(
            "这是一段视频内容",
            type_desc
        )


if __name__ == "__main__":
    # 简单测试
    import os
    import sys

    # 设置API密钥
    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    rewriter = TranscriptRewriter()

    # 测试数据
    video_info = {
        'id': 'test123',
        'title': '测试视频',
        'duration': 3600,
        'published_at': '2024-01-15',
        'platform': 'youtube',
    }

    channel_info = {
        'name': '测试频道'
    }

    prompt = """
    请总结以下内容：

    视频信息：
    标题: {title}
    频道: {channel_name}

    内容：
    {transcript}
    """

    transcript = "这是一段测试字幕内容。"

    try:
        result = rewriter.rewrite(transcript, video_info, channel_info, prompt)
        print("改写结果:", result[:100] + "...")
    except Exception as e:
        print(f"错误: {e}")
