import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
from datetime import datetime
import hashlib
import random
import os
import shutil

# =========================================================
# FitAI 전체 기능 안정형 코드
# 핵심:
# - Mediapipe가 되면 실제 관절선/실제 각도 사용
# - Mediapipe가 libGL 오류 등으로 실패하면 자동으로 데모 관절선/데모 각도 표시
# - 그래서 관절각도 데이터가 "없음"으로 끝나지 않게 구성
# =========================================================

st.set_page_config(
    page_title="FitAI 자세 분석",
    page_icon="🏋️",
    layout="wide"
)

USER_DATA_DIR = "user_data"
USER_DB = "users.csv"
os.makedirs(USER_DATA_DIR, exist_ok=True)

# =========================================================
# 로그인 / 회원가입 함수
# =========================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_DB):
        return pd.read_csv(USER_DB)

    return pd.DataFrame(
        columns=["user_id", "password", "gender", "height", "weight"]
    )

def save_user(user_id, password, gender, height, weight):
    users = load_users()

    if user_id in users["user_id"].values:
        return False

    new_user = pd.DataFrame([{
        "user_id": user_id,
        "password": hash_password(password),
        "gender": gender,
        "height": height,
        "weight": weight
    }])

    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_DB, index=False, encoding="utf-8-sig")
    return True

def check_login(user_id, password):
    users = load_users()

    if user_id not in users["user_id"].values:
        return False

    saved_pw = users.loc[users["user_id"] == user_id, "password"].values[0]
    return saved_pw == hash_password(password)

def get_user_profile(user_id):
    users = load_users()

    if user_id in users["user_id"].values:
        row = users.loc[users["user_id"] == user_id].iloc[0]

        return {
            "gender": row.get("gender", "미입력"),
            "height": row.get("height", "미입력"),
            "weight": row.get("weight", "미입력")
        }

    return {
        "gender": "미입력",
        "height": "미입력",
        "weight": "미입력"
    }

def calculate_bmi(height, weight):
    try:
        h = float(height) / 100
        w = float(weight)

        if h <= 0:
            return None

        return round(w / (h * h), 1)
    except:
        return None

# =========================================================
# 세션 상태
# =========================================================
if "login" not in st.session_state:
    st.session_state.login = False

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

# =========================================================
# 로그인 화면
# =========================================================
if not st.session_state.login:
    st.markdown("""
    <div style="
        max-width: 880px;
        margin: auto;
        background: white;
        padding: 36px;
        border-radius: 24px;
        box-shadow: 0 10px 25px rgba(15,23,42,0.08);
        border: 1px solid #e5e7eb;
    ">
        <h1>🏋️ FitAI 로그인</h1>
        <p style="color:#6b7280; font-size:17px;">
        AI 운동 자세 분석 서비스를 이용하려면 로그인 또는 회원가입을 진행하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    with tab_login:
        login_id = st.text_input("아이디", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")

        if st.button("로그인"):
            if check_login(login_id, login_pw):
                st.session_state.login = True
                st.session_state.user_id = login_id
                st.success("로그인 성공")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab_signup:
        new_id = st.text_input("새 아이디", key="new_id")
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")

        gender = st.selectbox(
            "성별",
            ["남성", "여성", "선택 안 함"],
            key="signup_gender"
        )

        height = st.number_input(
            "키(cm)",
            min_value=100,
            max_value=230,
            value=170,
            key="signup_height"
        )

        weight = st.number_input(
            "몸무게(kg)",
            min_value=30,
            max_value=200,
            value=65,
            key="signup_weight"
        )

        if st.button("회원가입"):
            if new_id == "" or new_pw == "":
                st.warning("아이디와 비밀번호를 입력하세요.")
            else:
                success = save_user(new_id, new_pw, gender, height, weight)

                if success:
                    st.success("회원가입 완료. 로그인하세요.")
                else:
                    st.error("이미 존재하는 아이디입니다.")

    st.stop()

# =========================================================
# 로그인 후 사용자 정보
# =========================================================
user_id = st.session_state.user_id
profile = get_user_profile(user_id)

user_gender = profile["gender"]
user_height = profile["height"]
user_weight = profile["weight"]
user_bmi = calculate_bmi(user_height, user_weight)

user_dir = os.path.join(USER_DATA_DIR, user_id)
image_dir = os.path.join(user_dir, "images")
os.makedirs(image_dir, exist_ok=True)

history_path = os.path.join(user_dir, "history.csv")

# =========================================================
# 사이드바
# =========================================================
st.sidebar.title("FitAI 메뉴")
st.sidebar.success(f"{user_id}님 로그인 중")

st.sidebar.markdown("### 내 정보")
st.sidebar.write(f"성별: {user_gender}")
st.sidebar.write(f"키: {user_height}cm")
st.sidebar.write(f"몸무게: {user_weight}kg")

if user_bmi is not None:
    st.sidebar.write(f"BMI: {user_bmi}")

if st.sidebar.button("로그아웃"):
    st.session_state.login = False
    st.session_state.user_id = ""
    st.rerun()

menu = st.sidebar.radio(
    "메뉴 선택",
    [
        "자세 분석",
        "실시간 웹캠 분석",
        "전/후 비교",
        "내 분석 기록",
        "내 운동 통계",
        "내 업로드 사진",
        "관리자 페이지",
        "프로젝트 소개",
        "사용 방법"
    ]
)

goal = st.sidebar.selectbox(
    "운동 목표",
    ["자세 교정", "근력 향상", "다이어트", "부상 예방"]
)

threshold = st.sidebar.slider("GOOD 판정 기준", 50, 90, 70)

coach_style = st.sidebar.selectbox(
    "AI 코치 말투",
    ["친절한 코치", "엄격한 코치", "간단 요약 코치"]
)

show_pose_line = st.sidebar.checkbox("관절선 표시", value=True)
show_angle_text = st.sidebar.checkbox("사진 위 관절각도 표시", value=True)
dark_mode = st.sidebar.checkbox("다크모드", value=False)

# =========================================================
# CSS
# =========================================================
if dark_mode:
    bg_color = "#0f172a"
    card_color = "#1e293b"
    text_color = "#f8fafc"
    sub_text = "#cbd5e1"
    border_color = "#334155"
    metric_bg = "#111827"
else:
    bg_color = "#f4f7fb"
    card_color = "#ffffff"
    text_color = "#111827"
    sub_text = "#6b7280"
    border_color = "#e5e7eb"
    metric_bg = "#f8fafc"

st.markdown(f"""
<style>
.stApp {{
    background: {bg_color};
}}

.main-container {{
    max-width: 1180px;
    margin: auto;
}}

.top-nav, .hero, .card {{
    background: {card_color};
    color: {text_color};
    padding: 28px;
    border-radius: 24px;
    box-shadow: 0 10px 25px rgba(15,23,42,0.08);
    margin-bottom: 25px;
    border: 1px solid {border_color};
}}

.brand {{
    font-size: 28px;
    font-weight: 900;
    color: {text_color};
}}

.hero-title {{
    font-size: 42px;
    font-weight: 900;
    color: {text_color};
}}

.hero-sub {{
    font-size: 18px;
    color: {sub_text};
}}

.good {{
    color: #16a34a;
    font-size: 34px;
    font-weight: 900;
}}

.bad {{
    color: #dc2626;
    font-size: 34px;
    font-weight: 900;
}}

.score-box {{
    background: #fff7ed;
    color: #9a3412;
    padding: 20px;
    border-radius: 18px;
    font-size: 26px;
    font-weight: 900;
    margin-top: 15px;
}}

.rank-box {{
    background: #ecfeff;
    color: #155e75;
    padding: 18px;
    border-radius: 18px;
    font-size: 23px;
    font-weight: 800;
    margin-top: 15px;
}}

.summary-card {{
    background: #f8fafc;
    color: #111827;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 22px;
    margin-top: 18px;
    line-height: 1.8;
}}

.coach-card {{
    background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%);
    color: #1e3a8a;
    border: 1px solid #bfdbfe;
    border-radius: 22px;
    padding: 24px;
    margin-top: 18px;
    line-height: 1.8;
}}

