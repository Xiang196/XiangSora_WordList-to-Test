import streamlit as st
import json
import requests

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "aaa"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def call_deepseek_api(prompt, temperature=0.7):
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"API 请求失败：{response.status_code}")
        return None
        
# 不再需要复杂的随机分布函数，使用简单的random.sample()即可

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def analyze_distribution(markdown_text, word_data=None):
    """分析试卷中的选项分布和单词使用情况"""
    import re
    from collections import Counter
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    
    # 分析选择题答案分布
    answer_pattern = re.compile(r'\d+\.\s+([A-D])', re.MULTILINE)
    answers = answer_pattern.findall(markdown_text)
    
    # 创建选项卡
    tab1, tab2 = st.tabs(["📊 选项分布", "📚 单词分布"])
    
    with tab1:
        if answers:
            # 计算选项分布
            answer_counts = Counter(answers)
            total = len(answers)
            
            # 创建选项分布表格
            option_data = {
                '选项': list(answer_counts.keys()),
                '数量': list(answer_counts.values()),
                '百分比': [f"{count/total*100:.1f}%" for count in answer_counts.values()]
            }
            
            st.subheader("📊 选项分布分析")
            
            # 显示分布表格
            st.dataframe(pd.DataFrame(option_data))
            
            # 创建选项分布图表
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(
                option_data['选项'],
                [count/total*100 for count in answer_counts.values()],
                color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
            )
            
            # 添加百分比标签
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.5,
                    f'{height:.1f}%',
                    ha='center', 
                    va='bottom'
                )
            
            # 添加理想分布参考线
            ax.axhline(y=25, color='r', linestyle='--', alpha=0.3)
            ax.text(0, 26, '理想分布 (25%)', color='r', alpha=0.7)
            
            # 设置图表样式
            ax.set_ylim(0, max([count/total*100 for count in answer_counts.values()]) + 5)
            ax.set_ylabel('百分比 (%)')
            ax.set_title('选择题答案分布')
            ax.grid(axis='y', alpha=0.3)
            
            # 显示图表
            st.pyplot(fig)
            
            # 分析结果
            max_deviation = max([abs(count/total*100 - 25) for count in answer_counts.values()])
            if max_deviation <= 2:
                st.success("✅ 选项分布非常均匀，最大偏差小于2%")
            elif max_deviation <= 5:
                st.info("ℹ️ 选项分布基本均匀，最大偏差小于5%")
            else:
                st.warning("⚠️ 选项分布不够均匀，最大偏差超过5%，建议降低AI创造性值重新生成")
                
            # 检查B选项比例
            if 'B' in answer_counts and answer_counts['B']/total*100 > 30:
                st.error("❌ B选项比例过高，超过30%，建议降低AI创造性值重新生成")
        else:
            st.info("未找到选择题答案数据")
    
    with tab2:
        st.subheader("📚 单词分布分析")
        
        # 提取试卷中使用的单词
        if word_data and 'words' in word_data:
            # 从JSON数据中获取完整单词列表
            all_words = [w['word'].lower() for w in word_data['words']]
            total_words = len(all_words)
            
            # 从试卷中提取使用的单词
            # 这里使用一个简化的正则表达式来匹配单词，实际应用中可能需要更复杂的匹配逻辑
            word_pattern = re.compile(r'\b([a-zA-Z]+)\b')
            used_words_raw = word_pattern.findall(markdown_text.lower())
            
            # 过滤出词库中的单词
            used_words = [w for w in used_words_raw if w in all_words]
            used_words_set = set(used_words)
            
            # 计算单词使用情况
            front_cutoff = int(total_words * 0.2)  # 前20%
            back_start = int(total_words * 0.5)    # 后50%
            
            front_words = set(all_words[:front_cutoff])
            middle_words = set(all_words[front_cutoff:back_start])
            back_words = set(all_words[back_start:])
            
            front_used = front_words.intersection(used_words_set)
            middle_used = middle_words.intersection(used_words_set)
            back_used = back_words.intersection(used_words_set)
            
            # 计算各部分使用比例
            front_ratio = len(front_used) / len(front_words) if front_words else 0
            middle_ratio = len(middle_used) / len(middle_words) if middle_words else 0
            back_ratio = len(back_used) / len(back_words) if back_words else 0
            
            # 创建单词分布表格
            word_data = {
                '词库部分': ['前20%单词', '中间30%单词', '后50%单词'],
                '使用数量': [len(front_used), len(middle_used), len(back_used)],
                '总数量': [len(front_words), len(middle_words), len(back_words)],
                '使用比例': [f"{front_ratio*100:.1f}%", f"{middle_ratio*100:.1f}%", f"{back_ratio*100:.1f}%"]
            }
            
            # 显示分布表格
            st.dataframe(pd.DataFrame(word_data))
            
            # 创建单词分布图表
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(
                word_data['词库部分'],
                [front_ratio*100, middle_ratio*100, back_ratio*100],
                color=['#3498db', '#2ecc71', '#e74c3c']
            )
            
            # 添加百分比标签
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.5,
                    f'{height:.1f}%',
                    ha='center', 
                    va='bottom'
                )
            
            # 添加目标分布参考线
            ax.axhline(y=30, color='r', linestyle='--', alpha=0.3)
            ax.text(0, 31, '前20%目标 (≤30%)', color='r', alpha=0.7)
            
            ax.axhline(y=40, color='g', linestyle='--', alpha=0.3)
            ax.text(2, 41, '后50%目标 (≥40%)', color='g', alpha=0.7)
            
            # 设置图表样式
            ax.set_ylim(0, max([front_ratio*100, middle_ratio*100, back_ratio*100]) + 10)
            ax.set_ylabel('使用比例 (%)')
            ax.set_title('单词分布情况')
            ax.grid(axis='y', alpha=0.3)
            
            # 显示图表
            st.pyplot(fig)
            
            # 分析结果
            if front_ratio <= 0.3 and back_ratio >= 0.4:
                st.success("✅ 单词分布符合要求：前20%单词使用率≤30%，后50%单词使用率≥40%")
            elif front_ratio > 0.3:
                st.warning(f"⚠️ 前20%单词使用率过高 ({front_ratio*100:.1f}% > 30%)，建议降低AI创造性值重新生成")
            elif back_ratio < 0.4:
                st.warning(f"⚠️ 后50%单词使用率过低 ({back_ratio*100:.1f}% < 40%)，建议降低AI创造性值重新生成")
        else:
            st.info("未找到单词数据，无法分析单词分布情况")


