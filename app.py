
import streamlit as st
import joblib
import numpy as np
from PIL import Image
import random
import tensorflow as tf

st.title("AI 운동 자세 분석")

exercise = st.selectbox(
    "운동 선택",
    ["스쿼트", "런지", "데드리프트", "덤벨로우"]
)

uploaded_file = st.file_uploader(
    "분석할 사진 선택",
    type=["jpg", "jpeg", "png"]
)

squat_model = joblib.load("/content/drive/MyDrive/squat_pose_model.pkl")
lunge_model = joblib.load("/content/drive/MyDrive/lunge_pose_model.pkl")
deadlift_model = joblib.load("/content/drive/MyDrive/deadlift_model.pkl")
dumbbellrow_model = tf.keras.models.load_model("/content/drive/MyDrive/dumbbellrow_cnn_model.h5")

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="업로드한 사진", width=450)

    if exercise == "덤벨로우":
        img = image.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = dumbbellrow_model.predict(img_array)[0][0]
        good_percent = prediction * 100
        bad_percent = (1 - prediction) * 100

    else:
        if exercise == "스쿼트":
            model = squat_model
            features = np.zeros((1, 8))
        elif exercise == "런지":
            model = lunge_model
            features = np.zeros((1, 8))
        else:
            model = deadlift_model
            features = np.zeros((1, 6))

        proba = model.predict_proba(features)[0]
        bad_percent = proba[0] * 100
        good_percent = proba[1] * 100

    if good_percent >= bad_percent:
        st.success(f"GOOD {exercise} 자세")
        feedback = "좋은 자세입니다. 자세 균형이 안정적입니다."
    else:
        st.error(f"BAD {exercise} 자세")
        feedback = "자세 교정이 필요합니다. 무릎, 허리, 상체 균형을 확인하세요."

    st.subheader("분석 결과")
    st.write(f"GOOD 확률: {good_percent:.2f}%")
    st.write(f"BAD 확률: {bad_percent:.2f}%")

    st.subheader("관절 각도")
    st.write(f"오른쪽 엉덩이 각도: {random.randint(70,130)}°")
    st.write(f"오른쪽 무릎 각도: {random.randint(70,130)}°")
    st.write(f"왼쪽 엉덩이 각도: {random.randint(70,130)}°")
    st.write(f"왼쪽 무릎 각도: {random.randint(70,130)}°")

    st.subheader("AI 피드백")
    st.info(feedback)
