import os # 운영체제와 상호작용하기 위함
import glob  # 특정 패턴에 맞는 경로명 찾기 위함
import cv2 # 이미지 처리 및 cv 작업 위함
from ultralytics import YOLO # yolo 모델 가져오기

# 훈련된 yolo 모델의 가중치를 로드해서 객체 탐지 모델 인스턴스 생성
model = YOLO("/Users/dobby/Library/Mobile Documents/com~apple~CloudDocs/electronicsandcode/code/arcticfo111/ms_06team/car_plate_detection_yolov8/runs/detect/label_class4_multi_car_all/best.pt")
# 테스트 이미지가 있는 폴더 경로 찾기
data_path = "/Users/dobby/Library/Mobile Documents/com~apple~CloudDocs/electronicsandcode/code/arcticfo111/ms_06team/ms_team_cardata/final_data_combination1/multi_car/test/images"
# 테스트 이미지가 있는 폴더에서 모든 이미지 파일의 경로를 찾아서 리스트에 저장하기
data_path_list = glob.glob(os.path.join(data_path, "*.png"))
# 각각의 이미지 파일경로에 대해 for 문
for path in data_path_list :
    # 테스트 이미지의 경로에서 이미지 읽기
    image = cv2.imread(path)
    # 모델에서 클래스 이름 읽기
    names = model.names
    # 이미지에서 객체를 탐지하고, 결과 반환하기 
    results = model.predict(path, save=False, imgsz=640, conf=0.7)
    # 결과에서 바운딩 박스 정보 가져오기
    boxes = results[0].boxes
    results_info = boxes
    # 각 바운딩 박스의 클래스 번호, 바운딩 박스 신뢰도, 바운딩 박스 좌표 점수 가져오기
    cls_numbers = results_info.cls 
    conf_numbers = results_info.conf 
    box_xyxy = results_info.xyxy
    # 각 바운딩 박스의 클래스 번호, 바운딩 박스 신뢰도, 바운딩 박스 좌표에 대해 for 문
    for bbox, cls_idx, conf_idx in zip(box_xyxy, cls_numbers, conf_numbers) :
        class_number = int(cls_idx.item()) # 클래스 인덱스를 정수로 변환
        class_name = names[class_number] # 클래스 이름을 가져오기
        # 바운딩 박스의 왼쪽, 오른족 x, y 값 각각 가져오기
        x1 = int(bbox[0].item()) 
        y1 = int(bbox[1].item())
        x2 = int(bbox[2].item())
        y2 = int(bbox[3].item())
        print(class_name, class_number, x1,y1,x2,y2)
        # 이미지에 녹색 바운딩 박스 그리기
        rect = cv2.rectangle(image, (x1,y1), (x2,y2), (0,255,0), 2)
    # 바운딩 박스가 그려진 이미지 표시하기, 엔터로 다음 이미지 넘어가기
    cv2.imshow("test", rect)
    # q 키가 눌러지면 프로그램 종료하기
    if cv2.waitKey(0) == ord('q') :
        exit()