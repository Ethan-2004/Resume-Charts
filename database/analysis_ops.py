import mysql.connector
from datetime import datetime
from database.db_config  import DB_CONFIG
def get_mysql_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_user_resumes(phonenumber):
    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, resume_name, upload_date, school, education, expected_salary, age, region, gender, state 
        FROM resumes WHERE phonenumber=%s
    """, (phonenumber,))
    resumes = c.fetchall()
    c.close()
    conn.close()
    return resumes
  
def get_resume_by_id(resume_id):
    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM resumes WHERE id = %s", (resume_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return row
  
  
def get_all_jobs():
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, job_name, job_category, job_description, created_at FROM jobs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
  
# 添加单个职位
def add_job(job_name, job_category, job_description):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO jobs (job_name, job_category, job_description, created_at)
        VALUES (%s, %s, %s, %s)
    """, (job_name, job_category, job_description, created_at))
    conn.commit()
    cursor.close()
    conn.close()
    
# 根据ID查询单个职位
def get_job_by_id(job_id):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, job_name, job_category, job_description, created_at FROM jobs WHERE id=%s", (job_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row
  
  
def get_all_models(phonenumber):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT api_name, api_url, api_key
        FROM analysis_api
        WHERE phonenumber = %s
        ORDER BY created_at DESC
    """, (phonenumber,))
    results = cursor.fetchall()
    cursor.close()
    return results
  
  
import os
import json
import re
import pdfplumber
import docx
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from utils.prompt_templateops import (
    prompt_template_format_jobrequire,
    prompt_template_format_resume,
    prompt_template_format_resume_job_score
)
from utils.zhipuapi import call_gpt_model


def save_resume_score_detail(analysis_id, score_data, job_name):
    """
    将评分结果保存到数据库的 resume_score_detail 表中。
    :param analysis_id: 对应 resume_analysis 表中的 id
    :param score_data: 包含各项评分的字典
    :param job_name: 所选岗位名称
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    query = """
    INSERT INTO resume_score_detail (
        analysis_id,
        choose_job,
        education_score,
        skills_score,
        experience_score,
        certifications_score,
        personal_qualities_score,
        honors_score,
        languages_score,
        tools_score
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        analysis_id,
        job_name,
        score_data.get("education_score", 0),
        score_data.get("skills_score", 0),
        score_data.get("experience_score", 0),
        score_data.get("certifications_score", 0),
        score_data.get("personal_qualities_score", 0),
        score_data.get("honors_score", 0),
        score_data.get("languages_score", 0),
        score_data.get("tools_score", 0)
    )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
def update_json_resume_data(resume_id, structured_resume):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resumes
        SET json_resume_data = %s
        WHERE id = %s
    """, (json.dumps(structured_resume, ensure_ascii=False), resume_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_resume_json_by_resume_id(resume_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT json_resume_data FROM resumes WHERE id = %s", (resume_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row["json_resume_data"]:
        try:
            return json.loads(row["json_resume_data"])
        except Exception as e:
            print("JSON 解析失败:", e)
            return None
    return None

def parse_model_output(raw_str: str) -> dict:
    """
    清洗模型返回的内容，将 ```json ... ``` 包裹的内容转换为 Python 字典
    """
    cleaned_str = re.sub(r"^```json\s*|```$", "", raw_str.strip(), flags=re.DOTALL)
    try:
        data = json.loads(cleaned_str)
    except Exception as e:
        st.error(f"解析模型返回JSON失败：{e}")
        return {}
    return data

def insert_analysis(phonenumber, resume_id, job_id, overall_score, analysis_summary, json_analysis_result, status="已完成"):
    """
    将简历分析结果插入到数据库 resume_analysis 表中。
    返回新插入的记录ID。
    """
    conn = get_mysql_connection()
    c = conn.cursor()

    insert_sql = """
        INSERT INTO resume_analysis (
            phonenumber, resume_id, job_id, overall_score, analysis_time,
            analysis_summary, json_analysis_result, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        phonenumber, resume_id, job_id, overall_score,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        analysis_summary, json_analysis_result, status
    )

    c.execute(insert_sql, values)
    inserted_id = c.lastrowid
    conn.commit()
    c.close()
    conn.close()
    return inserted_id

def extract_text(file_path):
    """
    从上传的 PDF 或 DOCX 文件中提取文本内容
    """
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                texts = [page.extract_text() for page in pdf.pages if page.extract_text()]
                return "\n".join(texts)
        elif ext == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            raise ValueError("不支持的文件类型")
    except Exception as e:
        raise RuntimeError(f"简历文本提取失败: {e}")

def structure_resume_content(resume_text, api_url, api_key, api_name):
    """
    调用大模型将简历文本结构化
    """
    prompt = prompt_template_format_resume(resume_text)
    try:
        response = call_gpt_model(prompt_template=prompt, api_url=api_url, api_key=api_key, api_name=api_name)
        structured_resume = parse_model_output(response)
        if not isinstance(structured_resume, dict):
            raise ValueError("模型返回的结构化简历不是字典格式")
        return structured_resume
    except Exception as e:
        st.error(f"结构化简历调用失败: {e}")
        return {}

def structure_job_requirements(job_requirements, api_url, api_key, api_name):
    """
    调用大模型将岗位要求结构化
    """
    prompt = prompt_template_format_jobrequire(job_requirements)
    try:
        response = call_gpt_model(prompt_template=prompt, api_url=api_url, api_key=api_key, api_name=api_name)
        structured_job = parse_model_output(response)
        if not isinstance(structured_job, dict):
            raise ValueError("岗位结构化失败")
        return structured_job
    except Exception as e:
        st.error(f"结构化岗位要求失败: {e}")
        return {}
def score_resume_with_llm(structured_resume, structured_job, api_url, api_key, api_name):
    """
    使用大模型对结构化简历进行多维度评分
    """
    prompt = prompt_template_format_resume_job_score(structured_resume, structured_job)
    try:
        response = call_gpt_model(prompt_template=prompt, api_url=api_url, api_key=api_key, api_name=api_name)
        structured_data = parse_model_output(response)
        expected_keys = [
            "education_score", "skills_score", "experience_score",
            "certifications_score", "personal_qualities_score",
            "honors_score", "languages_score", "tools_score"
        ]
        if all(k in structured_data for k in expected_keys):
            return structured_data
        else:
            raise ValueError("返回结果不包含完整评分字段")
    except Exception as e:
        st.warning(f"评分失败：{e}，请使用兜底评分逻辑")
        def calc_score(required, actual):
            if not required:
                return 0
            return int(len(set(required) & set(actual)) / len(required) * 100)

        score = {
            "education_score": 60,
            "skills_score": calc_score(structured_job.get("required_skills", []), structured_resume.get("skills", [])),
            "experience_score": calc_score(structured_job.get("required_experience", []), structured_resume.get("experience", [])),
            "certifications_score": calc_score(structured_job.get("required_certifications", []), structured_resume.get("certifications", [])),
            "personal_qualities_score": calc_score(structured_job.get("desired_personal_qualities", []), structured_resume.get("personal_qualities", [])),
            "honors_score": calc_score(structured_job.get("preferred_honors", []), structured_resume.get("honors", [])),
            "languages_score": calc_score(structured_job.get("required_languages", []), structured_resume.get("languages", [])),
            "tools_score": calc_score(structured_job.get("preferred_tools", []), structured_resume.get("tools", [])),}
        return score


def save_analysis_result(
                        phonenumber,
                        resume_id,
                        score_dict,
                        job_id,                    
                        outcome,
                        json_analysis_result,
                        state="已完成"):
    
    # 设置中文字体
    font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf", size=12)
    plt.rcParams['font.family'] = font.get_name()

    # 如果有负号显示问题，设置如下
    plt.rcParams['axes.unicode_minus'] = False

    score = int(sum(score_dict.values()) / len(score_dict))

    analysis_id = insert_analysis(
        phonenumber,
        resume_id,
        job_id=job_id,  # job_id，确保不是 None
        overall_score = score,
        analysis_summary=outcome,
        json_analysis_result=json_analysis_result,
        status=state
    )

    return analysis_id
    # def plot_score_radar(self, score_dict):
    #     """
    #     根据简历评分绘制雷达图
    #     """
    #     labels = ['教育', '知识技能', '经验', '证书', '个人品质', '荣誉', '语言', '工具']
    #     scores = [
    #         score_dict.get("education_score", 0),
    #         score_dict.get("skills_score", 0),
    #         score_dict.get("experience_score", 0),
    #         score_dict.get("certifications_score", 0),
    #         score_dict.get("personal_qualities_score", 0),
    #         score_dict.get("honors_score", 0),
    #         score_dict.get("languages_score", 0),
    #         score_dict.get("tools_score", 0)
    #     ]
    #     angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
    #     scores += scores[:1]
    #     angles += angles[:1]

    #     font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf", size=12)
    #     plt.rcParams['font.family'] = font.get_name()
    #     plt.rcParams['axes.unicode_minus'] = False

    #     fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    #     ax.set_theta_offset(3.14159 / 2)
    #     ax.set_theta_direction(-1)
    #     plt.xticks(angles[:-1], labels)
    #     ax.plot(angles, scores, linewidth=2, linestyle='solid')
    #     ax.fill(angles, scores, 'b', alpha=0.25)
    #     plt.title("简历多维匹配评分雷达图")
    #     st.pyplot(fig)
