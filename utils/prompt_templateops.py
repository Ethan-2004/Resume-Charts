
def prompt_template_format_resume(resume_text):
  # print(resume_text)
  prompt1 = """
你是一位专业的简历分析师，请对以下简历文本进行结构化提取、智能分析和合理推理，完成以下任务：

---
📄 以下是简历原文内容：

{}
""".format(resume_text)

  prompt2 = """
🎯 **目标输出**：请将简历信息提取并按如下字段返回一个**标准 JSON 对象**（无需注释、不带多余文本），包括：


"{
  "name": "",                           // 姓名，如无法明确请留空
  "gender": "",                         // 性别（男/女），如无法明确请合理推断
  "age": 0,                             // 年龄，若未明确请根据毕业年份或学历合理推测
  "phone": "",                          // 手机号，仅数字
  "email": "",                          // 邮箱地址
  "education": "",                      // 最高学历：高中、大专、本科、硕士、博士
  "school": "",                         // 毕业院校
  "major": "",                          // 所学专业
  "skills": [],                         // 技能关键词列表，如：["Python", "C++", "数据分析"]
  "certifications": [],                // 所获证书，如：["英语四级", "计算机二级", "华为HCIA"]
  "experience": "",                     // 项目或实习/工作经验（文本摘要）
  "personal_qualities": [],            // 品质关键词，如 ["认真", "踏实", "沟通能力强"]
  "honors": [],                        // 获奖情况，如 ["三等奖学金", "挑战杯二等奖"]
  "languages": [],                     // 语言能力，如 ["英语四级", "日语N2"]
  "tools": [],                         // 熟练工具/平台，如 ["Linux", "Flask", "MySQL", "Vue"]
  "expected_salary": "",               // 期望薪资（如有），若无请返回 "面议"
  "region": "",                        // 求职区域，如简历中有提及（如：江苏、上海）
  "position_direction": ""             // 模型自动推断候选人适合的岗位方向，如：“后端开发工程师”、“数据分析师”、“测试工程师”等
}
"
🔍 注意事项：
如果简历中没有明确写出某项，请根据上下文推断，若无迹可循则设为默认值或空。
请根据技能、经历、工具等自动判断候选人适合的岗位方向 position_direction。
返回的 JSON 必须符合格式规范，可被 Python json.loads() 正确解析。

          """
  prompt=f"{prompt1}{prompt2}"
  return prompt


def prompt_template_format_jobrequire(job_requirements):
    prompt = f"""
你是一位资深招聘专家，请你根据以下【职位名称与描述】提取岗位核心要素，并结构化为标准 JSON，仅包含以下字段：

```json
{{
  "required_education": "",               // 最低学历或优先学历（如本科、硕士）
  "required_skills": [],                 // 必须掌握的专业技能
  "preferred_experience": "",            // 推荐的工作/项目经验年限或类型
  "required_certifications": [],         // 必须或建议持有的证书（如软考、英语四六级等）
  "required_languages": [],              // 语言要求（如英语CET-4、日语N2等）
  "required_tools": [],                  // 岗位常用工具或技术平台（如Python、Excel、SQL、PPT等）
  "desired_personal_qualities": [],      // 企业偏好的性格或软技能（如责任心、沟通能力、抗压能力等）
  "honors_preference": ""                // 是否偏好获奖经历，如“有获奖经历优先”
}}
📌 说明与要求：

请基于招聘描述准确提取每一项；

所有字段必须输出，值为空时也必须保留字段；

字段内容尽量具体可量化，列表字段需使用 JSON 数组格式；

最终结果必须为纯 JSON 格式输出，不包含任何多余文字、解释或注释。

📄 职位信息如下：

{job_requirements}
"""
    return prompt

def prompt_template_format_resume_job_score(structured_resume, structured_job):
    prompt = f"""
你是一名人力资源与数据分析专家，任务是根据**应聘者简历信息**和**岗位要求**，从以下多个维度对该简历进行100分制评分，以评估其岗位匹配度。

📊 **评分维度**：
1. education_score：教育背景与岗位要求的匹配程度（0-100分）
2. skills_score：技能匹配度（0-100分）
3. experience_score：项目/实习/工作经验的匹配度（0-100分）
4. certifications_score：证书要求的匹配度（0-100分）
5. personal_qualities_score：人格特质的匹配度（0-100分）
6. honors_score：与岗位相关的奖励与荣誉匹配程度（0-100分）
7. languages_score：语言能力与岗位要求的匹配度（0-100分）
8. tools_score：熟练工具/平台的匹配度（0-100分）

请你通读结构化简历与岗位要求后，结合上下文进行专业判断，生成如下格式的标准 JSON：

```json
{{
  "education_score": 0,
  "skills_score": 0,
  "experience_score": 0,
  "certifications_score": 0,
  "personal_qualities_score": 0,
  "honors_score": 0,
  "languages_score": 0,
  "tools_score": 0
}}
🔒 注意事项：

所有字段必须包含，不能缺失；

请严格依据简历与岗位的实际内容进行评分，不要随意满分；

输出必须为标准 JSON 格式，不要包含任何多余文本或注释；

每个维度的评分标准应尽可能客观、明确、有据可依。

📄 简历信息：
{structured_resume}

📌 岗位要求：
{structured_job}
"""
    return prompt