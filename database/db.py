import pymysql
from .db_config import DB_CONFIG
# 连接数据库
def get_connection():
    return pymysql.connect(**DB_CONFIG)

# 查询数据
def fetch_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT COUNT(*) AS total FROM resume_analysis")
    total_analysis = cursor.fetchone()['total']

    cursor.execute("""
        SELECT DATE_FORMAT(analysis_time, '%Y-%m') AS month, COUNT(*) AS count
        FROM resume_analysis
        GROUP BY month
    """)
    monthly_distribution = cursor.fetchall()

    cursor.execute("""
        SELECT ra.id, r.resume_name, j.job_name, ra.overall_score, ra.analysis_time, rs.*
        FROM resume_analysis ra
        JOIN resumes r ON ra.resume_id = r.id
        LEFT JOIN jobs j ON ra.job_id = j.id
        JOIN resume_score_detail rs ON ra.id = rs.analysis_id
    """)
    analysis_details = cursor.fetchall()

    conn.close()
    return total_analysis, monthly_distribution, analysis_details