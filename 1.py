import streamlit as st
from openai import OpenAI
import time
from datetime import datetime
import re

# ===================== 1. 自定义配置 =====================
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"  # 可选moonshot-v1-32k/moonshot-v1-128k

PROMPT_TEMPLATES = {
    "故事生成": {
        "template": "请以{主题}为核心，写一个{风格}风格的短篇故事，字数控制在{字数}字左右。要求情节完整，角色鲜明，语言流畅。",
        "params": ["主题", "风格", "字数"]
    },
    "营销文案": {
        "template": "为{产品名称}撰写{平台}平台的营销文案，突出{核心卖点}，语言风格{风格}，字数控制在{字数}字内。需吸引目标用户，激发购买欲。",
        "params": ["产品名称", "平台", "核心卖点", "风格", "字数"]
    },
    "论文提纲": {
        "template": "为《{论文题目}》（{学科}领域）设计详细提纲，逻辑清晰，结构完整，至少包含{章节数}个章节。需列出每个章节的核心研究内容和逻辑关联。",
        "params": ["论文题目", "学科", "章节数"]
    },
    "自由创作": {
        "template": "{用户输入}",
        "params": ["用户输入"]
    }
}


# ===================== 2. AI 生成核心函数 =====================
def generate_content(kimi_api_key, template_type):
    if not kimi_api_key or not str(kimi_api_key).strip().startswith("sk-"):
        return "❌ 请输入有效的 Kimi API 密钥（以 sk- 开头）！"

    try:
        client = OpenAI(
            api_key=kimi_api_key.strip(),
            base_url=KIMI_BASE_URL
        )
    except Exception as e:
        return f"❌ 客户端初始化失败：{str(e)}"

    try:
        template_info = PROMPT_TEMPLATES[template_type]
        template = template_info["template"]
        required_params = template_info["params"]
    except KeyError:
        return "❌ 模板类型错误，无此生成模板！"

    param_dict = {}
    for param in required_params:
        param_dict[param] = st.session_state.get(param, "")

    invalid_or_missing = []
    for param in required_params:
        value = param_dict.get(param, "")
        if param in ["字数", "章节数"]:
            try:
                num_value = int(value) if value else 0
                if num_value <= 0:
                    invalid_or_missing.append(param)
            except (ValueError, TypeError):
                invalid_or_missing.append(param)
        else:
            if not str(value).strip():
                invalid_or_missing.append(param)

    if invalid_or_missing:
        return f"❌ 缺少或无效参数：{', '.join(invalid_or_missing)}（请填写有效且非空的内容）"

    try:
        prompt = template.format(**param_dict)
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content
    except Exception as e:
        error_info = str(e)
        if "invalid api key" in error_info.lower():
            return "❌ Kimi API密钥无效或已过期！"
        elif "insufficient funds" in error_info.lower():
            return "❌ Kimi账户余额不足，请充值！"
        elif "rate limit" in error_info.lower():
            return "❌ 请求频率过高，请稍后再试！"
        else:
            return f"❌ 生成失败：{error_info}"


# ===================== 3. 辅助函数 =====================
def copy_to_clipboard(text):
    """复制文本到剪贴板（修复版）"""
    # 使用Streamlit的原生复制功能
    st.write(f"""
        <script>
        navigator.clipboard.writeText(`{text.replace('`', '\\`')}`).then(() => {{
            alert('✅ 内容已复制到剪贴板！');
        }}).catch(err => {{
            alert('❌ 复制失败：' + err);
        }});
        </script>
    """, unsafe_allow_html=True)
    st.toast("✅ 内容已复制到剪贴板！", icon="📋")


