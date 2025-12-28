"""
Content Rewriter Module
使用云雾API调用 Gemini Pro 进行内容改写
支持多模型备选方案，防止超时
"""

import os
import requests
import json
import urllib3
from typing import Dict, Optional, List

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ContentRewriter:
    """内容改写器 - 使用云雾API调用 Gemini Pro，支持多模型备选"""

    # 模型优先级列表（从高到低）
    MODEL_PRIORITY = [
        "gemini-3-pro-preview-thinking",  # 最强模型，带思考
        "gemini-3-pro-preview",           # 高级模型
        "gemini-3-flash-preview",         # 快速模型
    ]

    # 每个模型的超时设置（秒）
    MODEL_TIMEOUTS = {
        "gemini-3-pro-preview-thinking": 600,  # 10分钟
        "gemini-3-pro-preview": 300,           # 5分钟
        "gemini-3-flash-preview": 180,         # 3分钟
    }

    def __init__(self, logger=None):
        self.logger = logger
        self.api_key = None
        self.api_url = None
        self.models = None
        self._load_config()

    def _load_config(self):
        """加载云雾API配置"""
        # 优先从环境变量读取
        self.api_key = os.environ.get("YUNWU_API_KEY")
        self.api_url = os.environ.get("YUNWU_API_URL")

        # 从环境变量读取模型列表（逗号分隔），或使用默认优先级列表
        models_env = os.environ.get("YUNWU_MODELS")
        if models_env:
            self.models = [m.strip() for m in models_env.split(",") if m.strip()]
        else:
            # 如果没有指定，使用默认优先级列表
            default_model = os.environ.get("YUNWU_MODEL", "gemini-3-pro-preview-thinking")
            # 将默认模型放在首位，然后添加其他模型
            self.models = [default_model]
            for model in self.MODEL_PRIORITY:
                if model != default_model:
                    self.models.append(model)

        # 如果环境变量没有，从配置文件读取
        if not self.api_key or not self.api_url:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "reference", "yunwu.txt"
            )
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == 'api_key':
                                self.api_key = value
                            elif key == 'url':
                                self.api_url = value
                            elif key == 'models':
                                self.models = [m.strip() for m in value.split(",") if m.strip()]
                            elif key == 'model':
                                # 单个模型配置
                                if not self.models or value not in self.models:
                                    self.models = [value]

        if not self.models:
            self.models = self.MODEL_PRIORITY

        if self.api_key:
            if self.logger:
                self.logger.info(f"云雾API配置加载成功: models={self.models}")
        else:
            if self.logger:
                self.logger.warning("云雾API配置未找到，将使用CLI方式")

    def rewrite(self, transcript: str, video_info: Dict, processor_result: Dict) -> str:
        """改写字幕内容，支持多模型备选

        Args:
            transcript: 原始字幕文本
            video_info: 视频配置信息
            processor_result: 处理器返回的视频元数据

        Returns:
            str: 改写后的内容
        """
        title = video_info.get("title", processor_result.get("title", "未知标题"))
        author = processor_result.get("author", processor_result.get("uploader", "未知"))
        platform = video_info.get("platform", processor_result.get("service", "unknown"))

        # 构建改写提示词
        prompt = self._build_prompt(title, author, platform, transcript)

        if self.logger:
            self.logger.info(f"开始改写: {title}")

        # 优先使用API，失败则降级到CLI
        if self.api_key and self.api_url:
            # 尝试所有模型
            last_error = None
            for i, model in enumerate(self.models):
                try:
                    if self.logger:
                        self.logger.info(f"尝试模型 {i+1}/{len(self.models)}: {model}")

                    result = self._call_yunwu_api(prompt, model)

                    if self.logger:
                        self.logger.info(f"改写完成，使用模型: {model}，输出长度: {len(result)} 字符")
                    return result

                except requests.exceptions.Timeout as e:
                    last_error = f"超时: {model}"
                    if self.logger:
                        self.logger.warning(f"模型 {model} 超时，尝试下一个模型")
                    continue

                except requests.exceptions.RequestException as e:
                    last_error = f"请求失败: {model} - {e}"
                    if self.logger:
                        self.logger.warning(f"模型 {model} 请求失败，尝试下一个模型: {e}")
                    continue

                except Exception as e:
                    last_error = f"错误: {model} - {e}"
                    if self.logger:
                        self.logger.warning(f"模型 {model} 失败，尝试下一个模型: {e}")
                    continue

            # 所有模型都失败了，尝试 CLI 方式
            if self.logger:
                self.logger.warning(f"所有模型尝试失败: {last_error}，尝试CLI方式")

            try:
                result = self._call_glm_cli(prompt)
                if self.logger:
                    self.logger.info(f"CLI改写完成，输出长度: {len(result)} 字符")
                return result
            except Exception as e2:
                error_msg = f"改写失败: API={last_error}, CLI={e2}"
                if self.logger:
                    self.logger.error(error_msg)
                return self._format_error(error_msg, transcript)
        else:
            # 使用CLI方式
            try:
                result = self._call_glm_cli(prompt)
                if self.logger:
                    self.logger.info(f"改写完成，输出长度: {len(result)} 字符")
                return result
            except Exception as e:
                error_msg = f"改写失败: {e}"
                if self.logger:
                    self.logger.error(error_msg)
                return self._format_error(error_msg, transcript)

    def _format_error(self, error_msg: str, transcript: str) -> str:
        """格式化错误信息"""
        return f"# 改写失败\n\n{error_msg}\n\n---\n\n## 原始字幕\n\n{transcript}"

    def _call_yunwu_api(self, prompt: str, model: str = None) -> str:
        """调用云雾API

        Args:
            prompt: 提示词
            model: 模型名称，如果为 None 则使用默认模型

        Returns:
            str: AI 返回的内容
        """
        if model is None:
            model = self.models[0] if self.models else self.MODEL_PRIORITY[0]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体 (OpenAI兼容格式)
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 8000
        }

        if self.logger:
            self.logger.debug(f"API请求: model={model}")

        # 根据模型获取超时设置
        timeout = self.MODEL_TIMEOUTS.get(model, 300)  # 默认 5 分钟

        response = requests.post(
            self.api_url,
            headers=headers,
            json=data,
            timeout=timeout,
            verify=False  # 禁用SSL验证（如果遇到SSL问题）
        )

        if response.status_code != 200:
            raise Exception(f"API请求失败: HTTP {response.status_code}, {response.text}")

        result = response.json()

        # 解析响应 (OpenAI兼容格式)
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            raise Exception(f"API响应格式错误: {result}")

    def _build_prompt(self, title: str, author: str, platform: str, transcript: str) -> str:
        """构建改写提示词

        Args:
            title: 视频标题
            author: 作者/UP主
            platform: 平台
            transcript: 字幕内容

        Returns:
            str: 完整的提示词
        """
        # 尝试从文件加载模板
        template_path = os.path.join(os.path.dirname(__file__), "..", "prompt-template.md")

        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # 替换变量
            return template.format(
                title=title,
                author=author,
                platform=platform,
                transcript=transcript
            )

        # 备用简化模板
        return f"""你是 AFP 逻辑架构师，负责将非结构化语料转结构化深度文稿。

# 视频信息
- 标题: {title}
- 作者: {author}
- 平台: {platform}

# 原始字幕
{transcript}

# 输出要求

## 核心金句 (3-5条)
提炼视频中具有启发性的金句，每条金句单独一行。

## 深度摘要 (2000字左右)
对视频内容进行深度梳理和总结，包括：
1. 核心观点：用简练的语言概括视频的核心观点
2. 关键概念：解释视频中的重要概念和术语
3. 详细论述：按逻辑顺序梳理视频的主要内容
4. 实践启示：总结视频的实践价值或启示

## 主题标签 (1-2个)
- 标签1
- 标签2

**标签生成原则**：
- 选择通用领域或大主题标签（如：AI、创业、产品思维、职业发展、学习方法等）
- 标签应具有跨内容的分类检索价值
- 避免过于宽泛或过于具体

# 风格要求
- 商业科技媒体风（简练、有力、逻辑严密、无废话）
- 禁止列表化堆砌内容
- 对关键概念和核心结论进行格式化：使用 **加粗** 或 <u>下划线</u> 标注
- 注意控制格式化数量：每段最多2-3处，避免过度使用影响阅读
- 使用小标题分隔不同部分
"""

    def _call_glm_cli(self, prompt: str) -> str:
        """调用 glm-4.7 CLI

        Args:
            prompt: 提示词

        Returns:
            str: AI 返回的内容
        """
        # 将提示词写入临时文件
        temp_prompt_file = "temp_prompt.txt"
        with open(temp_prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        try:
            # 调用 CLI (假设命令为 'claude' 或用户自定义的 CLI 命令)
            # 这里使用 subprocess 调用，用户可以根据实际情况修改命令
            command = self._get_cli_command(temp_prompt_file)

            if self.logger:
                self.logger.debug(f"执行命令: {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                error_msg = result.stderr or "未知错误"
                raise Exception(f"CLI 调用失败: {error_msg}")

            output = result.stdout.strip()

            if not output:
                raise Exception("CLI 返回空内容")

            return output

        except subprocess.TimeoutExpired:
            raise Exception("CLI 调用超时")
        except FileNotFoundError:
            raise Exception("未找到 CLI 命令，请检查是否正确安装")
        finally:
            # 清理临时文件
            if os.path.exists(temp_prompt_file):
                os.remove(temp_prompt_file)

    def _get_cli_command(self, prompt_file: str) -> list:
        """获取 CLI 命令

        Args:
            prompt_file: 提示词文件路径

        Returns:
            list: 命令列表
        """
        # 用户可以通过环境变量自定义 CLI 命令
        # 默认使用 'claude' 命令
        custom_cli = os.environ.get("GLM_CLI_COMMAND")

        if custom_cli:
            # 支持自定义命令，如: "python -m my_cli" 或 "my-cli --prompt-file"
            return custom_cli.split() + [prompt_file]

        # 默认命令 (根据实际情况修改)
        # 示例: 使用 claude CLI 读取文件内容
        return ["claude", "prompt", "-f", prompt_file, "--model", "glm-4.7"]

    def rewrite_with_template(
        self,
        transcript: str,
        video_info: Dict,
        processor_result: Dict,
        prompt_template: str
    ) -> str:
        """使用自定义模板改写

        Args:
            transcript: 原始字幕
            video_info: 视频配置信息
            processor_result: 处理器返回的视频元数据
            prompt_template: 自定义提示词模板

        Returns:
            str: 改写后的内容
        """
        title = video_info.get("title", processor_result.get("title", ""))
        author = processor_result.get("author", processor_result.get("uploader", ""))
        platform = video_info.get("platform", processor_result.get("service", ""))

        # 使用模板
        prompt = prompt_template.format(
            title=title,
            author=author,
            platform=platform,
            transcript=transcript
        )

        try:
            return self._call_glm_cli(prompt)
        except Exception as e:
            if self.logger:
                self.logger.error(f"模板改写失败: {e}")
            return f"# 改写失败\n\n{e}"


__all__ = ['ContentRewriter']
