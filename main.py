import streamlit as st
from streamlit_echarts import st_echarts
import pandas as pd
from database.db import fetch_data, get_connection
from datetime import datetime
import json



# 页面布局
st.set_page_config(page_title="简历分析大屏", layout="wide")
st.title("📊 简历分析数据大屏")

# 数据加载
total, month_data, detail_data = fetch_data()
df_month = pd.DataFrame(month_data)
df_detail = pd.DataFrame(detail_data)

# 一、总分析数量
st.metric("🔢 总简历分析数", total)

co1,co2 = st.columns([1,1])
# 二、月度分布柱状图+折线图
with co1:
  st.subheader("📈 每月分析数量分布")
  month_chart_option = {
      "tooltip": {"trigger": "axis"},
      "legend": {"data": ["数量"]},
      "xAxis": {"type": "category", "data": df_month['month'].tolist()},
      "yAxis": {"type": "value"},
      "series": [
          {"name": "数量", "type": "bar", "data": df_month['count'].tolist()},
          {"name": "数量", "type": "line", "data": df_month['count'].tolist()},
      ]
  }
  st_echarts(month_chart_option, height="400px")

with co2:
  # 三、选择简历记录，显示雷达图和总分趋势
  st.subheader("📌 分析记录详情与评分")
  selected_resume = st.selectbox("选择简历", df_detail['resume_name'].unique())
  resume_filtered = df_detail[df_detail['resume_name'] == selected_resume]

  # 构造显示标签：分析时间（年月日）+ 岗位 + 总分
  resume_filtered['display_label'] = resume_filtered.apply(
      lambda row: f"{pd.to_datetime(row['analysis_time']).strftime('%Y-%m-%d')} | {row['choose_job']} | {row['overall_score']}分",
      axis=1
  )

  # 选择分析记录（下拉框展示组合信息）
  selected_analysis_label = st.selectbox(
      "选择分析记录",
      resume_filtered['display_label'].tolist()
  )

  # 获取所选记录的完整行
  analysis_row = resume_filtered[resume_filtered['display_label'] == selected_analysis_label].iloc[0]

  # 雷达图评分项
  radar_indicators = [
      {"name": "学历", "max": 100},
      {"name": "技能", "max": 100},
      {"name": "经验", "max": 100},
      {"name": "证书", "max": 100},
      {"name": "素质", "max": 100},
      {"name": "荣誉", "max": 100},
      {"name": "语言", "max": 100},
      {"name": "工具", "max": 100},
  ]
  radar_data = [int(analysis_row[col]) for col in [
      'education_score', 'skills_score', 'experience_score',
      'certifications_score', 'personal_qualities_score',
      'honors_score', 'languages_score', 'tools_score'
  ]]


  print(radar_data)
  print(type(radar_data))
  radar_option = {
      "tooltip": {},
      "radar": {"indicator": radar_indicators},
      "series": [{
          "type": "radar",
          "data": [{"value": radar_data, "name": selected_resume}]
      }]
  }
  st_echarts(radar_option, height="400px")

# 四、该简历所有分析记录的总分趋势图
st.subheader("📉 总分趋势图")
trend_df = resume_filtered.sort_values(by='analysis_time')
trend_option = {
    "xAxis": {"type": "category", "data": trend_df['analysis_time'].astype(str).tolist()},
    "yAxis": {"type": "value"},
    "series": [{"data": trend_df['overall_score'].tolist(), "type": "line"}]
}
st_echarts(trend_option, height="400px")

import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.faker import Faker
from streamlit_echarts import st_pyecharts
c = (
    Line()
    .add_xaxis(trend_df['analysis_time'].astype(str).tolist())
    .add_yaxis("总分", trend_df['overall_score'].tolist())
    .set_global_opts(title_opts=opts.TitleOpts(title="简历得分趋势"))
)

st_pyecharts(c)


# 五、热力图展示当年分析简历的活跃情况
st.subheader("🌡️ 年度分析热力图")
this_year = datetime.now().year
df_detail['day'] = pd.to_datetime(df_detail['analysis_time']).dt.strftime('%Y-%m-%d')
df_this_year = df_detail[df_detail['analysis_time'].dt.year == this_year]
day_counts = df_this_year['day'].value_counts().sort_index()
heatmap_data = [[day, count] for day, count in day_counts.items()]
calendar_option = {
    "tooltip": {"position": "top"},
    "visualMap": {
        "min": 0,
        "max": max(day_counts),
        "calculable": True,
        "orient": "horizontal",
        "left": "center",
        "bottom": "15%"
    },
    "calendar": {
        "range": str(this_year)
    },
    "series": [{
        "type": "heatmap",
        "coordinateSystem": "calendar",
        "data": heatmap_data
    }]
}
st_echarts(calendar_option, height="300px")