def download_content(text, template_type):
    """下载生成的内容为txt文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{template_type}_{timestamp}.txt"
    # 确保文本编码正确
    text = text.encode('utf-8').decode('utf-8')
    return st.download_button(
        label="📥 下载",
        data=text,
        file_name=filename,
        mime="text/plain; charset=utf-8",
        use_container_width=True
    )


def count_words(text):
    """统计文本字数（中文字符数）"""
    # 移除标点符号和空格
    cleaned_text = re.sub(r'[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uff00-\uffef]', '', text)
    return len(cleaned_text)


# ===================== 4. Streamlit 页面主逻辑 =====================
def main():
    # 初始化session state
    if 'clipboard_text' not in st.session_state:
        st.session_state['clipboard_text'] = ""
    if 'generated_content' not in st.session_state:
        st.session_state['generated_content'] = ""
    if 'generate_time' not in st.session_state:
        st.session_state['generate_time'] = ""

    # 页面配置
    st.set_page_config(
        page_title="我的 AI 文字生成工具（Kimi+Streamlit版）",
        page_icon="✍️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 自定义CSS美化 - 重点优化背景和视觉效果
    st.markdown("""
        <style>
        /* 全局背景样式 */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4eaf5 100%);
            background-attachment: fixed;
        }

        /* 主容器样式 */
        [data-testid="stMainContainer"] {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        /* 基础样式优化 */
        .stButton>button {
            height: 3em;
            border-radius: 8px;
            border: none;
            transition: all 0.2s ease;
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .stTextInput>div>div>input {
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            padding: 8px 12px;
        }

        .stTextArea>div>div>textarea {
            border-radius: 6px;
            font-size: 16px;
            line-height: 1.6;
            border: 1px solid #e0e0e0;
            padding: 12px;
        }

        .stNumberInput>div>div>input {
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }

        .main-header {
            font-size: 2.5rem;
            color: #2E86AB;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* 生成结果卡片样式 - 增强视觉效果 */
        .result-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            border: 1px solid #f0f0f0;
        }

        /* 加载动画优化 */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .pulse {
            animation: pulse 1.5s infinite;
        }

        /* 按钮组样式 */
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }

        /* 统计信息样式 */
        .word-count {
            font-size: 0.9rem;
            color: #666;
            margin-top: 8px;
            padding: 4px 12px;
            background-color: #f5f5f5;
            border-radius: 6px;
            display: inline-block;
        }

        /* 响应式调整 */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem;
            }
            .result-card {
                padding: 15px;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    # 页面标题
    st.markdown('<p class="main-header">📝 AI 文字生成工具 (Kimi 版)</p>', unsafe_allow_html=True)
    st.divider()

    # 使用说明
    with st.expander("📖 使用说明", expanded=False):
        st.write("""
        1. 请先在 [月之暗面官网](https://platform.moonshot.cn/) 获取你的API密钥
        2. 选择合适的生成模板，填写相关参数
        3. 点击生成按钮，等待AI创作完成
        4. 生成结果可复制或下载使用

        ⚠️ 注意：API密钥请妥善保管，不要分享给他人，使用产生的费用由账号所有者承担
        """)

    st.caption(f"当前使用模型：{KIMI_MODEL} | 国内接口 ✔ 无需代理 ✔")
    st.divider()

    # 1. Kimi API密钥输入（使用st.text_input并缓存）
    kimi_api_key = st.text_input(
        label="🔑 Kimi API 密钥",
        type="password",
        placeholder="请输入你的Kimi密钥 (格式：sk-xxxxxxxxxxxxxxxxxx)",
        help="密钥从月之暗面(Kimi)官网获取，请勿泄露给他人",
        value=st.session_state.get('kimi_api_key', ''),
        key='api_key_input'
    )

    # 保存API密钥到session state
    if kimi_api_key:
        st.session_state['kimi_api_key'] = kimi_api_key

    st.divider()

    # 2. 模板选择
    template_type = st.selectbox(
        label="📋 选择生成模板",
        options=list(PROMPT_TEMPLATES.keys()),
        index=0,
        help="选择不同模板将展示对应必填参数"
    )
    current_params = PROMPT_TEMPLATES[template_type]["params"]
    st.divider()

    # 3. 动态渲染对应参数输入框
    st.subheader(f"✏️ 填写【{template_type}】参数", divider="blue")
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        for param in current_params:
            if param == "主题":
                st.text_input("主题", placeholder="友情、星空、冒险、成长...", key="主题")
            elif param == "风格":
                st.text_input("风格", placeholder="治愈、悬疑、科幻、古风、幽默...", key="风格")
            elif param == "字数":
                st.number_input("字数限制", min_value=100, max_value=2000, value=500, step=100, key="字数")
            elif param == "产品名称":
                st.text_input("产品名称", placeholder="无线蓝牙耳机、智能保温杯、代餐奶昔...", key="产品名称")
            elif param == "平台":
                st.text_input("推广平台", placeholder="小红书、抖音、朋友圈、知乎、B站...", key="平台")
            elif param == "核心卖点":
                st.text_input("核心卖点", placeholder="超长续航、便携小巧、0糖0卡、性价比高...", key="核心卖点")
            elif param == "论文题目":
                st.text_input("论文题目", placeholder="基于深度学习的图像识别技术研究...", key="论文题目")
            elif param == "学科":
                st.text_input("学科领域", placeholder="计算机科学、汉语言文学、市场营销、教育学...", key="学科")
            elif param == "章节数":
                st.number_input("章节数量", min_value=3, max_value=10, value=5, step=1, key="章节数")
            elif param == "用户输入":
                st.text_area("自由创作需求", placeholder="请详细描述你的创作需求，越详细生成效果越好...", height=200,
                             key="用户输入")

    with col2:
        st.info("""
        💡 填写提示：
        - 参数越详细，生成效果越好
        - 字数请填写合理范围
        - 风格描述越具体越好
        """)

    st.divider()

    # 4. 生成按钮区域
    col_btn, col_clear, _ = st.columns([0.2, 0.1, 0.7])
    with col_btn:
        generate_btn = st.button("🚀 立即生成", type="primary", use_container_width=True)

    with col_clear:
        if st.button("🧹 清空结果", use_container_width=True):
            st.session_state['generated_content'] = ""
            st.session_state['generate_time'] = ""
            st.rerun()

    st.divider()

    # ===================== 生成结果展示区域（重点优化） =====================
    st.subheader("📄 生成结果", divider="green")

    # 创建结果容器
    result_container = st.container()

    with result_container:
        # 生成按钮点击后的处理
        if generate_btn:
            # 显示加载状态
            with st.spinner('<span class="pulse">✨ AI 正在生成内容，请稍候...</span>', unsafe_allow_html=True):
                # 使用缓存的API密钥
                api_key_to_use = st.session_state.get('kimi_api_key', kimi_api_key)
                result = generate_content(api_key_to_use, template_type)

                # 保存结果和生成时间
                st.session_state['generated_content'] = result
                st.session_state['generate_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 显示结果（包括历史结果）
        if st.session_state['generated_content']:
            content = st.session_state['generated_content']

            # 创建卡片式布局
            st.markdown('<div class="result-card">', unsafe_allow_html=True)

            if content.startswith("❌"):
                # 错误信息展示
                st.error(content, icon="🚨")
            else:
                # 成功结果展示（重点优化）
                # 显示生成信息和操作按钮
                col_info, col_actions = st.columns([0.7, 0.3])
                with col_info:
                    st.success(f"✅ 生成完成！生成时间：{st.session_state['generate_time']}", icon="🎉")
                    # 字数统计
                    word_count = count_words(content)
                    st.markdown(f'<div class="word-count">📊 字数统计：{word_count} 个中文字符</div>',
                                unsafe_allow_html=True)

                with col_actions:
                    # 操作按钮组 - 增加悬停效果
                    col_copy, col_download = st.columns(2)
                    with col_copy:
                        st.button(
                            "📋 复制",
                            on_click=copy_to_clipboard,
                            args=(content,),
                            use_container_width=True
                        )
                    with col_download:
                        download_content(content, template_type)

                # 内容展示区域 - 优化排版和阅读体验
                edited_content = st.text_area(
                    "生成内容",
                    value=content,
                    height=500,
                    label_visibility="collapsed",
                    placeholder="生成的内容将显示在这里...",
                    key="result_textarea"
                )

                # 实时更新session state中的内容（支持编辑后复制/下载）
                if edited_content != st.session_state['generated_content']:
                    st.session_state['generated_content'] = edited_content

                # 额外提示
                st.caption("💡 提示：你可以直接编辑文本框中的内容，修改后仍可复制/下载")

            # 关闭卡片容器
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 无结果时显示更友好的提示
            st.markdown("""
            <div class="result-card">
                <div style="text-align: center; padding: 40px 0; color: #666;">
                    <span style="font-size: 3rem; margin-bottom: 1rem; display: block;">✏️</span>
                    <p style="font-size: 1.1rem; margin-bottom: 0;">填写参数后点击「立即生成」按钮</p>
                    <p style="font-size: 0.9rem; color: #999;">AI生成的内容将展示在这里</p>
                </div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
