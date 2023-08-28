import os # os 관련 기능 사용
import random
import shutil # 파일을 복사하거나 이동할 수 있는 모듈
from glob import glob # 경로명 패턴으로 파일을 찾을 수 있는 함수

# yolo 데이터셋을 분할하는 함수 정의
def split_yolo_dataset(path, images_path, labels_path, train_pct=0.8, val_pct=0.1):
    ## 필요한 디렉토리 생성, exist_ok=True으로 이미 디렉토리가 존재할시 오류가 발생하지 않도록 하기
    os.makedirs(os.path.join(path,"train/images"), exist_ok=True)
    os.makedirs(os.path.join(path,"train/labels"), exist_ok=True)
    
    os.makedirs(os.path.join(path,"test/images"), exist_ok=True)
    os.makedirs(os.path.join(path,"test/labels"), exist_ok=True)
    
    os.makedirs(os.path.join(path,"val/images"), exist_ok=True)
    os.makedirs(os.path.join(path,"val/labels"), exist_ok=True)

    ## 지정된 경로에서 png 파일 가져오기
    images = glob(images_path + "/*.png")
    ## 이미지 무작위로 섞기
    random.shuffle(images)
    ## 전체 이미지 데이터를 train, val, test로 나누기 위해 필요한 이미지 수 계산하기
    num_images = len(images)
    num_train = int(num_images * train_pct)
    num_val = int(num_images * val_pct)
    num_test = num_images - (num_train + num_val)

    ## 섞인 이미지 목록을 train, val, test 세트로 분할하기
    train_imgs = images[:num_train]
    val_imgs = images[num_train:num_train + num_val]
    test_imgs = images[num_train + num_val:]

    ## 각 세트에 대해 이미지와 레이블 파일을 train, val, test 디렉토리로 복사하기
    for train_img in train_imgs:
        basename = os.path.basename(train_img).split(".")[0]
        shutil.copy(train_img, os.path.join(path,"train/images"))
        shutil.copy(os.path.join(labels_path, basename + ".txt"), os.path.join(path,"train/labels"))

    for val_img in val_imgs:
        basename = os.path.basename(val_img).split(".")[0]
        shutil.copy(val_img, os.path.join(path,"val/images"))
        shutil.copy(os.path.join(labels_path, basename + ".txt"), os.path.join(path,"val/labels"))

    for test_img in test_imgs:
        basename = os.path.basename(test_img).split(".")[0]
        shutil.copy(test_img, os.path.join(path,"test/images"))
        shutil.copy(os.path.join(labels_path, basename + ".txt"), os.path.join(path,"test/labels"))

if __name__ == "__main__":
    path = "/Users/dobby/Library/Mobile Documents/com~apple~CloudDocs/electronicsandcode/code/arcticfo111/ms_06team/ms_team_cardata/final_data_combination1/multi_car"
    images_path = os.path.join(path,"images")
    labels_path = os.path.join(path,"labels")

    train_pct = 0.85
    val_pct = 0.1
    split_yolo_dataset(path, images_path, labels_path, train_pct, val_pct)