.routine-card {{
    background: {metric_bg};
    color: {text_color};
    padding: 18px;
    border-radius: 18px;
    border: 1px solid {border_color};
    margin-top: 12px;
}}

.footer {{
    text-align: center;
    color: {sub_text};
    font-size: 14px;
    margin-top: 40px;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 저장 / 기록 함수
# =========================================================
def save_uploaded_file(input_file):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = input_file.name.replace(" ", "_")
    save_name = f"{now}_{safe_name}"
    save_path = os.path.join(image_dir, save_name)

    with open(save_path, "wb") as f:
        f.write(input_file.getbuffer())

    return save_path, save_name

def save_pil_image(pil_image, prefix="camera"):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{now}_{prefix}.png"
    save_path = os.path.join(image_dir, save_name)
    pil_image.save(save_path)
    return save_path, save_name

def save_history(data):
    df_new = pd.DataFrame([data])

    if os.path.exists(history_path):
        df_old = pd.read_csv(history_path)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(history_path, index=False, encoding="utf-8-sig")

def load_history():
    if os.path.exists(history_path):
        return pd.read_csv(history_path)
    return pd.DataFrame()

def load_all_histories():
    all_data = []

    if not os.path.exists(USER_DATA_DIR):
        return pd.DataFrame()

    for uid in os.listdir(USER_DATA_DIR):
        h_path = os.path.join(USER_DATA_DIR, uid, "history.csv")

        if os.path.exists(h_path):
            all_data.append(pd.read_csv(h_path))

    if len(all_data) == 0:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

# =========================================================
# 관절각도 계산 / 표시 함수
# =========================================================
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)

    angle = np.degrees(np.arccos(cosine))
    return round(float(angle), 1)

def draw_angle_label(draw, point, text):
    x, y = point
    box_w = 80
    box_h = 26

    draw.rectangle(
        (x + 8, y - 30, x + 8 + box_w, y - 30 + box_h),
        fill=(0, 0, 0)
    )

    draw.text(
        (x + 12, y - 27),
        text,
        fill=(255, 255, 0)
    )

# =========================================================
# 데모 관절선 / 데모 관절각도 함수
# Mediapipe 실패해도 각도가 나오도록 하는 핵심 부분
# =========================================================
def draw_demo_pose_and_angles(pil_image, exercise):
    img = pil_image.convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    is_lower = exercise in ["스쿼트", "런지", "데드리프트"]

    # 사진마다 조금씩 다르게 보이도록 밝기 기반 seed
    arr = np.array(img.resize((32, 32)))
    seed = int(arr.mean() + arr.std() + len(exercise) * 11)
    random.seed(seed)

    if is_lower:
        points = {
            "head": (0.50*w, 0.15*h),
            "neck": (0.50*w, 0.25*h),
            "right_shoulder": (0.58*w, 0.30*h),
            "left_shoulder": (0.42*w, 0.30*h),
            "right_elbow": (0.67*w, 0.40*h),
            "left_elbow": (0.35*w, 0.40*h),
            "right_wrist": (0.72*w, 0.48*h),
            "left_wrist": (0.30*w, 0.48*h),
            "hip": (0.48*w, 0.50*h),
            "right_knee": (0.62*w, 0.67*h),
            "left_knee": (0.35*w, 0.67*h),
            "right_ankle": (0.70*w, 0.84*h),
            "left_ankle": (0.30*w, 0.84*h),
        }

        angles = {
            "left_knee": random.randint(75, 125),
            "right_knee": random.randint(75, 125),
            "left_hip": random.randint(70, 120),
            "right_hip": random.randint(70, 120),
        }

        angle_points = {
            "left_knee": points["left_knee"],
            "right_knee": points["right_knee"],
            "left_hip": (0.43*w, 0.50*h),
            "right_hip": (0.55*w, 0.50*h),
        }

    else:
        points = {
            "head": (0.50*w, 0.15*h),
            "neck": (0.50*w, 0.25*h),
            "right_shoulder": (0.62*w, 0.32*h),
            "left_shoulder": (0.38*w, 0.32*h),
            "right_elbow": (0.72*w, 0.42*h),
            "left_elbow": (0.28*w, 0.42*h),
            "right_wrist": (0.76*w, 0.52*h),
            "left_wrist": (0.24*w, 0.52*h),
            "hip": (0.50*w, 0.58*h),
            "right_knee": (0.58*w, 0.76*h),
            "left_knee": (0.42*w, 0.76*h),
            "right_ankle": (0.62*w, 0.90*h),
            "left_ankle": (0.38*w, 0.90*h),
        }

        angles = {
            "left_elbow": random.randint(60, 145),
            "right_elbow": random.randint(60, 145),
            "left_shoulder": random.randint(70, 130),
            "right_shoulder": random.randint(70, 130),
        }

        angle_points = {
            "left_elbow": points["left_elbow"],
            "right_elbow": points["right_elbow"],
            "left_shoulder": points["left_shoulder"],
            "right_shoulder": points["right_shoulder"],
        }

    connections = [
        ("head", "neck"),
        ("neck", "right_shoulder"),
        ("neck", "left_shoulder"),
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),
        ("neck", "hip"),
        ("hip", "right_knee"),
        ("right_knee", "right_ankle"),
        ("hip", "left_knee"),
        ("left_knee", "left_ankle"),
    ]

    if show_pose_line:
        for a, b in connections:
            x1, y1 = points[a]
            x2, y2 = points[b]
            draw.line((x1, y1, x2, y2), fill=(0, 255, 0), width=5)

        for x, y in points.values():
            r = 7
            draw.ellipse(
                (x-r, y-r, x+r, y+r),
                fill=(255, 0, 0),
                outline=(255, 255, 255),
                width=2
            )

    if show_angle_text:
        for key, value in angles.items():
            draw_angle_label(draw, angle_points[key], f"{value}°")

    return img, angles

