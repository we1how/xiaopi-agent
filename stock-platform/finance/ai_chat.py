"""
AI聊天组件
集成Claude API，支持新闻分析和对话
"""

import streamlit as st
from typing import List, Dict, Optional
import json
from datetime import datetime


class AIChatComponent:
    """AI聊天组件"""

    def __init__(self):
        self.init_session_state()

    def init_session_state(self):
        """初始化session state"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'ai_api_key' not in st.session_state:
            st.session_state.ai_api_key = ""
        if 'ai_base_url' not in st.session_state:
            st.session_state.ai_base_url = "https://api.moonshot.cn/v1"
        if 'ai_model' not in st.session_state:
            st.session_state.ai_model = "kimi-k2.5"
        # 注意：selected_news_ids 在 finance_page.py 中统一管理

    def get_selected_news(self) -> List[Dict]:
        """从 session state 获取选中的新闻列表"""
        # 从 finance_page 的 session state 获取
        if 'selected_news_ids' not in st.session_state or 'news_list' not in st.session_state:
            return []

        selected_ids = st.session_state.selected_news_ids
        news_list = st.session_state.news_list

        return [n for n in news_list if n.get('id') in selected_ids]

    def add_message(self, role: str, content: str):
        """添加消息"""
        st.session_state.chat_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def clear_chat(self):
        """清空对话"""
        st.session_state.chat_messages = []

    def remove_news(self, news_id: str):
        """移除特定新闻 - 同时同步到 news_list 的选中状态"""
        # 从 selected_news_ids 中移除，实现双向同步
        if 'selected_news_ids' in st.session_state:
            st.session_state.selected_news_ids.discard(news_id)

    def render_config_section(self):
        """渲染配置区域 - 现代简洁风格"""
        with st.expander("🔧 API配置", expanded=not st.session_state.ai_api_key):
            col1, col2 = st.columns(2)
            with col1:
                api_key = st.text_input(
                    "API Key",
                    value=st.session_state.ai_api_key,
                    type="password",
                    placeholder="sk-...",
                    help="你的API密钥"
                )
            with col2:
                base_url = st.text_input(
                    "Base URL",
                    value=st.session_state.ai_base_url,
                    placeholder="https://api.moonshot.cn/v1",
                    help="API基础地址"
                )

            model = st.text_input(
                "模型名称",
                value=st.session_state.ai_model,
                placeholder="kimi-k2.5",
                help="使用的AI模型"
            )

            if st.button("保存配置", use_container_width=True):
                st.session_state.ai_api_key = api_key
                st.session_state.ai_base_url = base_url
                st.session_state.ai_model = model
                st.success("配置已保存！")

    def render_context_section(self):
        """渲染上下文区域（选中的新闻）- 现代简洁风格"""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 16px;">📰</span>
            <span style="font-size: 15px; font-weight: 600; color: #111827;">已选新闻</span>
        </div>
        """, unsafe_allow_html=True)

        selected_news = self.get_selected_news()

        if not selected_news:
            st.markdown("""
            <div style="background: #1E293B; border: 1px dashed #4B5563; border-radius: 8px; padding: 16px; text-align: center; color: #9CA3AF; font-size: 13px;">
                <span style="font-size: 20px; display: block; margin-bottom: 6px;">📋</span>
                请从中间栏勾选新闻<br>将自动同步到此处
            </div>
            """, unsafe_allow_html=True)
            return

        # 已选新闻卡片容器 - 金融暗黑风
        st.markdown('<div style="background: #1E293B; border: 1px solid #374151; border-radius: 8px; padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">', unsafe_allow_html=True)

        for i, news in enumerate(selected_news):
            col1, col2 = st.columns([0.88, 0.12])
            with col1:
                title = news.get('title', '无标题')
                title_short = title[:35] + "..." if len(title) > 35 else title
                st.markdown(f"""
                <div style="padding: 8px 0; {'border-bottom: 1px solid #374151;' if i < len(selected_news) - 1 else ''}">
                    <span style="font-size: 13px; font-weight: 500; color: #D1D5DB;">📄 {title_short}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✕", key=f"remove_{news.get('id')}", help="移除"):
                    self.remove_news(news.get('id'))
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # 清空按钮 - 使用更紧凑的样式
        if st.button("🗑️ 清空全部", use_container_width=True, type="secondary"):
            st.session_state.selected_news_ids.clear()
            st.rerun()

    def render_prompt_section(self, prompt_manager) -> Optional[str]:
        """渲染Prompt选择区域 - 现代简洁风格"""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 16px;">📝</span>
            <span style="font-size: 15px; font-weight: 600; color: #111827;">分析模板</span>
        </div>
        """, unsafe_allow_html=True)

        templates = prompt_manager.get_all_templates()
        template_options = {t['name']: t['id'] for t in templates}

        selected_name = st.selectbox(
            "选择分析模板",
            options=list(template_options.keys()),
            index=0,
            key="template_selector"
        )

        selected_id = template_options[selected_name]
        template = prompt_manager.get_template_by_id(selected_id)

        # 显示模板详细信息
        with st.expander("📋 查看模板详情", expanded=False):
            st.markdown(f"**模板名称**：{template.get('name', '')}")
            st.markdown(f"**功能描述**：{template.get('description', '')}")

            # 显示适用场景（如果有）
            use_case = template.get('use_case', '')
            if use_case:
                st.markdown(f"**适用场景**：{use_case}")

            # 显示模板内容预览
            st.markdown("**Prompt预览**：")
            content_preview = template.get('content', '')[:300]
            if len(template.get('content', '')) > 300:
                content_preview += "..."
            st.code(content_preview)

            # 显示示例输出（如果有）
            example_output = template.get('example_output', '')
            if example_output:
                st.markdown("**示例输出**：")
                st.code(example_output)

        # 自定义编辑
        if selected_id == "custom":
            custom_prompt = st.text_area(
                "自定义Prompt",
                value=template.get('content', '{news_content}'),
                height=150,
                key="custom_prompt_editor"
            )
            return custom_prompt
        else:
            # 渲染最终的prompt
            selected_news = self.get_selected_news()
            if selected_news:
                rendered = prompt_manager.render_prompt_with_news(
                    selected_id,
                    selected_news
                )
                with st.expander("查看完整Prompt"):
                    st.text_area("Prompt内容", value=rendered, height=200, disabled=True, key="full_prompt_preview")
                return rendered
            return None

    def call_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用AI API"""
        if not st.session_state.ai_api_key:
            return "错误：请先配置API Key"

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=st.session_state.ai_api_key,
                base_url=st.session_state.ai_base_url
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=st.session_state.ai_model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"API调用失败: {str(e)}"

    def render_chat_section(self):
        """渲染对话区域 - 现代简洁风格"""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 16px;">💬</span>
            <span style="font-size: 15px; font-weight: 600; color: #111827;">对话</span>
        </div>
        """, unsafe_allow_html=True)

        # 显示历史消息
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

        # 用户输入
        user_input = st.chat_input("输入消息...")
        if user_input:
            self.add_message("user", user_input)

            # 构建完整上下文
            context = ""
            selected_news = self.get_selected_news()
            if selected_news:
                news_text = "\n\n".join([
                    f"【新闻】{n.get('title')}\n{n.get('content', '')[:500]}"
                    for n in selected_news
                ])
                context = f"以下是参考新闻内容：\n\n{news_text}\n\n用户问题："

            full_prompt = context + user_input

            # 调用API
            with st.spinner("思考中..."):
                response = self.call_api(
                    full_prompt,
                    system_prompt="你是顶级专业金融分析师、股票专家，擅长从新闻中识别对股票的影响，对股票给出专业的分析和判断。"
                )

            self.add_message("assistant", response)
            st.rerun()

    def render_analysis_button(self, prompt: str):
        """渲染分析按钮"""
        selected_news = self.get_selected_news()

        if not selected_news:
            st.warning("请先选择要分析的新闻")
            return

        if not prompt:
            st.warning("请配置分析模板")
            return

        if st.button("🚀 开始分析", use_container_width=True, type="primary"):
            self.add_message("user", f"请分析选中的 {len(selected_news)} 条新闻")

            with st.spinner("AI分析中..."):
                response = self.call_api(
                    prompt,
                    system_prompt="你是顶级专业金融分析师、股票专家，擅长从新闻中识别对股票的影响，对股票给出专业的分析和判断。"
                )

            self.add_message("assistant", response)
            st.rerun()

    def render_export_buttons(self):
        """渲染导出按钮 - 现代简洁风格"""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 16px;">📋</span>
            <span style="font-size: 15px; font-weight: 600; color: #111827;">导出</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # 复制对话
            if st.session_state.chat_messages:
                chat_text = "\n\n".join([
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in st.session_state.chat_messages
                ])
                if st.button("📋 复制对话", use_container_width=True):
                    try:
                        import pyperclip
                        pyperclip.copy(chat_text)
                        st.success("已复制到剪贴板！")
                    except Exception as e:
                        st.error(f"复制失败: {e}")

        with col2:
            # 清空对话
            if st.session_state.chat_messages:
                if st.button("🗑️ 清空对话", use_container_width=True):
                    self.clear_chat()
                    st.rerun()

    def render(self, prompt_manager):
        """渲染完整组件 - 现代简洁风格"""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">
            <span style="font-size: 20px;">🤖</span>
            <span style="font-size: 18px; font-weight: 700; color: #111827;">AI分析助手</span>
        </div>
        """, unsafe_allow_html=True)

        # API配置
        self.render_config_section()
        st.divider()

        # 上下文（选中的新闻）
        self.render_context_section()
        st.divider()

        # Prompt选择
        selected_prompt = self.render_prompt_section(prompt_manager)

        # 分析按钮
        if selected_prompt:
            self.render_analysis_button(selected_prompt)

        st.divider()

        # 对话区域
        self.render_chat_section()

        # 导出按钮
        self.render_export_buttons()
