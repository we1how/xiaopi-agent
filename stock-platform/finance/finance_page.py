"""
Finance页面 - 财经新闻聚合与AI分析
三栏布局：RSS路由 | 新闻列表 | AI助手
"""

import streamlit as st
from typing import List, Dict
from finance.rss_manager import RSSManager
from finance.news_fetcher import NewsFetcher
from finance.prompt_templates import PromptManager
from finance.ai_chat import AIChatComponent


def on_news_checkbox_change(news_id):
    """处理新闻勾选状态变化"""
    key = f"chk_{news_id}"
    if key in st.session_state:
        if st.session_state[key]:
            st.session_state.selected_news_ids.add(news_id)
        else:
            st.session_state.selected_news_ids.discard(news_id)


def init_finance_session_state():
    """初始化Finance页面的session state"""
    if 'selected_route_id' not in st.session_state:
        st.session_state.selected_route_id = None
    if 'news_list' not in st.session_state:
        st.session_state.news_list = []
    if 'selected_news_ids' not in st.session_state:
        st.session_state.selected_news_ids = set()
    if 'show_add_route_form' not in st.session_state:
        st.session_state.show_add_route_form = False


def render_route_manager(rss_manager: RSSManager):
    """渲染左侧：RSS路由管理 - 现代简洁风格"""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">
        <span style="font-size: 20px;">📡</span>
        <span style="font-size: 18px; font-weight: 700; color: #111827;">RSS路由</span>
    </div>
    """, unsafe_allow_html=True)

    routes = rss_manager.get_all_routes()

    if not routes:
        st.markdown("""
        <div style="background: #1E293B; border: 1px dashed #4B5563; border-radius: 8px; padding: 20px; text-align: center; color: #9CA3AF;">
            <span style="font-size: 24px; display: block; margin-bottom: 8px;">📭</span>
            暂无路由，请点击下方添加
        </div>
        """, unsafe_allow_html=True)

    # 显示路由列表
    for route in routes:
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            # 路由选择按钮
            is_selected = st.session_state.selected_route_id == route.get('id')
            btn_type = "primary" if is_selected else "secondary"

            label = f"{'✅' if route.get('enabled') else '⛔'} {route.get('name', '未命名')}"

            if st.button(label, key=f"route_{route.get('id')}", use_container_width=True, type=btn_type):
                if is_selected:
                    st.session_state.selected_route_id = None
                    st.session_state.news_list = []
                else:
                    st.session_state.selected_route_id = route.get('id')
                    # 加载新闻
                    fetcher = NewsFetcher()
                    with st.spinner("加载新闻中..."):
                        st.session_state.news_list = fetcher.fetch_with_cache(route)
                st.rerun()

        with col2:
            # 启用/禁用切换
            enabled = route.get('enabled', True)
            toggle_label = "🔴" if enabled else "🟢"
            if st.button(toggle_label, key=f"toggle_{route.get('id')}", help="切换启用状态"):
                rss_manager.toggle_route(route.get('id'))
                st.rerun()

    st.divider()

    # 添加路由按钮
    if st.button("➕ 添加路由", use_container_width=True):
        st.session_state.show_add_route_form = not st.session_state.show_add_route_form
        st.rerun()

    # 添加路由表单
    if st.session_state.show_add_route_form:
        render_add_route_form(rss_manager)


def render_add_route_form(rss_manager: RSSManager):
    """渲染添加路由表单"""
    with st.container():
        st.markdown("#### 添加新路由")

        # 预设路由选择
        preset_routes = rss_manager.get_preset_routes()
        preset_options = ["自定义"] + list(preset_routes.keys())

        preset_choice = st.selectbox("选择预设或自定义", preset_options)

        if preset_choice != "自定义":
            preset = preset_routes[preset_choice]
            route_name = st.text_input("路由名称", value=preset['name'])
            route_url = st.text_input("RSS URL", value=preset.get('url', ''))
            route_parser = st.selectbox("解析器", ["generic", "cls"], index=0 if preset.get('parser') == 'generic' else 1)
            route_desc = st.text_input("描述", value=preset.get('description', preset['name']))
        else:
            route_name = st.text_input("路由名称", placeholder="例如：新浪财经")
            route_url = st.text_input("RSS URL", placeholder="http://localhost:1200/sina/column/roll")
            route_parser = st.selectbox("解析器", ["generic", "cls"], help="generic:通用RSS, cls:财联社特定格式")
            route_desc = st.text_input("描述", placeholder="简短描述该RSS源")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("测试连接", use_container_width=True):
                if route_url:
                    result = rss_manager.test_route(route_url, route_parser)
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['message'])
                else:
                    st.warning("请输入URL")

        with col2:
            if st.button("保存路由", use_container_width=True, type="primary"):
                if route_name and route_url:
                    route_id = route_name.lower().replace(" ", "_").replace("-", "_")

                    if preset_choice != "自定义" and preset_choice in preset_routes:
                        success = rss_manager.add_preset_route(preset_choice)
                    else:
                        success = rss_manager.add_route(
                            route_id=route_id,
                            name=route_name,
                            url=route_url,
                            parser=route_parser,
                            description=route_desc
                        )

                    if success:
                        st.success("路由添加成功！")
                        st.session_state.show_add_route_form = False
                        st.rerun()
                    else:
                        st.error("路由ID已存在")
                else:
                    st.warning("请填写名称和URL")


def render_news_list():
    """渲染中间：新闻列表 - 现代简洁风格"""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">
        <span style="font-size: 20px;">📰</span>
        <span style="font-size: 18px; font-weight: 700; color: #111827;">新闻列表</span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.selected_route_id:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #374151; border-radius: 8px; padding: 24px; text-align: center;">
            <span style="font-size: 32px; display: block; margin-bottom: 12px;">👈</span>
            <span style="color: #9CA3AF; font-weight: 500; font-size: 15px;">请从左侧选择一个RSS路由</span>
        </div>
        """, unsafe_allow_html=True)
        return

    if not st.session_state.news_list:
        st.markdown("""
        <div style="background: #1E293B; border: 1px solid #4B5563; border-radius: 8px; padding: 20px; text-align: center;">
            <span style="font-size: 24px; display: block; margin-bottom: 8px;">📭</span>
            <span style="color: #9CA3AF;">该路由暂无新闻内容</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # 刷新按钮
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if st.button("🔄 刷新", use_container_width=True):
            rss_manager = RSSManager()
            route = rss_manager.get_route_by_id(st.session_state.selected_route_id)
            if route:
                fetcher = NewsFetcher()
                with st.spinner("刷新中..."):
                    st.session_state.news_list = fetcher.fetch_with_cache(route, use_cache=False)
                st.rerun()

    with col2:
        # 全选/取消全选
        if st.button("☑️ 全选", use_container_width=True):
            if len(st.session_state.selected_news_ids) == len(st.session_state.news_list):
                st.session_state.selected_news_ids.clear()
            else:
                st.session_state.selected_news_ids = {n.get('id') for n in st.session_state.news_list}
            st.rerun()

    # 显示新闻数量
    st.caption(f"共 {len(st.session_state.news_list)} 条新闻")

    # 显示新闻卡片
    for news in st.session_state.news_list:
        render_news_card(news)

    # 显示已选数量提示 - 金融暗黑风格
    if len(st.session_state.selected_news_ids) > 0:
        selected_count = len(st.session_state.selected_news_ids)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
                    border: 1px solid #10B981;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-top: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">
            <span style="font-size: 18px; color: #10B981;">✓</span>
            <span style="color: #10B981; font-weight: 500;">
                已选择 {selected_count} 条新闻，已自动同步到右侧AI助手
            </span>
        </div>
        """, unsafe_allow_html=True)