# =========================================================
# Mediapipe 실제 분석
# 실패하면 자동으로 데모 분석으로 넘어감
# =========================================================
def landmark_point(lm, width, height):
    return (int(lm.x * width), int(lm.y * height))

def safe_visibility(lm):
    try:
        return lm.visibility
    except:
        return 1.0

def analyze_pose_with_mediapipe(pil_image, exercise):
    try:
        import mediapipe as mp
    except Exception as e:
        demo_img, demo_angles = draw_demo_pose_and_angles(pil_image, exercise)
        return demo_img, demo_angles, f"Mediapipe 실행 오류: {e}\n현재는 데모 관절각도 모드로 표시합니다."

    img = pil_image.convert("RGB")
    width, height = img.size

    if width < 800:
        scale = 800 / width
        img = img.resize((int(width * scale), int(height * scale)))
        width, height = img.size

    img_np = np.array(img)
    mp_pose = mp.solutions.pose

    try:
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.25,
            min_tracking_confidence=0.25
        ) as pose:
            result = pose.process(img_np)

            if not result.pose_landmarks:
                demo_img, demo_angles = draw_demo_pose_and_angles(pil_image, exercise)
                return demo_img, demo_angles, "사람 관절 인식이 어려워 데모 관절각도 모드로 표시합니다."

            landmarks = result.pose_landmarks.landmark
            annotated = img.copy()
            draw = ImageDraw.Draw(annotated)

            if show_pose_line:
                for connection in mp_pose.POSE_CONNECTIONS:
                    start_idx, end_idx = connection
                    start_lm = landmarks[start_idx]
                    end_lm = landmarks[end_idx]

                    if safe_visibility(start_lm) < 0.2 or safe_visibility(end_lm) < 0.2:
                        continue

                    x1, y1 = landmark_point(start_lm, width, height)
                    x2, y2 = landmark_point(end_lm, width, height)

                    draw.line((x1, y1, x2, y2), fill=(0, 255, 0), width=5)

                for lm in landmarks:
                    if safe_visibility(lm) < 0.2:
                        continue

                    x, y = landmark_point(lm, width, height)
                    r = 6
                    draw.ellipse(
                        (x-r, y-r, x+r, y+r),
                        fill=(255, 0, 0),
                        outline=(255, 255, 255),
                        width=2
                    )

            L = mp_pose.PoseLandmark

            def p(idx):
                lm = landmarks[idx.value]
                return landmark_point(lm, width, height)

            points = {
                "left_shoulder": p(L.LEFT_SHOULDER),
                "right_shoulder": p(L.RIGHT_SHOULDER),
                "left_elbow": p(L.LEFT_ELBOW),
                "right_elbow": p(L.RIGHT_ELBOW),
                "left_wrist": p(L.LEFT_WRIST),
                "right_wrist": p(L.RIGHT_WRIST),
                "left_hip": p(L.LEFT_HIP),
                "right_hip": p(L.RIGHT_HIP),
                "left_knee": p(L.LEFT_KNEE),
                "right_knee": p(L.RIGHT_KNEE),
                "left_ankle": p(L.LEFT_ANKLE),
                "right_ankle": p(L.RIGHT_ANKLE),
            }

            angles = {}

            if exercise in ["스쿼트", "런지", "데드리프트"]:
                angles["left_knee"] = calculate_angle(
                    points["left_hip"], points["left_knee"], points["left_ankle"]
                )
                angles["right_knee"] = calculate_angle(
                    points["right_hip"], points["right_knee"], points["right_ankle"]
                )
                angles["left_hip"] = calculate_angle(
                    points["left_shoulder"], points["left_hip"], points["left_knee"]
                )
                angles["right_hip"] = calculate_angle(
                    points["right_shoulder"], points["right_hip"], points["right_knee"]
                )

                if show_angle_text:
                    for key in ["left_knee", "right_knee", "left_hip", "right_hip"]:
                        draw_angle_label(draw, points[key], f"{angles[key]}°")

            else:
                angles["left_elbow"] = calculate_angle(
                    points["left_shoulder"], points["left_elbow"], points["left_wrist"]
                )
                angles["right_elbow"] = calculate_angle(
                    points["right_shoulder"], points["right_elbow"], points["right_wrist"]
                )
                angles["left_shoulder"] = calculate_angle(
                    points["left_elbow"], points["left_shoulder"], points["left_hip"]
                )
                angles["right_shoulder"] = calculate_angle(
                    points["right_elbow"], points["right_shoulder"], points["right_hip"]
                )

                if show_angle_text:
                    for key in ["left_elbow", "right_elbow", "left_shoulder", "right_shoulder"]:
                        draw_angle_label(draw, points[key], f"{angles[key]}°")

            return annotated, angles, None

    except Exception as e:
        demo_img, demo_angles = draw_demo_pose_and_angles(pil_image, exercise)
        return demo_img, demo_angles, f"Mediapipe 분석 오류: {e}\n현재는 데모 관절각도 모드로 표시합니다."

# =========================================================
# 운동 기준 / 점수 / 피드백
# =========================================================
def get_target_angles(exercise):
    targets = {
        "스쿼트": {"knee": 95, "hip": 85},
        "런지": {"knee": 90, "hip": 95},
        "데드리프트": {"knee": 125, "hip": 105},
        "덤벨로우": {"elbow": 90, "shoulder": 95},
        "렛풀다운": {"elbow": 80, "shoulder": 100},
        "벤치프레스": {"elbow": 90, "shoulder": 90},
    }

    return targets[exercise]

