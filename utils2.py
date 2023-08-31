import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import YOLO
import re
import torch
from model import Model
import torch.nn.functional as F
import yaml
import argparse
import torch.utils.data
import torchvision.transforms as transforms
from PIL import Image
from sort.sort import *



device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# cudnn.benchmark = True
# cudnn.deterministic = True


def yaml_load(file='data.yaml', append_filename=False):

    with open(file, errors='ignore', encoding='utf-8') as f:
        s = f.read()  # string

        # Remove special characters
        if not s.isprintable():
            s = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010ffff]+', '', s)

        # Add YAML filename to dict and return
        return {**yaml.safe_load(s), 'yaml_file': str(file)} if append_filename else yaml.safe_load(s)


class ResizeNormalize(object):
    def __init__(self, size, interpolation=Image.BICUBIC):
        self.size = size
        self.interpolation = interpolation
        self.toTensor = transforms.ToTensor()

    def __call__(self, img):
        img = img.resize(self.size, self.interpolation)
        img = self.toTensor(img)
        img.sub_(0.5).div_(0.5)
        return img


class AttnLabelConverter(object):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    """ Convert between text-label and text-index """

    def __init__(self, character):
        # character (str): set of the possible characters.
        # [GO] for the start token of the attention decoder. [s] for end-of-sentence token.
        list_token = ['[GO]', '[s]']  # ['[s]','[UNK]','[PAD]','[GO]']
        list_character = list(character)
        self.character = list_token + list_character

        self.dict = {}
        for i, char in enumerate(self.character):
            # print(i, char)
            self.dict[char] = i

    def encode(self, text, batch_max_length=25):

        length = [len(s) + 1 for s in text]  # +1 for [s] at end of sentence.
        # batch_max_length = max(length) # this is not allowed for multi-gpu setting
        batch_max_length += 1
        # additional +1 for [GO] at first step. batch_text is padded with [GO] token after [s] token.
        batch_text = torch.LongTensor(len(text), batch_max_length + 1).fill_(0)
        for i, t in enumerate(text):
            text = list(t)
            text.append('[s]')
            text = [self.dict[char] for char in text]
            batch_text[i][1:1 + len(text)] = torch.LongTensor(text)  # batch_text[:, 0] = [GO] token
        return (batch_text.to(device), torch.IntTensor(length).to(device))

    def decode(self, text_index, length):
        """ convert text-index into text-label. """
        texts = []
        for index, l in enumerate(length):
            text = ''.join([self.character[i] for i in text_index[index, :]])
            texts.append(text)
        return texts



def preprocess_image(src):
    normalize = cv2.normalize(
        src, np.zeros((src.shape[0], src.shape[1])), 0, 255, cv2.NORM_MINMAX
    )
    denoise = cv2.fastNlMeansDenoisingColored(
        normalize, h=10, hColor=10, templateWindowSize=7, searchWindowSize=15
    )
    grayscale = cv2.cvtColor(denoise, cv2.COLOR_BGR2GRAY)
    threshold = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    pil_image = Image.fromarray(threshold)  # Convert to PIL Image
    return pil_image


def ocr(src):
    # Preprocess the image
    processed_image = preprocess_image(src)

    # Apply ResizeNormalize transform
    transform = ResizeNormalize((opt.imgW, opt.imgH))
    image_tensor = transform(processed_image)
    image_tensor = image_tensor.unsqueeze(0).to(device)

    # Perform OCR
    with torch.no_grad():
        length_for_pred = torch.IntTensor([opt.batch_max_length]).to(device)
        text_for_pred = torch.LongTensor(opt.batch_max_length + 1).fill_(0).to(device)
        preds = model(image_tensor, text_for_pred, is_train=False)
        _, preds_index = preds.max(2)
        preds_str = converter.decode(preds_index, torch.IntTensor([opt.batch_max_length]).to(device))

        preds_prob = F.softmax(preds, dim=2)
        preds_max_prob, _ = preds_prob.max(dim=2)

        for pred, pred_max_prob in zip(preds_str, preds_max_prob):
            pred_EOS = pred.find('[s]')
            pred = pred[:pred_EOS]
            pred_max_prob = pred_max_prob[:pred_EOS]
            confidence_score = pred_max_prob.cumprod(dim=0)[-1]
            #print(f'{pred:25s}\t{confidence_score:0.4f}')qq

        return pred, f'{confidence_score:0.4f}'