st.set_page_config(page_title="📘 AI词汇测试卷生成器", layout="wide")
st.title("📘 AI词汇测试卷生成器")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 生成设置")
    temperature = st.slider(
        "AI创造性", 
        min_value=0.1, 
        max_value=1.0, 
        value=0.3, 
        step=0.1,
        help="较低的值(0.1-0.3)会让AI更严格遵循指令，较高的值会增加创造性但可能导致不遵循预选单词"
    )
    st.markdown("""---
    **新特性**: 现在使用程序随机选择单词和分配选项，不再依赖AI随机，确保真正的随机分布。
    """)
    st.markdown("""---
    **提示**: 单词选择和选项分布已由程序保证，但如果AI不遵循预选单词，请降低AI创造性值重试。
    """)
    st.markdown("""---
    **版本**: 2.0.0 (简化版程序随机选词)
    """)


st.markdown("### 🧾 第一步：上传你的 JSON 文件（任选其一）")
col1, col2 = st.columns(2)

with col1:
    raw_file = st.file_uploader("📥 上传原始词汇文件（仅包含 'words': [...]）", type="json", key="raw")
with col2:
    enhanced_file = st.file_uploader("📥 上传增强后词汇文件（已含释义/例句等）", type="json", key="enhanced")

def prepare_exam_prompt(enhanced_data, temperature):
    """
    准备试卷生成的提示词，包含预先随机选择的单词
    """
    import random
    
    # 获取所有单词列表
    all_words = enhanced_data["words"]
    word_list = [w["word"] for w in all_words]
    
    # 定义各题型需要的单词数量
    section_counts = {
        "英译中": 15,
        "中译英": 10,
        "选词填空": 10,
        "词义辨析": 5,
        "翻译句子": 5,
        "短文填空": 10,
        "词形变化": 10
    }
    
    # 随机选择各题型的单词
    used_words = set()
    section_words = {}
    
    # 为每个题型选择单词
    for section, count in section_counts.items():
        # 过滤掉已使用的单词
        available_words = [w for w in word_list if w not in used_words]
        
        # 如果可用单词不足，则重置已使用单词集合（短文填空可以复用单词）
        if len(available_words) < count and section != "短文填空":
            st.warning(f"⚠️ 可用单词不足，部分单词将在多个题型中重复使用")
            # 只保留当前题型之前的已使用单词
            used_words = set()
            available_words = word_list
        
        # 简单随机选择单词
        selected = random.sample(available_words, min(count, len(available_words)))
        
        # 记录选择的单词
        section_words[section] = selected
        
        # 更新已使用单词集合（短文填空可以复用单词）
        if section != "短文填空":
            used_words.update(selected)
    
    # 为选择题生成均匀分布的答案位置
    answer_positions = {}
    
    # 为英译中题型分配答案位置
    positions_英译中 = ['A', 'B', 'C', 'D'] * (section_counts["英译中"] // 4)
    if section_counts["英译中"] % 4 > 0:
        positions_英译中.extend(['A', 'B', 'C', 'D'][:section_counts["英译中"] % 4])
    random.shuffle(positions_英译中)
    answer_positions["英译中"] = positions_英译中
    
    # 为词义辨析题型分配答案位置
    positions_词义辨析 = ['A', 'B', 'C', 'D'] * (section_counts["词义辨析"] // 4)
    if section_counts["词义辨析"] % 4 > 0:
        positions_词义辨析.extend(['A', 'B', 'C', 'D'][:section_counts["词义辨析"] % 4])
    random.shuffle(positions_词义辨析)
    answer_positions["词义辨析"] = positions_词义辨析
    
    # 构建包含预选单词的提示词
    prompt_template = load_prompt("templates/exam_prompt.txt")
    
    # 添加预选单词和答案位置信息
    prompt_with_selections = prompt_template.replace(
        "{粘贴你的完整 JSON 数据在这里}", 
        json.dumps(enhanced_data, ensure_ascii=False)
    )
    
    # 添加预选单词信息
    prompt_with_selections += "\n\n# 预选单词（必须严格使用）\n"
    for section, words in section_words.items():
        prompt_with_selections += f"## {section}题型单词\n"
        prompt_with_selections += ", ".join(words) + "\n\n"
    
    # 添加预分配答案位置信息
    prompt_with_selections += "\n# 预分配答案位置（必须严格按顺序使用）\n"
    for section, positions in answer_positions.items():
        prompt_with_selections += f"## {section}题型答案位置\n"
        prompt_with_selections += ", ".join(positions) + "\n\n"
    
    return prompt_with_selections

# 如果上传的是原始 JSON（仅有 words）
if raw_file:
    raw_data = json.load(raw_file)
    if "words" in raw_data:
        st.success(f"✅ 原始词汇列表读取成功，共 {len(raw_data['words'])} 个单词")

        if st.button("🚀 生成增强词汇信息"):
            enhance_prompt = load_prompt("templates/enhance_prompt.txt").replace(
                "{单词列表}", json.dumps(raw_data["words"], ensure_ascii=False)
            )
            st.info("⏳ AI正在生成结构化词汇信息...")
            enhanced_json_str = call_deepseek_api(enhance_prompt, temperature=0.7)

            # 解析增强后的JSON
            try:
                enhanced_data = json.loads(enhanced_json_str)
                st.code(enhanced_json_str, language="json")
                st.download_button("📥 下载增强版JSON", enhanced_json_str, file_name="enhanced_words.json")

                # 自动传递给试卷生成模块
                with st.expander("👉 继续生成试卷", expanded=True):
                    if st.button("📝 生成试卷"):
                        # 使用程序随机选择单词并准备提示词
                        exam_prompt = prepare_exam_prompt(enhanced_data, temperature)
                        st.info("⏳ AI正在生成测试卷...")
                        markdown_exam = call_deepseek_api(exam_prompt, temperature=temperature)
                        st.markdown(markdown_exam)
                        st.download_button("📥 下载试卷 Markdown", markdown_exam, file_name="word_test.md")
                        
                        # 添加分布分析功能
                        with st.expander("📊 查看分布分析", expanded=False):
                            analyze_distribution(markdown_exam, enhanced_data)
            except json.JSONDecodeError:
                st.error("❌ 生成的JSON格式有误，请重试")
                st.code(enhanced_json_str, language="json")

# 如果用户直接上传了增强版 JSON（跳过第一步）
elif enhanced_file:
    enhanced_data = json.load(enhanced_file)
    st.success("✅ 增强词汇数据读取成功，可直接生成试卷")

    if st.button("📝 直接生成试卷"):
        # 使用程序随机选择单词并准备提示词
        exam_prompt = prepare_exam_prompt(enhanced_data, temperature)
        st.info("⏳ AI正在生成测试卷...")
        markdown_exam = call_deepseek_api(exam_prompt, temperature=temperature)
        st.markdown(markdown_exam)
        st.download_button("📥 下载试卷 Markdown", markdown_exam, file_name="word_test.md")
        
        # 添加分布分析功能
        with st.expander("📊 查看分布分析", expanded=False):
            analyze_distribution(markdown_exam, enhanced_data)