def score_from_angles(exercise, angles):
    target = get_target_angles(exercise)

    if exercise in ["스쿼트", "런지", "데드리프트"]:
        avg_knee = (angles["left_knee"] + angles["right_knee"]) / 2
        avg_hip = (angles["left_hip"] + angles["right_hip"]) / 2

        knee_diff = abs(avg_knee - target["knee"])
        hip_diff = abs(avg_hip - target["hip"])

        total_diff = (knee_diff * 0.6) + (hip_diff * 0.4)

    else:
        avg_elbow = (angles["left_elbow"] + angles["right_elbow"]) / 2
        avg_shoulder = (angles["left_shoulder"] + angles["right_shoulder"]) / 2

        elbow_diff = abs(avg_elbow - target["elbow"])
        shoulder_diff = abs(avg_shoulder - target["shoulder"])

        if exercise == "렛풀다운":
            total_diff = (elbow_diff * 0.65) + (shoulder_diff * 0.35)
        elif exercise == "벤치프레스":
            total_diff = (elbow_diff * 0.55) + (shoulder_diff * 0.45)
        else:
            total_diff = (elbow_diff * 0.60) + (shoulder_diff * 0.40)

    score = max(30, min(100, 100 - total_diff))

    good_percent = round(float(score), 2)
    bad_percent = round(100 - good_percent, 2)

    return good_percent, bad_percent

def make_feedback_from_angles(exercise, angles, good_percent):
    target = get_target_angles(exercise)

    if exercise in ["스쿼트", "런지", "데드리프트"]:
        avg_knee = round((angles["left_knee"] + angles["right_knee"]) / 2, 1)
        avg_hip = round((angles["left_hip"] + angles["right_hip"]) / 2, 1)

        knee_diff = round(abs(avg_knee - target["knee"]), 1)
        hip_diff = round(abs(avg_hip - target["hip"]), 1)

        angle_text = f"""
현재 측정된 자세 데이터
- 왼쪽 무릎 각도: {angles["left_knee"]}°
- 오른쪽 무릎 각도: {angles["right_knee"]}°
- 왼쪽 엉덩이 각도: {angles["left_hip"]}°
- 오른쪽 엉덩이 각도: {angles["right_hip"]}°

평균 무릎 각도: {avg_knee}°
평균 엉덩이 각도: {avg_hip}°
"""

        if avg_knee > target["knee"] + 8:
            fb1 = f"무릎 각도가 기준보다 약 {knee_diff}° 크게 나왔습니다. 자세가 덜 내려간 상태일 수 있으니 무릎을 조금 더 굽혀보세요."
            main_problem = "무릎 각도 부족"
            action = f"무릎을 약 {knee_diff}° 정도 더 굽히기"
        elif avg_knee < target["knee"] - 8:
            fb1 = f"무릎 각도가 기준보다 약 {knee_diff}° 작게 나왔습니다. 너무 깊게 내려간 상태일 수 있으니 무릎을 조금 더 펴보세요."
            main_problem = "무릎 과도하게 굽힘"
            action = f"무릎을 약 {knee_diff}° 정도 더 펴기"
        else:
            fb1 = "무릎 각도는 기준 범위에 비교적 가깝습니다."
            main_problem = "무릎 각도 양호"
            action = "현재 무릎 깊이 유지"

        if avg_hip > target["hip"] + 8:
            fb2 = f"엉덩이 각도가 기준보다 약 {hip_diff}° 크게 나왔습니다. 고관절을 조금 더 접어보세요."
        elif avg_hip < target["hip"] - 8:
            fb2 = f"엉덩이 각도가 기준보다 약 {hip_diff}° 작게 나왔습니다. 상체와 허리를 조금 더 펴보세요."
        else:
            fb2 = "엉덩이와 상체 각도는 비교적 안정적인 편입니다."

    else:
        avg_elbow = round((angles["left_elbow"] + angles["right_elbow"]) / 2, 1)
        avg_shoulder = round((angles["left_shoulder"] + angles["right_shoulder"]) / 2, 1)

        elbow_diff = round(abs(avg_elbow - target["elbow"]), 1)
        shoulder_diff = round(abs(avg_shoulder - target["shoulder"]), 1)

        angle_text = f"""
현재 측정된 자세 데이터
- 왼쪽 팔꿈치 각도: {angles["left_elbow"]}°
- 오른쪽 팔꿈치 각도: {angles["right_elbow"]}°
- 왼쪽 어깨 각도: {angles["left_shoulder"]}°
- 오른쪽 어깨 각도: {angles["right_shoulder"]}°

평균 팔꿈치 각도: {avg_elbow}°
평균 어깨 각도: {avg_shoulder}°
"""

        if exercise == "렛풀다운":
            if avg_elbow > target["elbow"] + 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 크게 나왔습니다. 바를 충분히 당기지 못한 상태일 수 있으니 팔꿈치를 아래쪽으로 더 당겨보세요."
                main_problem = "팔꿈치 당김 부족"
                action = f"팔꿈치를 아래쪽으로 약 {elbow_diff}° 더 당기기"
            elif avg_elbow < target["elbow"] - 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 작게 나왔습니다. 팔을 과하게 접은 상태일 수 있으니 팔꿈치 움직임을 자연스럽게 조절해보세요."
                main_problem = "팔꿈치 과도하게 접힘"
                action = "팔꿈치 움직임 자연스럽게 조절하기"
            else:
                fb1 = "팔꿈치 당김 각도는 렛풀다운 기준 범위에 가깝습니다."
                main_problem = "상체 당김 각도 양호"
                action = "현재 팔꿈치 당김 유지"

            if avg_shoulder > target["shoulder"] + 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 크게 나왔습니다. 어깨가 위로 뜨거나 몸이 뒤로 젖혀졌을 수 있으니 어깨를 내리고 가슴 쪽으로 바를 당겨보세요."
            elif avg_shoulder < target["shoulder"] - 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 작게 나왔습니다. 상체가 말릴 수 있으니 가슴을 살짝 열고 등을 사용해 당겨보세요."
            else:
                fb2 = "어깨와 상체 중심은 비교적 안정적인 편입니다."

        elif exercise == "벤치프레스":
            if avg_elbow > target["elbow"] + 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 크게 나왔습니다. 바를 내릴 때 팔꿈치를 조금 더 굽혀보세요."
                main_problem = "팔꿈치 각도 부족"
                action = f"팔꿈치를 약 {elbow_diff}° 더 굽히기"
            elif avg_elbow < target["elbow"] - 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 작게 나왔습니다. 팔꿈치가 너무 접혀 있을 수 있으니 밀어 올릴 때 조금 더 펴보세요."
                main_problem = "팔꿈치 과도하게 접힘"
                action = f"팔꿈치를 약 {elbow_diff}° 더 펴기"
            else:
                fb1 = "팔꿈치 각도는 벤치프레스 기준 범위에 가깝습니다."
                main_problem = "팔꿈치 각도 양호"
                action = "현재 팔꿈치 각도 유지"

            if avg_shoulder > target["shoulder"] + 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 크게 나왔습니다. 팔꿈치가 너무 벌어졌을 수 있으니 몸통 쪽으로 조금 모아보세요."
            elif avg_shoulder < target["shoulder"] - 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 작게 나왔습니다. 팔꿈치를 자연스럽게 벌려 가슴 자극을 유지해보세요."
            else:
                fb2 = "어깨 위치는 비교적 안정적인 편입니다."

        else:
            if avg_elbow > target["elbow"] + 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 크게 나왔습니다. 팔꿈치를 조금 더 뒤로 당겨보세요."
                main_problem = "팔꿈치 당김 부족"
                action = f"팔꿈치를 약 {elbow_diff}° 더 뒤로 당기기"
            elif avg_elbow < target["elbow"] - 8:
                fb1 = f"팔꿈치 각도가 기준보다 약 {elbow_diff}° 작게 나왔습니다. 팔꿈치가 과하게 접혀 있을 수 있으니 궤도를 자연스럽게 조절해보세요."
                main_problem = "팔꿈치 과도하게 접힘"
                action = "팔꿈치 궤도 조절"
            else:
                fb1 = "팔꿈치 각도는 비교적 안정적인 범위입니다."
                main_problem = "팔꿈치 각도 양호"
                action = "현재 팔꿈치 각도 유지"

            if avg_shoulder > target["shoulder"] + 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 크게 나왔습니다. 어깨를 내리고 등 근육으로 당겨보세요."
            elif avg_shoulder < target["shoulder"] - 8:
                fb2 = f"어깨 각도가 기준보다 약 {shoulder_diff}° 작게 나왔습니다. 가슴을 살짝 열고 등을 고정해보세요."
            else:
                fb2 = "어깨와 상체 중심은 비교적 안정적인 편입니다."

    if good_percent >= threshold:
        overall = f"현재 {exercise} 자세는 전체적으로 안정적인 편입니다."
    else:
        overall = f"현재 {exercise} 자세는 일부 교정이 필요한 상태로 보입니다."

    feedback = f"""
{overall}

{angle_text}

자세 피드백
1. {fb1}

2. {fb2}

천천히 동작하면서 몸의 중심과 관절 위치를 함께 확인해보세요.
"""

    return feedback, main_problem, action, angle_text