def display_images(img1, img2) :
    try :
        fig=plt.figure(figsize=(10,10))
        
        ax=fig.add_subplot(121)
        ax.imshow(cv2.cvtColor(img1,cv2.COLOR_BGR2RGB))
        ax.title.set_text('Line 1')

        ax=fig.add_subplot(122)
        ax.imshow(cv2.cvtColor(img2,cv2.COLOR_BGR2RGB))
        ax.title.set_text('Line 2')

        plt.show()
    except Exception :
        print("Error Occurs")

def display_image(img) :
    try : 
        plt.imshow(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
        plt.title('plate')
        plt.xticks([])
        plt.yticks([])
        plt.show()
    except Exception :
        print("Error Occurs")

def perspectiveTransform(img, plot):
    lu_x = plot[0][0][0]
    lu_y = plot[0][0][1]
    ru_x = plot[0][1][0]
    ru_y = plot[0][1][1]
    rl_x = plot[0][2][0]
    rl_y = plot[0][2][1]
    ll_x = plot[0][3][0]
    ll_y = plot[0][3][1]

    topLeft = np.array([lu_x, lu_y])
    topRight = np.array([ru_x, ru_y])
    bottomRight = np.array([rl_x, rl_y])
    bottomLeft = np.array([ll_x, ll_y])

    pts1 = np.float32([topLeft, topRight, bottomRight, bottomLeft])

    w1 = abs(rl_x - ll_x)
    w2 = abs(ru_x - lu_x)
    h1 = abs(ru_y - rl_y)
    h2 = abs(lu_y - ll_y)
    width = int(max([w1, w2]))
    height = int(max([h1, h2]))

    # 변환 후 4개 좌표
    pts2 = np.float32([[0, 0], [width - 1, 0],
                    [width - 1, height - 1], [0, height - 1]])

    # 변환 행렬 계산
    mtrx = cv2.getPerspectiveTransform(pts1, pts2)
    # 원근 변환 적용
    result_img = cv2.warpPerspective(img, mtrx, (width, height))
    # result_img = cv2.resize(result_img, dsize=(640, 480), interpolation=cv2.INTER_AREA)

    return result_img

def warp_plate(pose_model, image) :
    results = pose_model(image)
    if results :
        keypoints = results[0].keypoints.xy.cpu().numpy()
        transformed_image = perspectiveTransform(image, keypoints)
        return transformed_image
    else : 
        return None

def distinguish_ev_plate(image) :
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 파란색 범위 정의
    lower_blue = np.array([95, 50, 50]) # 색상, 채도, 명도
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # 파란색 픽셀 비율 계산
    blue_ratio = np.sum(mask_blue) / (mask_blue.shape[0] * mask_blue.shape[1] * 255)

    if blue_ratio >= 0.8:                
        return True
    else : 
        return False
    


def extract_twoline(twoline_model, image) :
    results = twoline_model.predict(image, save=False, imgsz=640, conf=0.7)
    if results : 
        boxes = results[0].boxes
        results_info = boxes
        cls_numbers = results_info.cls 
        conf_numbers = results_info.conf 
        box_xyxy = results_info.xyxy
        
        for bbox, cls_idx, conf_idx in zip(box_xyxy, cls_numbers, conf_numbers) :
            class_number = int(cls_idx.item())
            
            x1 = int(bbox[0].item())
            y1 = int(bbox[1].item())
            x2 = int(bbox[2].item())
            y2 = int(bbox[3].item())

            if class_number == 0 :
                plate_line1 = image[y1:y2, x1:x2]
            elif class_number == 1 :
                plate_line2 = image[y1:y2, x1:x2]
                
        return plate_line1, plate_line2
    else :
        return None

def extract_plate_image(yolo_model, pose_model, twoline_model, video_path) :
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    results = {}
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % 30 == 0:
            results[frame_count] = {}
            image = frame
            names = yolo_model.names
            detections = yolo_model(image, save=False, imgsz=640, conf=0.5)[0]
            # for result in results:
            detections_ = []
            for r in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = r
                print(r)
                if int(class_id) in plates:
                    detections_.append([x1, y1, x2, y2, score])
                    
                    
            track_ids = tracker.update(np.asarray(detections_))
            if int(class_id) in plates:
                plate_img = image[int(y1):int(y2), int(x1):int(x2), :]
                warped_plate = warp_plate(pose_model, plate_img)
                if score < 0.7 :
                    bool = distinguish_ev_plate(warped_plate)
                    if class_id == 1 :
                        if bool == True :
                            continue
                        else : 
                            print("Contact Admin") # return image to admin
                    
                    elif class_id == 2 :
                        if bool == False :
                            if warped_plate is not None :
                                display_image(warped_plate) # display - ocr
                                ocr_plate, ocr_conf = ocr(warped_plate)
                                print(ocr_plate, ocr_conf)
                            else :
                                display_image(plate_img)
                                ocr_plate, ocr_conf = ocr(warped_plate)
                                print(ocr_plate, ocr_conf)
                        else :
                            print("Contact Admin") # return image to admin
                        
                    elif class_id == 3 :
                        if bool == False :
                            if warped_plate is not None :
                                output = extract_twoline(twoline_model, warped_plate)
                                if isinstance(output, tuple) :
                                    line1, line2 = output
                                    display_images(line1, line2)
                                    line1_ocr , line1_conf = ocr(line1)
                                    line2_ocr , line2_conf = ocr(line2)
                                    ocr_plate = line1_ocr +line2_ocr
                                    ocr_conf = line1_conf + line2_conf / 2 
                                    print(ocr_plate, ocr_conf)                                      
                                else :
                                    print("No plate detected!")
                            else :
                                output = extract_twoline(twoline_model, plate_img)
                                if isinstance(output, tuple) :
                                    line1, line2 = output
                                    display_images(line1, line2)
                                    line1_ocr , line1_conf = ocr(line1)
                                    line2_ocr , line2_conf = ocr(line2)
                                    ocr_plate = line1_ocr +line2_ocr
                                    ocr_conf = line1_conf + line2_conf / 2 
                                    print(ocr_plate, ocr_conf)
                                        
                                else :
                                    print("No plate detected!")
                    else : 
                        print("Contact Admin") # return image to admin

                ##### conf_score > 0.7 #####
                else :
                    if class_id == 1 :
                        continue
                    elif class_id == 2 :
                        if warped_plate is not None :
                            display_image(warped_plate)
                            ocr_plate, ocr_conf = ocr(warped_plate)
                            print(ocr_plate, ocr_conf)
                        else : 
                            display_image(plate_img)
                            ocr_plate, ocr_conf = ocr(warped_plate)
                            print(ocr_plate, ocr_conf)
                    elif class_id == 3 :
                        if warped_plate is not None :
                            output = extract_twoline(twoline_model, warped_plate)
                            if isinstance(output, tuple) :
                                line1, line2 = output
                                display_images(line1, line2)
                                line1_ocr , line1_conf = ocr(line1)
                                line2_ocr , line2_conf = ocr(line2)
                                ocr_plate = line1_ocr +line2_ocr
                                ocr_conf = line1_conf + line2_conf / 2 
                                print(ocr_plate, ocr_conf)
                            else :
                                print("No plate detected!")
                        else :
                            output = extract_twoline(twoline_model, plate_img)
                            if isinstance(output, tuple) :
                                line1, line2 = output
                                display_images(line1, line2)
                                line1_ocr , line1_conf = ocr(line1)
                                line2_ocr , line2_conf = ocr(line2)
                                ocr_plate = line1_ocr +line2_ocr
                                ocr_conf = line1_conf + line2_conf / 2 
                                print(ocr_plate, ocr_conf)
                            else :
                                print("No plate detected!")

                print("detections shape:", detections.shape)
                print("trackers shape:", trackers.shape)
                if ocr_plate is not None:
                    results[frame_count][tuple(track_ids)] = {
                                                'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                    'text': ocr_plate,
                                                                    'bbox_score': score,
                                                                    'text_score': ocr_conf}}
        else :
            pass

                
            

            # if results :
            #     detection = []
            #     boxes = results[0].boxes
            #     results_info = boxes
            #     cls_numbers = results_info.cls 
            #     conf_numbers = results_info.conf 
            #     box_xyxy = results_info.xyxy
            #     detection.append([box_xyxy,conf_numbers])
            #     print(detection)
            #     car_bbox = []
            #     plate_bbox = []
            #     for bbox, cls_idx, conf_idx in zip(box_xyxy, cls_numbers, conf_numbers) :
            #         class_number = int(cls_idx.item())
            #         confidence_score = float(conf_idx.item())
            #         print(f"{class_number} {confidence_score}") 
                    
            #         x1 = int(bbox[0].item())
            #         y1 = int(bbox[1].item())
            #         x2 = int(bbox[2].item())
            #         y2 = int(bbox[3].item())
            #         if class_number == 0 :
            #             # car_bbox.append(x1,y1,x2,y2)
            #             continue
            #         # plate_bbox.append(x1,y1,x2,y2)
            #         plate_img = image[y1:y2, x1:x2]
            #         warped_plate = warp_plate(pose_model, plate_img)
                    
            #         if confidence_score < 0.7 :
            #             bool = distinguish_ev_plate(warped_plate)
            #             if class_number == 1 :
            #                 if bool == True :
            #                     continue
            #                 else : 
            #                     print("Contact Admin") # return image to admin
                        
            #             elif class_number == 2 :
            #                 if bool == False :
            #                     if warped_plate is not None :
            #                         display_image(warped_plate) # display - ocr
            #                         ocr_plate, ocr_conf = ocr(warped_plate)
            #                         print(ocr_plate, ocr_conf)
            #                     else :
            #                         display_image(plate_img)
            #                         ocr_plate, ocr_conf = ocr(warped_plate)
            #                         print(ocr_plate, ocr_conf)
            #                 else :
            #                     print("Contact Admin") # return image to admin
                            
            #             elif class_number == 3 :
            #                 if bool == False :
            #                     if warped_plate is not None :
            #                         output = extract_twoline(twoline_model, warped_plate)
            #                         if isinstance(output, tuple) :
            #                             line1, line2 = output
            #                             display_images(line1, line2)
            #                             line1_ocr , line1_conf = ocr(line1)
            #                             line2_ocr , line2_conf = ocr(line2)
            #                             ocr_plate = line1_ocr +line2_ocr
            #                             ocr_conf = line1_conf + line2_conf / 2 
            #                             print(ocr_plate, ocr_conf)                                      
            #                         else :
            #                             print("No plate detected!")
            #                     else :
            #                         output = extract_twoline(twoline_model, plate_img)
            #                         if isinstance(output, tuple) :
            #                             line1, line2 = output
            #                             display_images(line1, line2)
            #                             line1_ocr , line1_conf = ocr(line1)
            #                             line2_ocr , line2_conf = ocr(line2)
            #                             ocr_plate = line1_ocr +line2_ocr
            #                             ocr_conf = line1_conf + line2_conf / 2 
            #                             print(ocr_plate, ocr_conf)
                                            
            #                         else :
            #                             print("No plate detected!")
            #                 else : 
            #                     print("Contact Admin") # return image to admin
            #         else :
            #             if class_number == 1 :
            #                 continue
            #             elif class_number == 2 :
            #                 if warped_plate is not None :
            #                     display_image(warped_plate)
            #                     ocr_plate, ocr_conf = ocr(warped_plate)
            #                     print(ocr_plate, ocr_conf)
            #                 else : 
            #                     display_image(plate_img)
            #                     ocr_plate, ocr_conf = ocr(warped_plate)
            #                     print(ocr_plate, ocr_conf)
            #             elif class_number == 3 :
            #                 if warped_plate is not None :
            #                     output = extract_twoline(twoline_model, warped_plate)
            #                     if isinstance(output, tuple) :
            #                         line1, line2 = output
            #                         display_images(line1, line2)
            #                         line1_ocr , line1_conf = ocr(line1)
            #                         line2_ocr , line2_conf = ocr(line2)
            #                         ocr_plate = line1_ocr +line2_ocr
            #                         ocr_conf = line1_conf + line2_conf / 2 
            #                         print(ocr_plate, ocr_conf)
            #                     else :
            #                         print("No plate detected!")
            #                 else :
            #                     output = extract_twoline(twoline_model, plate_img)
            #                     if isinstance(output, tuple) :
            #                         line1, line2 = output
            #                         display_images(line1, line2)
            #                         line1_ocr , line1_conf = ocr(line1)
            #                         line2_ocr , line2_conf = ocr(line2)
            #                         ocr_plate = line1_ocr +line2_ocr
            #                         ocr_conf = line1_conf + line2_conf / 2 
            #                         print(ocr_plate, ocr_conf)
            #                     else :
            #                         print("No plate detected!")
            # else :
            #     pass
        frame_count += 1
    cap.release()
if __name__ == "__main__":
    # main에 들어갈 코드
    pose_model = YOLO('./models/pose_best.pt')
    twoline_model = YOLO('./models/twoline_best.pt')
    yolo_model = YOLO("./models/yolo_best.pt")
    DEFAULT_CFG_DICT = yaml_load('./yaml/opt.yaml')
    opt = argparse.Namespace(**DEFAULT_CFG_DICT)
    model = Model(opt)
    model = torch.nn.DataParallel(model).to(device)
    converter = AttnLabelConverter(opt.character_list)
    model.load_state_dict(torch.load(opt.saved_model, map_location=device))
    plates = [1, 2, 3]

    tracker = Sort()

    input_path = "./data/1min_low_.mp4"
    extract_plate_image(yolo_model, pose_model, twoline_model, input_path)