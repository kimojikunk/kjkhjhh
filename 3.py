import streamlit as st
from openai import OpenAI

# ===================== 1. 基础配置（新增背景参数） =====================
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"

# 新增背景参数（仅修改模板，不新增冗余代码）
PROMPT_TEMPLATES = {
    "故事生成": {
        "template": "请以{主题}为核心，在{背景}背景下，写一个{风格}风格的短篇故事，字数控制在{字数}字左右。要求情节完整，角色鲜明，语言流畅。",
        "params": ["主题", "背景", "风格", "字数"]
    },
    "营销文案": {
        "template": "为{产品名称}撰写{平台}平台的营销文案，突出{核心卖点}，结合{背景}场景，语言风格{风格}，字数控制在{字数}字内。需吸引目标用户，激发购买欲。",
        "params": ["产品名称", "平台", "核心卖点", "背景", "风格", "字数"]
    },
    "论文提纲": {
        "template": "为《{论文题目}》（{学科}领域）设计详细提纲，结合{背景}研究背景，逻辑清晰，结构完整，至少包含{章节数}个章节。需列出每个章节的核心研究内容和逻辑关联。",
        "params": ["论文题目", "学科", "背景", "章节数"]
    },
    "自由创作": {
        "template": "{用户输入}",
        "params": ["用户输入"]
    }
}

# ===================== 2. AI 生成核心函数（无冗余修改） =====================
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
        else:
            return f"❌ 生成失败：{error_info}"

# ===================== 3. 页面主逻辑（五彩渐变背景+背景参数） =====================
def main():
    st.set_page_config(
        page_title="我的 AI 文字生成工具（Kimi+Streamlit版）",
        page_icon="✍️",
        layout="wide"
    )

    # 五彩渐变背景（核心修改部分）
    st.markdown("""
        <style>
        /* 全局五彩渐变背景 */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, 
                #ff9a9e 0%, 
                #fad0c4 20%, 
                #fad0c4 40%, 
                #fbc2eb 60%, 
                #a6c1ee 80%, 
                #f5f7fa 100%);
            background-attachment: fixed;
        }
        /* 内容区域轻微美化 */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 6px;
            border: 1px solid #dee2e6;
            background: rgba(255, 255, 255, 0.85);
        }
        /* 按钮美化（可选，搭配渐变风格） */
        .stButton>button {
            background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
            color: white;
            border: none;
            border-radius: 6px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("📝 AI 文字生成工具 (Kimi 版)")
    st.divider()
    st.info("✅ 操作步骤：1.输入Kimi密钥 → 2.选择模板 → 3.填写参数 → 4.点击生成")
    st.caption(f"当前使用模型：{KIMI_MODEL} | 国内接口 ✔ 无需代理 ✔")
    st.divider()

    # 1. API密钥输入
    kimi_api_key = st.text_input(
        label="🔑 Kimi API 密钥",
        type="password",
        placeholder="请输入你的Kimi密钥 (格式：sk-xxxxxxxxxxxxxxxxxx)",
        help="密钥从月之暗面(Kimi)官网获取，请勿泄露给他人"
    )
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

    # 3. 动态渲染参数（仅新增背景参数输入，不修改原有逻辑）
    st.subheader(f"✏️ 填写【{template_type}】参数", divider=True)
    col1, _ = st.columns([0.6, 0.4])
    with col1:
        for param in current_params:
            if param == "背景":  # 新增背景参数输入
                st.text_input("背景/场景", placeholder="例如：校园、职场、未来都市、古代江湖...", key="背景")
            elif param == "主题":
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
                st.text_area("自由创作需求", placeholder="请详细描述你的创作需求，越详细生成效果越好...", height=200, key="用户输入")

    st.divider()

    # 4. 生成按钮 + 结果展示（无修改）
    col_btn, _ = st.columns([0.2, 0.8])
    with col_btn:
        generate_btn = st.button("🚀 立即生成", type="primary", use_container_width=True)

    st.divider()
    st.subheader("📄 生成结果", divider=True)
    result_box = st.empty()

    if generate_btn:
        with st.spinner("✨ AI 正在生成内容，请稍候..."):
            result = generate_content(kimi_api_key, template_type)
            if result.startswith("❌"):
                result_box.error(result)
            else:
                result_box.success("✅ 生成完成！")
                st.text_area("生成内容", value=result, height=500)

if __name__ == "__main__":

    main()