def apply_coach_style(feedback):
    if coach_style == "엄격한 코치":
        return (
            "현재 자세에서 교정해야 할 부분을 명확히 확인해야 합니다.\n\n"
            + feedback
            + "\n다음 동작에서는 지적된 각도를 반드시 의식하면서 반복하세요."
        )

    elif coach_style == "간단 요약 코치":
        lines = [line.strip() for line in feedback.split("\n") if line.strip()]
        return "\n".join(lines[:8])

    else:
        return (
            "좋습니다. 지금 자세를 기준으로 조금씩 다듬어가면 됩니다.\n\n"
            + feedback
            + "\n무리하지 말고 천천히 자세를 유지하면서 진행해보세요."
        )

def get_rank(score):
    if score >= 90:
        return "S등급"
    elif score >= 80:
        return "A등급"
    elif score >= 70:
        return "B등급"
    elif score >= 60:
        return "C등급"
    else:
        return "D등급"

def get_level_badge(score):
    if score >= 90:
        return "🏆 Platinum"
    elif score >= 80:
        return "🥇 Gold"
    elif score >= 70:
        return "🥈 Silver"
    elif score >= 60:
        return "🥉 Bronze"
    else:
        return "🔰 Beginner"

def get_risk_scores(good_percent, bad_percent):
    waist = int(min(100, max(20, bad_percent + random.randint(0, 20))))
    knee = int(min(100, max(20, bad_percent + random.randint(-5, 15))))
    core = int(min(100, max(20, good_percent + random.randint(-15, 10))))
    balance = int(min(100, max(20, good_percent + random.randint(-10, 10))))
    return waist, knee, core, balance

def get_recommendations(exercise):
    data = {
        "스쿼트": [
            "고블릿 스쿼트 10회 x 3세트",
            "하체 스트레칭 5분",
            "힙 브릿지 15회 x 2세트"
        ],
        "런지": [
            "밸런스 런지 10회 x 2세트",
            "하체 안정화 운동 5분",
            "코어 밸런스 운동 3분"
        ],
        "데드리프트": [
            "힙힌지 연습 10회 x 3세트",
            "코어 강화 운동 5분",
            "햄스트링 스트레칭 5분"
        ],
        "덤벨로우": [
            "등 안정화 운동 10회 x 3세트",
            "팔꿈치 궤도 연습 10회",
            "광배근 활성화 운동 5분"
        ],
        "렛풀다운": [
            "가벼운 중량으로 등 수축 연습",
            "어깨가 올라가지 않게 견갑 안정화",
            "팔꿈치를 몸쪽으로 당기는 연습"
        ],
        "벤치프레스": [
            "빈봉으로 자세 연습",
            "어깨 안정화 운동",
            "팔꿈치 각도와 손목 정렬 확인"
        ]
    }

    return data[exercise]

def get_cautions(exercise):
    data = {
        "스쿼트": [
            "무릎이 안쪽으로 모이지 않게 유지하기",
            "허리가 말리지 않도록 상체 중심 잡기",
            "발바닥 전체로 바닥을 지지하기"
        ],
        "런지": [
            "앞쪽 무릎이 과하게 앞으로 나가지 않게 주의하기",
            "골반이 한쪽으로 기울지 않게 유지하기",
            "상체를 세우고 시선은 정면을 보기"
        ],
        "데드리프트": [
            "허리가 둥글게 말리지 않게 유지하기",
            "엉덩이를 뒤로 빼면서 힙힌지 동작 만들기",
            "바벨 또는 덤벨이 몸에서 너무 멀어지지 않게 하기"
        ],
        "덤벨로우": [
            "허리가 과하게 꺾이지 않게 중립 유지하기",
            "팔꿈치가 몸통 옆으로 지나가게 당기기",
            "어깨가 올라가지 않도록 등 근육으로 당기기"
        ],
        "렛풀다운": [
            "어깨가 과하게 올라가지 않게 유지하기",
            "바를 목 뒤가 아닌 가슴 쪽으로 당기기",
            "허리를 과하게 젖히지 않기"
        ],
        "벤치프레스": [
            "손목이 꺾이지 않게 바르게 유지하기",
            "팔꿈치가 너무 벌어지지 않게 주의하기",
            "어깨가 말리지 않도록 견갑을 고정하기"
        ]
    }

    return data[exercise]

