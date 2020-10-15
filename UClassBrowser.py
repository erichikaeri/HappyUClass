from time import sleep
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import visibility_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup

def sleepUntil(condition):
    while True:
        canBreak = condition()
        if canBreak:
            break
        sleep(1)

class UClassBrowser:
    def __init__(self):
        options = Options()
        options.headless = True
        options.add_argument("--log-level=OFF")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver : WebDriver = webdriver.Chrome(executable_path="./chromedriver.exe", options=options, service_log_path="NUL")
        self.driver.get("http://uclass.uos.ac.kr/")

        self.isLoggedIn = False
        self.courseList = []
        self.lectures = []
        self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.close()

    def close(self):
        self.driver.close()

    def login(self, id, password):
        data = {
            "_enpass_login_":"submit",
            "langKnd":"ko",
            "loginType":"normal",
            "returnUrl":"",
            "ssoId":"",
            "password":""
        }

        data["ssoId"] = id
        data["password"] = password

        self.session = requests.Session()
        res = self.session.post("https://portal.uos.ac.kr/user/loginProcess.face", data=data)
        self.isLoggedIn = "ENPASSTGC" in self.session.cookies.get_dict()

    def fetchCourseList(self):
        self.lectures = []

        if not self.isLoggedIn:
            raise RuntimeError("로그인을 먼저 해야함!")

        self.session.get("http://uclass.uos.ac.kr/sso_main.jsp")
        self.session.get("http://uclass.uos.ac.kr/Main.do?cmd=viewHome")
        res = self.session.get("http://uclass.uos.ac.kr/Study.do?cmd=viewStudyMyClassroom")
        soup = BeautifulSoup(res.content, "html.parser")
        table = soup.find("table")
        self.courseList = table.find_all("a", { "target": "_parent", "title": None })

        return list(map(lambda course : course.text, self.courseList))

    @staticmethod
    def _convertLectureListToString(chapter):
        ret = {}
        ret["name"] = chapter["tds"][0].text.strip()
        ret["children"] = list(map(lambda tds : { 
            "name" : tds[0].text.strip(),
            "status" : tds[2].text.strip()
            }, chapter["children"]))
        return ret

    def fetchLectureList(self, courseNumber):
        if not self.courseList:
            raise RuntimeError("수업 목록을 먼저 불러와야 함!")

        if self.isLoggedIn:
            for k, v in self.session.cookies.get_dict().items():
                self.driver.add_cookie({ "name" : k, "value" : v })

        self.driver.get("http://uclass.uos.ac.kr" + self.courseList[courseNumber]["href"])
        self.driver.get("http://uclass.uos.ac.kr/AuthGroupMenu.do?cmd=goMenu&mcd=menu_00087")
        lectureTable = self.driver.find_element_by_xpath("//table[@class='list-table']")
        lectureRows = lectureTable.find_elements_by_xpath("//tbody/tr")

        for row in lectureRows:
            tds = row.find_elements_by_tag_name("td")
            try:
                row.find_element_by_tag_name("a")
                self.lectures[-1]["children"].append(tds)
            except:
                self.lectures.append({ "tds" : tds, "children" : []})

        jsToBeInserted = '''
            var StudyRecordDTO = new Object();
            var lessonElementId = ""; // LESN_200909190851f5d41aae
            var learningControl = "date";
            var inStudyDate = "";
            var recordUpdateComplete = false;

            function viewStudyContents() {
                // 콘텐츠 정보 조회
                StudyWork.viewStudyContents(lessonElementId, viewStudyContentsCallback);
            }

            function viewStudyContentsCallback(ProcessResultDTO) {
                StudyRecordDTO = ProcessResultDTO.returnDto;
                var lessonElementDTO = StudyRecordDTO.lessonElementDTO;
                inStudyDate = StudyRecordDTO.inStudyDate; // -1:학습기간이전, 0:학습기간중, 1:학습기간경과후
            }

            function editStudyRecord(seconds) {
                try {
                    if (StudyRecordDTO.elementType == "video" && playerType == "mp4" && videoPlayer != null) {
                        if (videoPlayer.video.time != undefined) {
                            StudyRecordDTO.studySeekTime = parseInt(videoPlayer.video.time);
                        }
                    }
                    
                    // 학습시간 계산
                    StudyRecordDTO.studySessionTime = seconds;
                    
                    StudyWork.editStudyRecord(StudyRecordDTO, learningControl, inStudyDate, function(){{ recordUpdateComplete = true }});
                } catch(e) {
                }
            }
        '''

        jsAddCodeToWindow = '''
            var importPaths = ["/dwr/engine.js", "/dwr/util.js", "/dwr/interface/StudyWork.js"];
            for (let path of importPaths)
            {{
                let s = window.document.createElement("script");
                s.src = path;
                window.document.head.appendChild(s);
            }}

            let s = window.document.createElement("script");
            s.text = `{}`;
            window.document.head.appendChild(s);
        '''.format(jsToBeInserted)

        self.driver.execute_script(jsAddCodeToWindow)

        sleepUntil(lambda : self.driver.execute_script("return typeof dwr.engine !== 'undefined'")\
            and self.driver.execute_script("return typeof dwr.util !== 'undefined'")\
            and self.driver.execute_script("return typeof StudyWork !== 'undefined'"))

        return list(map(self._convertLectureListToString, self.lectures))

    def refreshLectureList(self):
        if not self.driver.execute_script("return typeof dwr.engine !== 'undefined'"):
            raise RuntimeError("새로고침은 강의 목록을 먼저 불러와야 함!")
        
        res = requests.get("http://uclass.uos.ac.kr/AuthGroupMenu.do?cmd=goMenu&mcd=menu_00087", cookies=self.cookies)
        soup = BeautifulSoup(res.content, "html.parser")
        lectureTable = soup.find("table", class_="list-table")
        lectureRows = lectureTable.find("tbody").find_all("tr")

        ret = []
        for row in lectureRows:
            tds = row.find_all("td")
            if row.find("a"):
                ret[-1]["children"].append({ "name" : tds[0].text.strip(), "status" : tds[2].text.strip() })
            else:
                ret.append({ "name" : tds[0].text.strip(), "children" : [] })

        return ret

    def freeMySoul(self, chapter, lecture, seconds):
        if not self.lectures:
            raise RuntimeError("수업 목록을 먼저 불러와야 함!")

        href = self.lectures[chapter]["children"][lecture][1].find_element_by_tag_name("a").get_attribute("href")
        index = href.find("LESN_")

        self.driver.execute_script("lessonElementId = '{}'".format(href[index:]))
        self.driver.execute_script('''
            StudyRecordDTO = new Object();
            viewStudyContents();
        ''')

        sleepUntil(lambda : self.driver.execute_script("return Object.keys(StudyRecordDTO).length > 0"))

        self.driver.execute_script('''
            recordUpdateComplete = false;
            editStudyRecord({});
        '''.format(seconds))

        sleepUntil(lambda : self.driver.execute_script("return recordUpdateComplete"))