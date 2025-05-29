import pandas as pd
import streamlit as st
from database.analysis_ops import (
    add_job, extract_text, get_all_jobs, get_all_models,
    get_job_by_id, get_resume_by_id, get_resume_json_by_resume_id,
    get_user_resumes, save_analysis_result, save_resume_score_detail,
    score_resume_with_llm, update_json_resume_data,
    structure_job_requirements, structure_resume_content
)
from utils.secret import decrypt_api_key


# ✅ 页面主入口
def display_analysis(phonenumber: str, username: str):
    st.title("📊 简历分析中心")

    resume_id, resume_name, file_path = select_resume(phonenumber)
    if not resume_id:
        st.info("暂无简历，请先上传。")
        return

    job_data_row, job_display, job_full_description = select_job()
    api_name, api_url, api_key = select_model(phonenumber)

    if st.button("🚀 开始分析"):
        process_resume_analysis(
            resume_id=resume_id,
            resume_file_path=file_path,
            job_data_row=job_data_row,
            job_display=job_display,
            job_full_description=job_full_description,
            api_name=api_name,
            api_url=api_url,
            api_key=api_key,
            phonenumber=phonenumber
        )


# 🧩 选择简历
def select_resume(phonenumber: str):
    resumes = get_user_resumes(phonenumber)
    if not resumes:
        return None, None, None

    resume_dict = {r[1]: r[0] for r in resumes}
    selected_name = st.selectbox("请选择要分析的简历", list(resume_dict.keys()))
    selected_id = resume_dict[selected_name]
    resume_row = get_resume_by_id(selected_id)
    return selected_id, selected_name, resume_row[4]


# 🧩 选择职位
def select_job():
    jobs = get_all_jobs()
    job_options = [f"{j[1]} - {j[2]}" for j in jobs]
    job_mapping = {label: j[0] for label, j in zip(job_options, jobs)}

    selected_label = st.selectbox("选择职位", job_options)

    with st.expander("➕ 新增职位"):
        with st.form("add_job_form"):
            name = st.text_input("职位名称")
            category = st.text_input("职位类别")
            description = st.text_area("职位描述", height=100)
            if st.form_submit_button("添加职位"):
                if name.strip() and category.strip():
                    add_job(name, category, description)
                    st.success("职位添加成功！")
                    st.rerun()
                else:
                    st.error("职位名称和类别不能为空")

    job_id = job_mapping[selected_label]
    job_row = get_job_by_id(job_id)
    job_display = f"{job_row[1]} - {job_row[2]}"
    job_full_description = f"{job_display} - {job_row[3]}"
    st.success(f"✅ 已选职位：{job_display}")

    return job_row, job_display, job_full_description


# 🧩 选择模型
def select_model(phonenumber: str):
    models = get_all_models(phonenumber)
    model_options = [m["api_name"] for m in models]
    selected_model = st.selectbox("选择模型", model_options)

    if selected_model:
        model_info = next((m for m in models if m["api_name"] == selected_model), None)
        if model_info:
            st.success(f"✅ 已选模型：{model_info['api_name']}")
            return (
                model_info["api_name"],
                model_info["api_url"],
                decrypt_api_key(model_info["api_key"])
            )
    return None, None, None


# ✅ 简历分析主逻辑
def process_resume_analysis(
    resume_id, resume_file_path, job_data_row,
    job_display, job_full_description,
    api_name, api_url, api_key, phonenumber
):
    # 结构化简历
    structured_resume = get_resume_json_by_resume_id(resume_id)
    if not structured_resume:
        raw_text = extract_text(resume_file_path)
        structured_resume = structure_resume_content(raw_text, api_url, api_key, api_name)
        update_json_resume_data(resume_id, structured_resume)
        st.success("✅ 简历结构化完成")

    # 展示结构化简历
    st.subheader("📄 结构化简历内容")
    st.table(pd.DataFrame(flatten_dict(structured_resume).items(), columns=["字段", "内容"]))

    # 结构化岗位要求
    structured_job = structure_job_requirements(job_full_description, api_url, api_key, api_name)
    st.success("✅ 岗位结构化完成")
    st.subheader("🧾 结构化岗位要求")
    st.table(pd.DataFrame(flatten_dict(structured_job).items(), columns=["字段", "要求"]))

    # 匹配评分
    st.write("📝 简历与岗位匹配评分")
    score_dict = score_resume_with_llm(structured_resume, structured_job, api_url, api_key, api_name)
    st.success("✅ 匹配评分完成")

    score_display, avg_score = format_score_output(score_dict)
    st.info(score_display)
    # st.write(f"score_display:{score_display}")
    # st.write(f"avg_score:{avg_score}")
    # st.write(f"str(score_dict):{str(score_dict)}")
    # 保存结果
    job_id = job_data_row[0]
    analysis_id = save_analysis_result(
        phonenumber=phonenumber,
        resume_id=resume_id,
        score_dict=score_dict,
        job_id=job_id,
        outcome=score_display,
        json_analysis_result=str(score_dict),
        # score_json=str(score_dict),
        state="已完成"
    )

    save_resume_score_detail(
        analysis_id=analysis_id,
        score_data={k.split("（")[1][:-1]: v for k, v in score_display_lines(score_dict)},
        job_name=job_display
    )


# 📌 工具函数：扁平化结构化字典
def flatten_dict(d: dict):
    return {k: ", ".join(v) if isinstance(v, list) else str(v) for k, v in d.items()}


# 📌 工具函数：格式化评分展示
def format_score_output(score_dict):
    items = score_display_lines(score_dict)
    avg = int(sum(v for _, v in items) / len(items))
    output = f"该简历的整体评分为 **{avg} 分**，各项得分如下：\n\n"
    for k, v in items:
        output += f"- {k}: {v} 分\n"
    return output, avg


def score_display_lines(score_dict):
    return [
        ('教育背景（education_score）', score_dict.get('education_score', 0)),
        ('技能匹配（skills_score）', score_dict.get('skills_score', 0)),
        ('经验匹配（experience_score）', score_dict.get('experience_score', 0)),
        ('证书匹配（certifications_score）', score_dict.get('certifications_score', 0)),
        ('人格特质（personal_qualities_score）', score_dict.get('personal_qualities_score', 0)),
        ('奖项荣誉（honors_score）', score_dict.get('honors_score', 0)),
        ('语言能力（languages_score）', score_dict.get('languages_score', 0)),
        ('工具平台（tools_score）', score_dict.get('tools_score', 0))
    ]


# ✅ 页面测试入口（非 Streamlit 页面部署环境下可用）
if __name__ == "__main__":
    display_analysis(phonenumber="18326660594", username="zhs")
