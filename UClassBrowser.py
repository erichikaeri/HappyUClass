from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

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
        self.isLoggedIn = False
        self.courseList = []
        self.lectures = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.close()

    def close(self):
        self.driver.close()

    def login(self, id, password):
        self.driver.get("https://portal.uos.ac.kr/user/login.face");

        loginId = self.driver.find_element_by_xpath("//input[@id='id']")
        loginPwd = self.driver.find_element_by_xpath("//input[@id='pw']")
        loginSubmit = self.driver.find_element_by_class_name("btn_login")

        loginId.send_keys(id)
        loginPwd.send_keys(password)
        loginSubmit.click()
        self.isLoggedIn = True

    def fetchCourseList(self):
        self.lectures = []

        if not self.isLoggedIn:
            raise RuntimeError("로그인을 먼저 해야함!")

        self.driver.get("http://uclass.uos.ac.kr/sso_main.jsp")
        self.driver.switch_to.frame("main")
        self.driver.switch_to.frame("bodyFrame")
        table = self.driver.find_element_by_xpath("//table[@summary='과목 목록']")
        self.courseList =  table.find_elements_by_xpath("//a[@target='_parent' and not(@title)]")
        
        return list(map(lambda course : course.text, self.courseList))

    @staticmethod
    def _convertLectureListToString(chapter):
        ret = {}
        ret["name"] = chapter["tds"][0].text.strip()
        ret["children"] = list(map(lambda tds : { 
            "name" : tds[0].text.strip(),
            "status" : tds[2].text
            }, chapter["children"]))
        return ret

    def fetchLectureList(self, courseNumber):
        if not self.courseList:
            raise RuntimeError("수업 목록을 먼저 불러와야 함!")

        self.driver.get(self.courseList[courseNumber].get_attribute("href"))
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