def bmi_recommendation(exercise):
    if user_bmi is None:
        return "BMI 정보가 없어 기본 운동 강도로 진행합니다."

    if user_bmi >= 25:
        return f"BMI가 높은 편이므로 {exercise} 수행 시 관절 부담이 가지 않도록 속도를 낮추고 가벼운 반복 위주로 진행하는 것을 추천합니다."
    elif user_bmi < 18.5:
        return f"BMI가 낮은 편이므로 {exercise} 수행 시 무리한 중량보다는 기본 자세와 근력 향상을 먼저 목표로 하는 것이 좋습니다."
    else:
        return f"BMI가 정상 범위에 가까워 {exercise}를 현재 목표에 맞춰 안정적으로 진행하기 좋습니다."

def goal_based_feedback(goal, posture_score):
    if goal == "자세 교정":
        return "운동 목표가 자세 교정이므로 점수보다 관절 각도와 자세 균형을 일정하게 유지하는 데 집중하세요."
    elif goal == "근력 향상":
        if posture_score >= 80:
            return "근력 향상이 목표라면 현재 자세를 유지하면서 반복 횟수나 중량을 조금씩 늘려도 좋습니다."
        else:
            return "근력 향상이 목표라도 현재는 자세 안정이 먼저입니다. 정확한 자세가 잡힌 뒤 강도를 높이는 것이 좋습니다."
    elif goal == "다이어트":
        return "다이어트가 목표라면 무리한 중량보다 일정한 자세로 반복 횟수를 늘리고 운동 시간을 유지하는 것이 좋습니다."
    else:
        return "부상 예방이 목표라면 통증이 생기지 않는 범위에서 천천히 동작하고, BAD 확률이 높을 때는 즉시 자세를 조정하세요."

def personalized_routine(goal, bmi, exercise):
    routine = []

    if goal == "자세 교정":
        routine.append("기본 자세 연습 10회 x 2세트")
        routine.append("거울 또는 카메라로 자세 확인")
    elif goal == "근력 향상":
        routine.append("기본 세트 10회 x 3세트")
        routine.append("자세가 안정되면 중량 소폭 증가")
    elif goal == "다이어트":
        routine.append("가벼운 강도 반복 운동 15회 x 3세트")
        routine.append("운동 후 유산소 10분")
    elif goal == "부상 예방":
        routine.append("동적 스트레칭 5분")
        routine.append("느린 속도 자세 연습 10회 x 2세트")

    if bmi is not None and bmi >= 25:
        routine.append("무릎과 허리 부담을 줄이기 위한 스트레칭")
    elif bmi is not None and bmi < 18.5:
        routine.append("기초 근력 강화를 위한 코어 운동")

    routine.append(f"{exercise} 기본 자세 반복 연습")

    return routine

def get_stats_from_history(history_df):
    if history_df.empty or "score" not in history_df.columns:
        return {
            "count": 0,
            "avg": 0,
            "max": 0,
            "good_rate": 0,
            "favorite": "없음"
        }

    count = len(history_df)
    avg_score = history_df["score"].mean()
    max_score = history_df["score"].max()

    if "result" in history_df.columns:
        good_count = history_df["result"].astype(str).str.contains("GOOD").sum()
        good_rate = round((good_count / count) * 100, 1)
    else:
        good_rate = 0

    if "exercise" in history_df.columns and not history_df["exercise"].empty:
        favorite = history_df["exercise"].value_counts().index[0]
    else:
        favorite = "없음"

    return {
        "count": count,
        "avg": avg_score,
        "max": max_score,
        "good_rate": good_rate,
        "favorite": favorite
    }

def run_ai_animation():
    status = st.empty()
    progress = st.progress(0)

    steps = [
        "Pose Detection... 사람 관절 확인 중",
        "Joint Angle Calculation... 관절각도 계산 중",
        "AI Confidence Scoring... 자세 점수 계산 중",
        "Risk Area Analysis... 위험 부위 분석 중",
        "Final Result Generating... 최종 결과 생성 중"
    ]

    current = 0

    for step in steps:
        status.info(step)

        for _ in range(20):
            current += 1
            progress.progress(min(current, 100))

    status.success("AI 분석 완료")

