import os, re, random, inspect, math, csv
import pyqt5_fugueicons as fugue
import cv2
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

from make_new_window import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 전역 변수
        self.video_source = None

        self.setWindowTitle("EV 차량 번호판 감지 프로그램")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(fugue.icon("surveillance-camera", size=16, fallback_size=True))

        # (1) 탭

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("background-color: #F0F0F0;")

        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, fugue.icon("camera", size=16, fallback_size=True), "실시간 체크")

        tab_bar = self.tab_widget.tabBar()
        font = QFont("Malgun Gothic", 8)
        font.setBold(True)
        tab_bar.setFont(font)

        tab_layout1 = QVBoxLayout(self.tab1)
        tab1_splitter_layout = QSplitter(Qt.Horizontal)
        tab_layout1.addWidget(tab1_splitter_layout)

        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, fugue.icon("eye", size=16, fallback_size=True), "관리자 페이지")

        tab_layout2 = QVBoxLayout(self.tab2)
        tab2_splitter_layout = QSplitter(Qt.Horizontal)
        tab_layout2.addWidget(tab2_splitter_layout)


        ## (2) 탭 1

        ### (2-1) 왼쪽 위젯

        self.video_player = QLabel()
        self.video_player.setMaximumHeight(1200)

        tab1_inner_layout1 = QVBoxLayout()
        tab1_inner_layout1.addWidget(self.video_player)

        ### (2-2) 오른쪽 위젯 (테이블)
        #### 레이블
        self.tab1_item_list_label = QLabel('🚗 차량 정보', font=QFont('Malgun Gothic', 18, QFont.Bold))  
        self.tab1_item_list_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")

        #### 테이블
        self.tab1_item_list_table = QTableWidget(font=QFont('Malgun Gothic', 10))
        headers = ["√", "frame_nmr", "car_id", "car_bbox", "license_plate_bbox", "license_plate_bbox_score", "license_number", "license_number_score"]
        self.tab1_item_list_table.setColumnCount(len(headers))
        self.tab1_item_list_table.setHorizontalHeaderLabels(headers)
        self.tab1_item_list_table.setStyleSheet("background-color: white;")
        self.tab1_item_list_table.setEditTriggers(QTableWidget.NoEditTriggers)     # 수정 금지
        
        self.tab1_item_list_table.setColumnWidth(0, 10)    # 체크박스 컬럼

        # 컬럼 더블 클릭시 오름차순/내림차순 정렬
        self.tab1_item_list_table.horizontalHeader().sectionDoubleClicked.connect(lambda col: self.on_header_double_clicked_table(col, self.tab1_item_list_table))

        #### 레이아웃에 위젯 부착
        tab1_inner_layout2 = QVBoxLayout()
        tab1_inner_layout2.addWidget(self.tab1_item_list_label)
        tab1_inner_layout2.addWidget(self.tab1_item_list_table)

        #### 위젯에 레이아웃 부착
        tab1_widget1 = QWidget()
        tab1_widget1.setLayout(tab1_inner_layout1)

        tab1_widget2 = QWidget()
        tab1_widget2.setLayout(tab1_inner_layout2)

        #### 구분자 레이아웃에 위젯 부착
        tab1_splitter_layout.addWidget(tab1_widget1)
        tab1_splitter_layout.addWidget(tab1_widget2)


        ## (3) 탭 2

        ### (3-1) 왼쪽 위젯 (이미지 뷰어)
        self.image_viewer = QLabel()
        self.image_viewer.setMaximumHeight(1200)

        tab2_inner_layout1 = QVBoxLayout()
        tab2_inner_layout1.addWidget(self.image_viewer)

        ### (3-2) 오른쪽 위젯 (테이블)
        #### 레이블
        self.tab2_item_list_label = QLabel('✅ 관리자 설정', font=QFont('Malgun Gothic', 18, QFont.Bold))  
        self.tab2_item_list_label.setStyleSheet("background-color: rgba(189, 189, 189, 0.1);")

        #### 테이블
        self.tab2_item_list_table = QTableWidget(font=QFont('Malgun Gothic', 10))
        headers = ["√", "EV", "번호판(1줄)", "번호판(2줄)", "🖼️"]
        self.tab2_item_list_table.setColumnCount(len(headers))
        self.tab2_item_list_table.setHorizontalHeaderLabels(headers)
        self.tab2_item_list_table.setStyleSheet("background-color: white;")
        self.tab2_item_list_table.setEditTriggers(QTableWidget.NoEditTriggers)    # 수정 금지
        

        # 컬럼 더블 클릭시 오름차순/내림차순 정렬
        self.tab2_item_list_table.horizontalHeader().sectionDoubleClicked.connect(lambda col: self.on_header_double_clicked_table(col, self.tab2_item_list_table))
        
        # 각 컬럼 사이즈 설정
        self.tab2_item_list_table.setColumnWidth(0, 10)
        self.tab2_item_list_table.setColumnWidth(1, 60) 
        self.tab2_item_list_table.setColumnWidth(2, 60) 
        self.tab2_item_list_table.setColumnWidth(3, 60) 
        self.tab2_item_list_table.setColumnWidth(4, 10)

        self.tab2_item_list_table.cellDoubleClicked.connect(self.copy_image_to_image_viewer) 

        #### 레이아웃에 위젯 부착
        tab2_inner_layout2 = QVBoxLayout()
        tab2_inner_layout2.addWidget(self.tab2_item_list_label)
        tab2_inner_layout2.addWidget(self.tab2_item_list_table)

        #### 위젯에 레이아웃 부착
        tab2_widget1 = QWidget()
        tab2_widget1.setLayout(tab2_inner_layout1)

        tab2_widget2 = QWidget()
        tab2_widget2.setFixedWidth(280)
        tab2_widget2.setLayout(tab2_inner_layout2)


        #### 구분자 레이아웃에 위젯 부착
        tab2_splitter_layout.addWidget(tab2_widget1)
        tab2_splitter_layout.addWidget(tab2_widget2)



        ## (4) 상태 표시줄 생성 및 부착
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)


        ## (5) 메뉴바 생성 및 설정
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgba(240, 240, 240, 0.65); color: black;")

        ### (5-1) 메뉴 목록 생성
        self.filemenu = menubar.addMenu("파일")
        self.infomenu = menubar.addMenu("정보")

        self.menuNames = {
            "파일": self.filemenu,
            "정보": self.infomenu
        }


        ### (5-2) 하위 메뉴 생성
        ### [파일] 메뉴
        filemenu_items = [
            {
                "icon": "application-plus",
                "text": "CCTV 녹화 동영상 파일 불러오기",
                "shortcut": "Ctrl+O",
                "status_tip": "CCTV 녹화 동영상 파일을 불러옵니다.",
                "triggered": self.open_video_file
            },
            {
                "icon": "cross",
                "text": "프로그램 종료",
                "shortcut": "Ctrl+Q",
                "status_tip": "프로그램을 종료합니다.",
                "triggered": qApp.quit
            }
        ]

        ### [정보] 메뉴
        infomenu_items = [
            {
                "icon": "information",
                "text": "프로그램 정보",
                "shortcut": "Ctrl+I",
                "status_tip": "프로그램 정보를 확인합니다.",
                "triggered": lambda: QMessageBox.information(self, "프로그램 정보", "EV 차량 번호판 감지 프로그램 \n제작: MS AI School 6팀 (2기)")
            },
        ]


        self.setMenuWithItems("파일", filemenu_items)
        self.setMenuWithItems("정보", infomenu_items)

        toolbar_style = """
        QToolButton:checked { 
                background-color: #CCE8FF; 
                border: 1px solid #99D1FF; 
                border-radius: 2px;
                padding: 2px; 
        }
        QToolButton:hover { 
            background-color: #E5F3FF; 
            border: 1px solid #CCE8FF; 
            border-radius: 2px; 
        }
        """
        

        ## (6) 📦 툴바 생성 및 설정, 그리고 레이아웃에 부착
        ### 툴바1 생성 (탭1)
        self.tab1_toolbar1 = QToolBar()
        self.tab1_toolbar1.setMovable(False)
        self.tab1_toolbar1.setFixedHeight(50)
        self.tab1_toolbar1.setStyleSheet(toolbar_style)

        ### 툴바2 생성 (탭1)
        self.tab1_toolbar2 = QToolBar()
        self.tab1_toolbar2.setMovable(True)
        self.tab1_toolbar2.setFixedHeight(50)
        self.tab1_toolbar2.setStyleSheet(toolbar_style)

        ### 툴바1 생성 (탭2)
        self.tab2_toolbar1 = QToolBar()
        self.tab2_toolbar1.setMovable(False)
        self.tab2_toolbar1.setFixedHeight(50)
        self.tab2_toolbar1.setStyleSheet(toolbar_style)

        ### 툴바2 생성 (탭2)
        self.tab2_toolbar2 = QToolBar()
        self.tab2_toolbar2.setMovable(True)
        self.tab2_toolbar2.setFixedHeight(50)
        self.tab2_toolbar2.setStyleSheet(toolbar_style)


        self.toolBarNames = {
            '툴바1': self.tab1_toolbar1,
            '툴바2': self.tab1_toolbar2,
            '툴바3': self.tab2_toolbar1,
            '툴바4': self.tab2_toolbar2,
        }

        ### 각 툴바에 추가할 액션 생성
        tab1_toolbar1_actions = [
            ("CCTV 동영상 불러오기", "film", self.open_video_file, False, False),
            ("CCTV 동영상 멈추기", "minus-circle", self.pause_the_video, False, False),
            ("CCTV 동영상 재생하기", "monitor", self.resume_the_video, False, False),
            ("재생 속도 올리기 (x0.1)", "navigation-090", self.speed_up_video, False, False),
            ("재생 속도 내리기 (x0.1)", "navigation-270", self.speed_down_video, False, False),
            ("CCTV 동영상 지우기", "scissors", lambda: self.clear_the_content("동영상"), False, False),
        ]

        tab1_toolbar2_actions = [
            ("테이블에 내용 불러오기 (CSV)", "table-import", lambda: self.import_table_widget(self.tab1_item_list_table), False, False),
            ("테이블 내용 내보내기 (CSV)", "table-export", lambda: self.export_table_widget(self.tab1_item_list_table), False, False),
            ("선택한 행 지우기", "scissors-blue", lambda: self.delete_selected_row_on_table(self.tab1_item_list_table), False, False),
            # ("구분선", "", "", "", ""),
            # ("이메일로 보내기", "mail", self.send_email, False, False),
            # ("카카오톡으로 보내기", "./icon/kakaotalk.ico_ni", self.send_kakaotalk_alarm, False, False),
        ]

        tab2_toolbar1_actions = [
            ("이미지 불러오기", "photo-album-blue", self.open_image_file, False, False),
            ("이미지 지우기", "scissors", lambda: self.clear_the_content("이미지"), False, False),
        ]

        tab2_toolbar2_actions = [
            ("결과 확인", "system-monitor", self.show_the_result, False, False),
            ("선택한 행 지우기", "scissors-blue", lambda: self.delete_selected_row_on_table(self.tab2_item_list_table), False, False),
        ]

        self.setToobarWithActions("툴바1", tab1_toolbar1_actions)
        self.setToobarWithActions("툴바2", tab1_toolbar2_actions)
        self.setToobarWithActions("툴바3", tab2_toolbar1_actions)
        self.setToobarWithActions("툴바4", tab2_toolbar2_actions)

        
        tab1_inner_layout1.addWidget(self.tab1_toolbar1)    
        tab1_inner_layout2.addWidget(self.tab1_toolbar2)    
        tab2_inner_layout1.addWidget(self.tab2_toolbar1)    
        tab2_inner_layout2.addWidget(self.tab2_toolbar2)    



    ###############################################################
    ######################### 기능 구현 ###########################
    ###############################################################


    # 툴바 설정 기능
    def setToobarWithActions(self, target, actions):
        toolbar = self.toolBarNames[target]

        for text, icon_name, connect_func, shortcut, checkable in actions:
            if text != "구분선":    
                action = QAction(text, toolbar)
                
                if "_ni" in icon_name:
                    icon_name = icon_name.replace("_ni", "")
                    action.setIcon(QIcon(icon_name))
                else:    
                    action.setIcon(fugue.icon(icon_name, size=24, fallback_size=True))
                action.triggered.connect(connect_func)
                action.setShortcut(shortcut)
                action.setCheckable(checkable)
                toolbar.addAction(action)

            else: 
                toolbar.addSeparator() 

        
    # 메뉴에 초기 항목을 추가하는 기능
    def setMenuWithItems(self, target, items):
        menu = self.menuNames[target]
        
        for item in items:
            # icon의 존재 유무에 따라 항목/구분선 구분
            if item["icon"] != None:
                action = QAction(fugue.icon(item["icon"], size=16, fallback_size=True), item["text"], self)
                action.setShortcut(item["shortcut"])
                action.setStatusTip(item["status_tip"])
                action.triggered.connect(item["triggered"])
                menu.addAction(action)
            else:
                menu.addSeparator()


    # 테이블에 있는 내용 CSV 파일로 내보내는 기능
    def export_table_widget(self, target):
        file_dialog = QFileDialog(self)

        datetime_format_style = "%Y%m%d_%H%M%S"
        current_datetime = datetime.now().strftime(datetime_format_style)
        
        fileName = f"차량정보_{current_datetime}.csv"
        file_path, _ = file_dialog.getSaveFileName(self, f"차량 정보 테이블 내용 내보내기", fileName, filter="CSV File (*.csv)")

        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)

                # 컬럼명 저장
                column_names = []
                for column in range(target.columnCount()):
                    column_names.append(target.horizontalHeaderItem(column).text())
                writer.writerow(column_names)

                # 데이터 저장
                for row in range(target.rowCount()):
                    row_data = []
                    for column in range(target.columnCount()):
                        item = target.item(row, column)
                        if item is not None:
                            if isinstance(item, QCheckBox):
                                # 체크박스인 경우 불리언 값을 "1" 또는 "0"으로 변환하여 처리
                                row_data.append("1" if item.isChecked() else "0")
                            else:
                                row_data.append(item.text())
                        else:
                            row_data.append("")
                    writer.writerow(row_data)
                
            QMessageBox.information(self, "알림", "차량 정보 테이블의 내용을 내보냈습니다.", QMessageBox.Ok)

            file.close()


    # 테이블로 CSV 파일을 불러오는 기능
    def import_table_widget(self, target_table):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix("csv")

        file_path, _ = file_dialog.getOpenFileName(self, "차량 정보 테이블에 내용 불러오기", filter="CSV File (*.csv)")

        if file_path:
            # 테이블에 있는 기존 내용 지우기
            target_table.clearContents()
            target_table.setRowCount(0)

            with open(file_path, newline='', encoding='ISO-8859-1') as file:
                try:
                    reader = csv.reader(file)
                    next(reader)     # 첫 번째 행 건너뛰기
                    data = list(reader)
                except:
                    QMessageBox.warning(self, "알림", "파일의 인코딩 방식에 문제가 있습니다.")
                target_table.setRowCount(len(data))
                target_table.setColumnCount(len(data[0]))

                for row_idx, row_data in enumerate(data):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(cell_data.strip())
                        
                        # 폰트 설정
                        cell_font = QFont("Consolas", 9)
                        item.setFont(cell_font)

                        if col_idx == 0:
                            row_checkbox = QTableWidgetItem()
                            row_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                            row_checkbox.setCheckState(Qt.Unchecked)
                            target_table.setColumnWidth(0, 16)
                            target_table.setItem(row_idx, col_idx, row_checkbox)

                        target_table.setItem(row_idx, col_idx + 1, item)    # 체크박스 빼고 넣기
                
                QMessageBox.information(self, "알림", "차량 정보 테이블에 내용을 가져왔습니다.")

                file.close()

    # 상태바 메시지 업데이트
    def setStatusBarMessage(self, message):
        self.statusBar.showMessage(message, 3000)  # 3초간 메시지 표시

    # 동영상 파일 열기
    def open_video_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "동영상 선택", "", "동영상 파일 (*.mp4 *.avi *.mkv);;모든 파일 (*)", options=options)

        if file_name:
            self.play_video(file_name)


    # 동영상 재생 멈추기
    def pause_the_video(self):
        if self.video_source is not None:
            # self.video_player.clear() 
            self.video_source.release()  # 비디오 소스 종료
            self.video_source = None
            self.setStatusBarMessage("동영상 재생이 멈추었습니다.")


    # 동영상 재생 재개하기
    def resume_the_video(self):
        try:
            if self.video_source is None:
                self.play_video(self.current_video_source)
                self.setStatusBarMessage("동영상 재생이 재개되었습니다.")
        except:
            pass


    # 재생 속도 올리기
    def speed_up_video(self):
        if self.video_source is not None:
            self.fps_multiplier += 0.1
            self.update_video_speed()


    # 재생 속도 내리기
    def speed_down_video(self):
        if self.video_source is not None:
            self.fps_multiplier = max(0.1, self.fps_multiplier - 0.1)
            self.update_video_speed()


    # 재생 속도 업데이트
    def update_video_speed(self):
        if self.video_source is not None:
            self.video_source.set(cv2.CAP_PROP_FPS, self.base_fps * self.fps_multiplier)
            self.setStatusBarMessage(f"재생 속도: {self.fps_multiplier:.1f}배")


    # 동영상 재생하기
    def play_video(self, video_src):
        self.current_video_source = video_src
        self.video_source = cv2.VideoCapture(video_src)
        self.base_fps = self.video_source.get(cv2.CAP_PROP_FPS)   
        self.fps_multiplier = 1.0

        try:
            if self.video_source is not None:
                while self.video_source.isOpened():
                    ret, frame = self.video_source.read()

                    if not ret:
                        self.stop_video()
                        break

                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, c = img.shape
                    qImg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)

                    pixmap = QPixmap.fromImage(qImg)
                    p = pixmap.scaled(int(w * 480 / h), 480, Qt.IgnoreAspectRatio)
                    self.video_player.setPixmap(p)

                    key = cv2.waitKey(int(1000 / (self.base_fps * self.fps_multiplier)))

                    if key == ord('q'):
                        break

                self.video_source.release()
                cv2.destroyAllWindows()
        except:
            pass


    # 동영상 재생 중 프로그램을 끌 때 비디오 객체 제거
    def closeEvent(self, event):
        self.stop_video()
        super().closeEvent(event)


    # 비디오 재생 중단시키기
    def stop_video(self):
        if self.video_source is not None:
            self.video_source.release()
            cv2.destroyAllWindows()


    # 이메일로 보내기
    def send_email(self):
        value, ok = QInputDialog.getText(self, "알림", "수신 이메일 주소를 입력하세요: ")

        if ok:
            # 이메일 발송자(관리자) 정보 입력
            from_email = "admin_msteam06@gmail.com"   
            password = "Msteam#06"   

            subject = "주차 위반 알림"                     # 메시지 제목
            message = "주차 위반 차량이 발견되었습니다."     # 메시지 내용
            to_email = value                              # 수신자 이메일

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)    # gmail (587)
                server.starttls()
                server.login(from_email, password)
                server.sendmail(from_email, to_email, msg.as_string())
                server.quit()

                self.setStatusBarMessage("이메일이 발송되었습니다.")

            except:
                self.setStatusBarMessage("이메일 발송 중 오류가 발생했습니다")


    # 이미지 불러오기
    def open_image_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_names, _ = QFileDialog.getOpenFileNames(self, "이미지 불러오기", "", "이미지 파일 (*.jpg *.png *.bmp);;모든 파일 (*)", options=options)

        if file_names:
            for file_name in file_names:
                pixmap = QPixmap(file_name)
                scaled_pixmap = pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                self.image_viewer.setPixmap(scaled_pixmap)
                self.image_viewer.setAlignment(Qt.AlignCenter)

                # 표 안에 새로운 행을 추가하고 체크 박스 채워넣기
                target_table = self.tab2_item_list_table
                row_position = target_table.rowCount()
                target_table.insertRow(row_position)

                row_checkbox = QTableWidgetItem()
                row_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                row_checkbox.setCheckState(Qt.Unchecked)
                target_table.setColumnWidth(0, 16)

                ev_checkbox = QTableWidgetItem()
                ev_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                ev_checkbox.setCheckState(Qt.Unchecked)

                one_line_checkbox = QTableWidgetItem()
                one_line_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                one_line_checkbox.setCheckState(Qt.Unchecked)

                two_line_checkbox = QTableWidgetItem()
                two_line_checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) 
                two_line_checkbox.setCheckState(Qt.Unchecked)

                target_table.setItem(row_position, 0, row_checkbox)
                target_table.setItem(row_position, 1, ev_checkbox)
                target_table.setItem(row_position, 2, one_line_checkbox)
                target_table.setItem(row_position, 3, two_line_checkbox)

                car_image_item = QTableWidgetItem()
                car_image_item.setIcon(QIcon(pixmap))
                target_table.setItem(row_position, 4, car_image_item)



    # 내용물 지우기
    def clear_the_content(self, type):
        if type == "동영상":
            if self.video_source is not None:
                self.video_player.clear()      # 비디오 플레이어 내용 지우기
                self.video_source.release()      # 비디오 소스 종료
                self.video_source = None
        elif type == "이미지":
            self.image_viewer.clear()    # 이미지 뷰어 내용 지우기
        
        self.setStatusBarMessage(f"{type}을 지웠습니다.")

    
    # 결과 보여주기 (새로운 창)
    def show_the_result(self):
        target_table = self.tab2_item_list_table

        items = {}

        # 테이블에서 정보 가져와서 딕셔너리에 넣기
        for row in range(target_table.rowCount()):
            row_number_checkbox = target_table.item(row, 0)

            if row_number_checkbox.checkState() == Qt.Checked:   # 첫 번째 체크박스가 체크되어 있으면
                is_ev_checkbox = target_table.item(row, 1)
                is_one_line_checkbox = target_table.item(row, 2)
                is_two_line_checkbox = target_table.item(row, 3)
                car_image = target_table.item(row, 4)

                is_ev = is_ev_checkbox.checkState() == Qt.Checked
                is_one_line = is_one_line_checkbox.checkState() == Qt.Checked
                is_two_line = is_two_line_checkbox.checkState() == Qt.Checked
                car_image = car_image.icon().pixmap(QSize(9999, 9999))

                items[row] = [is_ev, is_one_line, is_two_line, car_image]

                # 버튼 3개
                # 




        # 다이얼로그를 넣을 리스트
        dialogs = []  

        for row in range(target_table.rowCount()):
            row_number_checkbox = target_table.item(row, 0)

            if row_number_checkbox.checkState() == Qt.Checked:
                car_image = target_table.item(row, 4)
                car_pixmap = car_image.icon().pixmap(QSize(9999, 9999))

                dialog = QDialog(self)
                dialog.setFixedSize(dialog.sizeHint())

                outer_layout = QVBoxLayout()
                
                # 이미지 넣기
                image_label = QLabel()
                image_label.setPixmap(car_pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                image_label.setAlignment(Qt.AlignCenter)
                outer_layout.addWidget(image_label)

                # 설명 넣기
                item_label = QLabel(f"<b>[Plate #{row}]</b> <b>EV</b>: {'O' if items[row][0] else 'X'} | <b>One Line Plate</b>: {'O' if items[row][1] else 'X'} | <b>Two Line Plate</b>: {'O' if items[row][2] else 'X'}")
                label_font = QFont("Consolas", 9)

                item_label.setAlignment(Qt.AlignCenter)
                item_label.setFont(label_font)
                
                inner_layout = QHBoxLayout()
                inner_layout.addWidget(item_label)

                outer_layout.addLayout(inner_layout)  
                dialog.setLayout(outer_layout)
                dialog.setWindowTitle(f"{row}번 차량 사진")
                dialog.setWindowIcon(fugue.icon("car-red"))

                dialogs.append(dialog)  


        # 다이얼로그 띄우기
        for dialog in dialogs:
            dialog.show()


    # 테이블에 있는 사진을 더블 클릭하면 이미지 뷰어에 띄어주기
    def copy_image_to_image_viewer(self, row, column):
        if column == 4: 
            item = self.tab2_item_list_table.item(row, column)
            if item and isinstance(item, QTableWidgetItem):
                pixmap = item.icon().pixmap(QSize(9999, 9999))   # 임의로 최대 사이즈로 설정
                scaled_pixmap = pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # 이미지 뷰어에 표시
                self.image_viewer.clear()
                self.image_viewer.setPixmap(scaled_pixmap)
                self.image_viewer.setAlignment(Qt.AlignCenter)

    # 테이블에서 선택한 행 지우기
    def delete_selected_row_on_table(self, target):
        rows_to_delete = []
        count_checkbox = 0

        for row in range(target.rowCount() - 1, -1, -1):
            item_checkbox = target.item(row, 0)

            if item_checkbox and item_checkbox.checkState() == Qt.Checked:
                count_checkbox += 1
                rows_to_delete.append(row)
                
        for row_index in rows_to_delete:
            target.removeRow(row_index)
        
        self.setStatusBarMessage(f"테이블에서 {count_checkbox}개의 행을 삭제하였습니다.")
    

    # 테이블 헤더 더블 클릭 시 전체 선택/해제 (체크박스)
    def on_header_double_clicked_table(self, col, target):
        if col == 0:
            check_state = Qt.Checked if all(target.item(row, 0).checkState() == Qt.Unchecked for row in range(target.rowCount())) else Qt.Unchecked

            for row in range(target.rowCount()):
                item = target.item(row, 0)
                item.setCheckState(check_state)