def render_news_card(news: Dict):
    """渲染单个新闻卡片 - 现代简洁风格"""
    news_id = news.get('id', '')
    is_selected = news_id in st.session_state.selected_news_ids

    # 确保checkbox状态在session_state中
    chk_key = f"chk_{news_id}"
    if chk_key not in st.session_state:
        st.session_state[chk_key] = is_selected

    # 动态添加 selected 类
    card_class = "news-card selected" if is_selected else "news-card"

    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

    with st.container():
        # 顶部：复选框 + 标题行
        col1, col2 = st.columns([0.08, 0.92])

        with col1:
            def on_change_handler(nid=news_id):
                key = f"chk_{nid}"
                if st.session_state.get(key):
                    st.session_state.selected_news_ids.add(nid)
                else:
                    st.session_state.selected_news_ids.discard(nid)

            st.checkbox(
                "选择",
                value=is_selected,
                key=chk_key,
                label_visibility="collapsed",
                on_change=on_change_handler
            )

        with col2:
            # 标题样式
            title = news.get('title', '无标题')
            title_display = title[:60] + "..." if len(title) > 60 else title

            # 元信息行
            pub_date = news.get('pub_date', '')
            source = news.get('source', '未知')

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 15px; font-weight: 600; color: #F9FAFB; line-height: 1.5;">{title_display}</span>
            </div>
            <div style="font-size: 12px; color: #9CA3AF; display: flex; gap: 12px; align-items: center;">
                <span>📅 {pub_date}</span>
                <span>📢 {source}</span>
            </div>
            """, unsafe_allow_html=True)

            # 展开详情
            with st.expander("查看详情"):
                st.markdown(f"**{title}**")
                st.markdown(f"<span style='color: #9CA3AF;'>来源：{source} · {pub_date}</span>", unsafe_allow_html=True)
                if news.get('author'):
                    st.markdown(f"<span style='color: #9CA3AF;'>作者：{news.get('author')}</span>", unsafe_allow_html=True)

                st.divider()

                # 正文内容
                content = news.get('content', '')
                st.markdown(content if content else "*暂无内容*")

                # 原文链接
                if news.get('link'):
                    st.markdown(f"[🔗 查看原文]({news.get('link')})")

    st.markdown('</div>', unsafe_allow_html=True)


def render_finance_page():
    """渲染Finance页面"""
    st.markdown("## 📊 Finance - 财经资讯与AI分析")

    # 全局CSS：专业金融风格（支持暗黑模式）
    st.markdown("""
    <style>
    /* ===== 金融风格配色 - 自动适配暗黑/亮色模式 ===== */
    :root {
        /* 金融专业色 */
        --finance-gold: #D4AF37;
        --finance-gold-light: #F4E4A6;
        --finance-green: #059669;
        --finance-green-light: #34D399;
        --finance-red: #DC2626;
        --finance-blue: #1E40AF;
        --finance-blue-light: #3B82F6;
    }

    /* 亮色模式 */
    @media (prefers-color-scheme: light) {
        :root {
            --bg-primary: #FAFBFC;
            --bg-secondary: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-hover: #F3F4F6;
            --border-color: #E5E7EB;
            --border-strong: #D1D5DB;
            --text-primary: #111827;
            --text-secondary: #4B5563;
            --text-muted: #6B7280;
            --accent-primary: #1E40AF;
            --accent-secondary: #D4AF37;
        }
    }

    /* 暗黑模式 */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-card: #1E293B;
            --bg-hover: #334155;
            --border-color: #334155;
            --border-strong: #475569;
            --text-primary: #F1F5F9;
            --text-secondary: #CBD5E1;
            --text-muted: #94A3B8;
            --accent-primary: #60A5FA;
            --accent-secondary: #FCD34D;
        }
    }

    /* 强制使用深色主题（金融专业风格） */
    :root {
        --bg-primary: #0B1120;
        --bg-secondary: #111827;
        --bg-card: #1E293B;
        --bg-hover: #374151;
        --border-color: #374151;
        --border-strong: #4B5563;
        --text-primary: #F9FAFB;
        --text-secondary: #D1D5DB;
        --text-muted: #9CA3AF;
        --accent-primary: #3B82F6;
        --accent-secondary: #D4AF37;
        --accent-green: #10B981;
        --accent-red: #EF4444;
    }

    /* 全局背景 */
    .stApp {
        background: linear-gradient(180deg, #0B1120 0%, #111827 100%) !important;
    }

    /* 三栏独立滚动 */
    [data-testid="stColumn"] {
        max-height: calc(100vh - 100px) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-right: 12px !important;
        background: transparent !important;
    }

    /* 自定义滚动条 - 金融暗黑风格 */
    [data-testid="stColumn"]::-webkit-scrollbar {
        width: 6px;
    }
    [data-testid="stColumn"]::-webkit-scrollbar-track {
        background: #1F2937;
        border-radius: 3px;
    }
    [data-testid="stColumn"]::-webkit-scrollbar-thumb {
        background: #4B5563;
        border-radius: 3px;
    }
    [data-testid="stColumn"]::-webkit-scrollbar-thumb:hover {
        background: #6B7280;
    }

    /* 隐藏Streamlit默认的main区域滚动 */
    .main .block-container {
        max-height: none !important;
        overflow-y: visible !important;
        background: transparent !important;
    }

    /* ===== 区块标题样式 - 金融风 ===== */
    h3, h2 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        border-bottom: 2px solid var(--accent-secondary) !important;
        padding-bottom: 8px !important;
        text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
    }

    /* ===== 路由按钮样式 - 金融风 ===== */
    div[data-testid="stButton"] > button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        padding: 10px 16px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        border-color: var(--accent-primary) !important;
        background: var(--bg-hover) !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3) !important;
    }

    /* Primary 按钮 - 金色金融风 */
    div[data-testid="stButton"] > button[kind="primary"] {
        border-radius: 8px !important;
        background: linear-gradient(135deg, var(--accent-secondary) 0%, #B8860B 100%) !important;
        border: none !important;
        color: #0B1120 !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(212, 175, 55, 0.5) !important;
    }

    /* ===== 新闻卡片样式 - 金融暗黑风 ===== */
    .news-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .news-card:hover {
        border-color: var(--border-strong);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transform: translateY(-1px);
    }
    .news-card.selected {
        border-color: var(--accent-secondary);
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(30, 64, 175, 0.1) 100%);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
    }
    .news-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.5;
        margin-bottom: 8px;
    }
    .news-meta {
        font-size: 12px;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* ===== 输入框样式 ===== */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* ===== Expander 样式 ===== */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ===== 选中提示样式 - 金融风 ===== */
    .selected-info {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid var(--accent-green);
        border-radius: 8px;
        padding: 12px 16px;
        color: var(--accent-green);
        font-weight: 500;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }

    /* ===== 标签和徽章 ===== */
    .finance-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .badge-gold {
        background: rgba(212, 175, 55, 0.15);
        color: var(--accent-secondary);
        border: 1px solid rgba(212, 175, 55, 0.3);
    }
    .badge-green {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-red {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* ===== 分隔线 ===== */
    hr {
        border-color: var(--border-color) !important;
        opacity: 0.5;
    }

    /* ===== Checkbox 样式 ===== */
    .stCheckbox label {
        color: var(--text-secondary) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    init_finance_session_state()

    # 初始化管理器
    rss_manager = RSSManager()
    prompt_manager = PromptManager()
    ai_chat = AIChatComponent()

    # 三栏布局 - 每栏使用独立滚动
    left_col, mid_col, right_col = st.columns([1, 2, 2])

    with left_col:
        render_route_manager(rss_manager)

    with mid_col:
        render_news_list()

    with right_col:
        ai_chat.render(prompt_manager)


if __name__ == "__main__":
    # 测试用
    st.set_page_config(page_title="Finance", layout="wide")
    render_finance_page()