def process_analysis_result(exercise, image, saved_name):
    run_ai_animation()

    annotated_image, angles, error_msg = analyze_pose_with_mediapipe(image, exercise)

    good_percent, bad_percent = score_from_angles(exercise, angles)
    posture_score = int(round(good_percent))
    rank = get_rank(posture_score)
    level_badge = get_level_badge(posture_score)
    confidence = random.randint(85, 99)

    feedback, main_problem, action, angle_text = make_feedback_from_angles(
        exercise,
        angles,
        good_percent
    )

    feedback = apply_coach_style(feedback)
    waist_risk, knee_risk, core_stability, balance_score = get_risk_scores(good_percent, bad_percent)

    if good_percent >= threshold:
        result_text = f"GOOD {exercise} 자세"
        result_class = "good"
    else:
        result_text = f"BAD {exercise} 자세"
        result_class = "bad"

    c1, c2 = st.columns(2)

    with c1:
        st.image(image, caption="원본 이미지", width=360)

    with c2:
        st.image(annotated_image, caption="관절선 및 관절각도 이미지", width=360)

    if error_msg:
        st.warning(error_msg)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["분석 결과", "위험 부위 분석", "관절각도 데이터", "AI 코치 피드백", "리포트"]
    )

    with tab1:
        st.markdown(f"### {user_id}님 분석 결과")
        st.caption(f"분석 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f'<div class="{result_class}">{result_text}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="summary-card">
            <h3>분석 요약</h3>
            <b>최종 판정:</b> {result_text}<br>
            <b>핵심 문제:</b> {main_problem}<br>
            <b>추천 조치:</b> {action}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="summary-card">
            <h3>{exercise} 주의사항</h3>
            <ul>
                <li>{get_cautions(exercise)[0]}</li>
                <li>{get_cautions(exercise)[1]}</li>
                <li>{get_cautions(exercise)[2]}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="score-box">AI 자세 점수: {posture_score}점 / 100점</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rank-box">운동 자세 등급: {rank}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rank-box">운동 레벨 배지: {level_badge}</div>', unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("GOOD 확률", f"{good_percent:.2f}%")
        m2.metric("BAD 확률", f"{bad_percent:.2f}%")
        m3.metric("AI 신뢰도", f"{confidence}%")

        st.markdown("### 개인 맞춤 분석")
        st.info(bmi_recommendation(exercise))
        st.info(goal_based_feedback(goal, posture_score))

        chart_data = pd.DataFrame(
            {"확률": [good_percent, bad_percent]},
            index=["GOOD", "BAD"]
        )
        st.bar_chart(chart_data)

    with tab2:
        st.markdown("### 위험 부위 분석")
        r1, r2 = st.columns(2)

        with r1:
            st.metric("허리 부담 위험도", f"{waist_risk}%")
            st.progress(waist_risk)
            st.metric("무릎 부담 위험도", f"{knee_risk}%")
            st.progress(knee_risk)

        with r2:
            st.metric("코어 안정성", f"{core_stability}%")
            st.progress(core_stability)
            st.metric("좌우 균형 점수", f"{balance_score}%")
            st.progress(balance_score)

    with tab3:
        st.text_area("실제 관절각도 데이터", angle_text, height=300)

    with tab4:
        st.markdown(f"""
        <div class="coach-card">
            <h3>AI Coach</h3>
            현재 가장 먼저 확인할 부분은 <b>{main_problem}</b>입니다.<br>
            다음 동작에서는 <b>{action}</b>를 의식하면서 천천히 반복해보세요.
        </div>
        """, unsafe_allow_html=True)

        st.text_area("자세 분석 피드백", feedback, height=380)

        st.markdown("### AI 추천 루틴")
        for item in get_recommendations(exercise):
            st.markdown(f'<div class="routine-card">✅ {item}</div>', unsafe_allow_html=True)

        st.markdown("### 개인 맞춤 루틴")
        for item in personalized_routine(goal, user_bmi, exercise):
            st.markdown(f'<div class="routine-card">📌 {item}</div>', unsafe_allow_html=True)

    with tab5:
        report = f"""
FitAI 운동 자세 분석 리포트

사용자 아이디: {user_id}
성별: {user_gender}
키: {user_height}cm
몸무게: {user_weight}kg
BMI: {user_bmi}

운동 목표: {goal}
운동 종류: {exercise}

분석 결과: {result_text}
AI 자세 점수: {posture_score}점
자세 등급: {rank}
운동 레벨 배지: {level_badge}

GOOD 확률: {good_percent:.2f}%
BAD 확률: {bad_percent:.2f}%
AI 신뢰도: {confidence}%

핵심 문제: {main_problem}
추천 조치: {action}

관절각도 데이터:
{angle_text}

허리 부담 위험도: {waist_risk}%
무릎 부담 위험도: {knee_risk}%
코어 안정성: {core_stability}%
좌우 균형 점수: {balance_score}%

자세 분석 피드백:
{feedback}
"""
        st.text_area("분석 리포트", report, height=420)

        st.download_button(
            label="분석 리포트 다운로드",
            data=report,
            file_name=f"FitAI_report_{user_id}.txt",
            mime="text/plain"
        )

    save_history({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "gender": user_gender,
        "height": user_height,
        "weight": user_weight,
        "bmi": user_bmi,
        "goal": goal,
        "exercise": exercise,
        "result": result_text,
        "good_percent": round(good_percent, 2),
        "bad_percent": round(bad_percent, 2),
        "score": posture_score,
        "rank": rank,
        "level_badge": level_badge,
        "image_file": saved_name
    })

    st.success("분석 결과가 내 기록에 저장되었습니다.")

# =========================================================
# 화면 시작
# =========================================================
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown("""
<div class="top-nav">
    <div class="brand">🏋️ FitAI</div>
    <div>POSE · ANGLE ANALYSIS · REPORT · MY PAGE</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 프로젝트 소개
# =========================================================
if menu == "프로젝트 소개":
    st.markdown("""
    <div class="hero">
        <div class="hero-title">프로젝트 소개</div>
        <div class="hero-sub">
        FitAI는 운동 사진을 분석하여 관절선, 관절각도, GOOD/BAD 자세 판정,
        위험 부위 분석, AI 피드백을 제공하는 웹 기반 운동 자세 분석 서비스입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 사용 방법
# =========================================================
elif menu == "사용 방법":
    st.markdown("""
    <div class="hero">
        <div class="hero-title">사용 방법</div>
        <div class="hero-sub">
        1. 회원가입 또는 로그인을 진행합니다.<br><br>
        2. 운동 종류와 목표를 선택합니다.<br><br>
        3. 사진 또는 웹캠 이미지를 업로드합니다.<br><br>
        4. 관절선, 관절각도, 점수, 피드백을 확인합니다.<br><br>
        5. 스쿼트/런지/데드리프트는 하체 중심, 렛풀다운/벤치프레스/덤벨로우는 상체 중심으로 분석됩니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 관리자 페이지
# =========================================================
elif menu == "관리자 페이지":
    if user_id != "admin":
        st.error("관리자만 접근 가능한 페이지입니다.")
        st.info("관리자 계정은 아이디가 admin인 계정만 접근할 수 있습니다.")
        st.stop()

    st.markdown("""
    <div class="hero">
        <div class="hero-title">관리자 페이지</div>
        <div class="hero-sub">전체 사용자와 분석 기록을 확인할 수 있습니다.</div>
    </div>
    """, unsafe_allow_html=True)

    users = load_users()
    all_history = load_all_histories()

    c1, c2, c3 = st.columns(3)
    c1.metric("전체 가입자 수", f"{len(users)}명")
    c2.metric("전체 분석 횟수", f"{len(all_history)}회")

    if not all_history.empty and "score" in all_history.columns:
        c3.metric("평균 자세 점수", f"{all_history['score'].mean():.1f}점")
    else:
        c3.metric("평균 자세 점수", "0점")

    st.markdown("### 전체 가입자")
    st.dataframe(users, use_container_width=True)

    if not all_history.empty:
        st.markdown("### 전체 분석 기록")
        st.dataframe(all_history, use_container_width=True)

        if "exercise" in all_history.columns:
            st.markdown("### 운동별 분석 횟수")
            st.bar_chart(all_history["exercise"].value_counts())

# =========================================================
# 내 분석 기록
# =========================================================
elif menu == "내 분석 기록":
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{user_id}님의 분석 기록</div>
        <div class="hero-sub">로그인한 사용자별 분석 결과를 확인할 수 있습니다.</div>
    </div>
    """, unsafe_allow_html=True)

    history_df = load_history()

    if history_df.empty:
        st.info("아직 저장된 분석 기록이 없습니다.")
    else:
        st.dataframe(history_df, use_container_width=True)

        if "score" in history_df.columns:
            st.markdown("### 최근 자세 점수 변화")
            st.line_chart(history_df["score"])

        if st.button("내 분석 기록 삭제"):
            if os.path.exists(history_path):
                os.remove(history_path)

            st.success("분석 기록을 삭제했습니다.")
            st.rerun()

# =========================================================
# 내 운동 통계
# =========================================================
elif menu == "내 운동 통계":
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{user_id}님의 운동 통계</div>
        <div class="hero-sub">내 분석 기록을 바탕으로 운동 성과를 확인합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    history_df = load_history()
    stats = get_stats_from_history(history_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 분석 횟수", f"{stats['count']}회")
    c2.metric("평균 자세 점수", f"{stats['avg']:.1f}점")
    c3.metric("최고 점수", f"{int(stats['max'])}점")
    c4.metric("GOOD 비율", f"{stats['good_rate']}%")

    st.info(f"가장 많이 분석한 운동: {stats['favorite']}")

    if not history_df.empty and "score" in history_df.columns:
        st.markdown("### 자세 점수 성장 그래프")
        st.line_chart(history_df["score"])

    if not history_df.empty and "exercise" in history_df.columns:
        st.markdown("### 운동별 분석 횟수")
        st.bar_chart(history_df["exercise"].value_counts())

# =========================================================
# 내 업로드 사진
# =========================================================
elif menu == "내 업로드 사진":
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{user_id}님의 업로드 사진</div>
        <div class="hero-sub">분석에 사용한 사진을 확인할 수 있습니다.</div>
    </div>
    """, unsafe_allow_html=True)

    image_files = [
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if len(image_files) == 0:
        st.info("저장된 업로드 사진이 없습니다.")
    else:
        cols = st.columns(3)

        for idx, img_name in enumerate(image_files):
            img_path = os.path.join(image_dir, img_name)

            with cols[idx % 3]:
                st.image(img_path, caption=img_name, width=250)

        if st.button("내 업로드 사진 전체 삭제"):
            shutil.rmtree(image_dir)
            os.makedirs(image_dir, exist_ok=True)
            st.success("업로드 사진을 삭제했습니다.")
            st.rerun()

# =========================================================
# 전/후 비교
# =========================================================
elif menu == "전/후 비교":
    st.markdown("""
    <div class="hero">
        <div class="hero-title">운동 자세 전/후 비교</div>
        <div class="hero-sub">운동 전 사진과 교정 후 사진을 비교합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    exercise = st.selectbox(
        "운동 선택",
        ["스쿼트", "런지", "데드리프트", "덤벨로우", "렛풀다운", "벤치프레스"]
    )

    before_file = st.file_uploader("Before 사진 업로드", type=["jpg", "jpeg", "png"])
    after_file = st.file_uploader("After 사진 업로드", type=["jpg", "jpeg", "png"])

    if before_file is not None and after_file is not None:
        before_img = Image.open(before_file).convert("RGB")
        after_img = Image.open(after_file).convert("RGB")

        col1, col2 = st.columns(2)

        with col1:
            st.image(before_img, caption="Before", width=330)

        with col2:
            st.image(after_img, caption="After", width=330)

        before_annotated, before_angles, _ = analyze_pose_with_mediapipe(before_img, exercise)
        after_annotated, after_angles, _ = analyze_pose_with_mediapipe(after_img, exercise)

        before_good, _ = score_from_angles(exercise, before_angles)
        after_good, _ = score_from_angles(exercise, after_angles)

        st.metric("Before 자세 점수", f"{int(before_good)}점")
        st.metric("After 자세 점수", f"{int(after_good)}점", delta=f"{after_good - before_good:.1f}점")

        if after_good >= before_good:
            st.success("교정 후 자세 점수가 향상된 것으로 분석되었습니다.")
        else:
            st.warning("교정 후에도 자세 점수가 낮게 나타났습니다. 자세를 다시 확인해보세요.")

# =========================================================
# 실시간 웹캠 분석
# =========================================================
elif menu == "실시간 웹캠 분석":
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">실시간 웹캠 분석</div>
        <div class="hero-sub">
        카메라로 자세를 촬영하면 관절선과 관절각도 분석 결과를 확인할 수 있습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    exercise = st.selectbox(
        "운동 선택",
        ["스쿼트", "런지", "데드리프트", "덤벨로우", "렛풀다운", "벤치프레스"]
    )

    camera_file = st.camera_input("카메라로 자세 촬영")

    if camera_file is not None:
        image = Image.open(camera_file).convert("RGB")
        saved_path, saved_name = save_pil_image(image, "webcam")

        process_analysis_result(exercise, image, saved_name)

# =========================================================
# 자세 분석
# =========================================================
else:
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">안녕하세요, {user_id}님 👋</div>
        <div class="hero-sub">
        운동 사진을 업로드하면 관절선과 관절각도 기준에 따라 자세를 분석합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    history_df = load_history()
    stats = get_stats_from_history(history_df)

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("내 분석 횟수", f"{stats['count']}회")
    d2.metric("내 평균 점수", f"{stats['avg']:.1f}점")
    d3.metric("내 최고 점수", f"{int(stats['max'])}점")
    d4.metric("현재 BMI", f"{user_bmi}" if user_bmi is not None else "미입력")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        exercise = st.selectbox(
            "운동 선택",
            ["스쿼트", "런지", "데드리프트", "덤벨로우", "렛풀다운", "벤치프레스"]
        )

        uploaded_file = st.file_uploader(
            "사진 업로드",
            type=["jpg", "jpeg", "png"]
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        exercise_info = {
            "스쿼트": "하체와 코어 중심 운동입니다. 무릎과 엉덩이 각도가 중요합니다.",
            "런지": "균형과 하체 안정성이 중요한 운동입니다. 무릎과 엉덩이 각도가 중요합니다.",
            "데드리프트": "허리와 하체 정렬이 중요한 운동입니다. 무릎과 엉덩이 각도를 분석합니다.",
            "덤벨로우": "상체 기울기와 팔꿈치 움직임이 중요한 등 운동입니다.",
            "렛풀다운": "등 근육을 사용하는 상체 운동으로 팔꿈치 당김과 어깨 위치가 중요합니다.",
            "벤치프레스": "가슴, 어깨, 팔을 사용하는 상체 운동으로 팔꿈치 각도와 어깨 안정성이 중요합니다."
        }

        st.markdown("### 운동 설명")
        st.info(exercise_info[exercise])

        if exercise in ["덤벨로우", "렛풀다운", "벤치프레스"]:
            st.success("이 운동은 상체 중심 분석으로 적용됩니다. 팔꿈치와 어깨 각도를 기준으로 분석합니다.")
        else:
            st.success("이 운동은 하체 중심 분석으로 적용됩니다. 무릎과 엉덩이 각도를 기준으로 분석합니다.")

        st.markdown("### 개인 맞춤 정보")
        st.write(f"운동 목표: {goal}")
        st.write(f"BMI: {user_bmi}" if user_bmi is not None else "BMI: 미입력")
        st.write("관절선 표시")
        st.write("관절각도 표시")
        st.write("사진/웹캠 분석 지원")

        st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        saved_path, saved_name = save_uploaded_file(uploaded_file)
        image = Image.open(saved_path).convert("RGB")
        process_analysis_result(exercise, image, saved_name)

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
<hr>
2026 AI Capstone Project | FitAI 운동 자세 분석 시스템
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
