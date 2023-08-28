# ultralytics에서 YOLO 모델 학습시키기
from ultralytics import YOLO

# 스크립트가 직접 실행될 때만 함수 안의 내용을 실행하기
if __name__ == "__main__" :
    model = YOLO("yolov8m.pt") # YOLO를 사용해서 ""안의 이름을 가진 모델을 불러오거나 생성한다.
    model.train(data="car_data.yaml", epochs=3, batch=64, lrf=0.025) # yaml 파일의 설정대로 YOLO 모델을 학습 시키기

    # model = YOLO("./runs/detect/train/weights/last.pt") # 이전 학습에서 얻은 가장 최근의 가중치 파일을 불러오기
    # model.train(resume=True) # 이전 학습에 중단된 시점부터 학습을 이어가기