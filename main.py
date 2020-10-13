import tkinter
from threading import Thread
from ScrollableFrame import ScrollableFrame

class Global:
    title = "온라인강의실 자율학습도우미"
    logoText = "서울시립대학교\n온라인강의실 자율학습도우미"
    loginIdLabel = "아이디"
    loginPasswordLabel = "패스워드"
    loginButton = "로그인"
    loadingText = "불러오는 중..."
    selectCourse = "과목을 선택하세요"
    selectLecture = "강의를 선택하세요"

class ScreenBase:
    def __init__(self, window, manager):
        self.window = window
        self.manager = manager
        self.centerFrame = tkinter.Frame()
        self.loadingLabel = tkinter.Label(master=self.centerFrame, text=Global.loadingText, font=(None, 20))
        self.loadingLabel.pack()

    def show(self):
        self.centerFrame.pack(expand=True)

    def destory(self):
        self.centerFrame.destroy()

class LoginScreen(ScreenBase):
    def __init__(self, window, manager):
        super().__init__(window, manager)
        self.logo = tkinter.Label(master=self.centerFrame, text=Global.logoText, font=(None, 23))
        self.loginFrame = tkinter.Frame(master=self.centerFrame, relief=tkinter.RAISED, borderwidth=2)

        loginId = tkinter.Label(master=self.loginFrame, text=Global.loginIdLabel)
        loginPassword = tkinter.Label(master=self.loginFrame, text=Global.loginPasswordLabel)
        self.loginIdEntry = tkinter.Entry(master=self.loginFrame)
        self.loginPasswordEntry = tkinter.Entry(master=self.loginFrame)

        loginId.grid(row=0, column=0)
        self.loginIdEntry.grid(row=0, column=1)
        loginPassword.grid(row=1, column=0)
        self.loginPasswordEntry.grid(row=1, column=1)

        self.loginButton = tkinter.Button(master=self.centerFrame, text=Global.loginButton,\
            width=10, height=2, command=self._onLoginButtonClicked)

    def show(self):
        super().show()
        Thread(target=self._initUClass).start()

    def _initUClass(self):
        from UClassBrowser import UClassBrowser
        self.manager.uclass = UClassBrowser()
        self.window.after(0, self._showLoginForm)

    def _showLoginForm(self):
        '''
        Must be called from UI thread
        '''
        self.loadingLabel.destroy()
        self.logo.pack()
        self.loginFrame.pack(pady=30)
        self.loginButton.pack()

    def _onLoginButtonClicked(self):
        self.loginIdEntry["state"] = "disable"
        self.loginPasswordEntry["state"] = "disable"
        self.loginButton["state"] = "disable"
        Thread(target=self._login).start()

    def _login(self):
        try:
            self.manager.uclass.login(self.loginIdEntry.get(), self.loginPasswordEntry.get())
            self.window.after(0, lambda: self.manager.nextScreen())
        except:
            pass

class CourseListScreen(ScreenBase):
    def __init__(self, window, manager):
        super().__init__(window, manager)

    def show(self):
        super().show()
        Thread(target=self._fetchCourseList).start()

    def _fetchCourseList(self):
        courseList = self.manager.uclass.fetchCourseList()
        self.window.after(0, lambda: self._showCourseList(courseList))

    def _showCourseList(self, courseList):
        self.loadingLabel.destroy()
        tkinter.Label(master=self.centerFrame, text=Global.selectCourse).pack()
        for i, course in enumerate(courseList):
            tkinter\
                .Button(master=self.centerFrame, text=course, anchor="w", command=lambda localI = i: self._onCourseButtonClicked(localI))\
                .pack(pady=5, fill=tkinter.BOTH)

    def _onCourseButtonClicked(self, number):
        self.manager.courseNumber = number
        self.manager.nextScreen()

class LectureListScreen(ScreenBase):
    def __init__(self, window, manager):
        super().__init__(window, manager)
        self.scrollableFrame = ScrollableFrame(window)
        self.courseNumber = manager.courseNumber

    def show(self):
        super().show()
        Thread(target=self._fetchLectureList).start()

    def _fetchLectureList(self):
        chapterList = self.manager.uclass.fetchLectureList(self.courseNumber)
        self.window.after(0, lambda: self._showLectureList(chapterList))

    def _showLectureList(self, chapterList):
        self.centerFrame.destroy()
        self.scrollableFrame.pack(expand=True, fill=tkinter.BOTH)

        tkinter.Label(self.scrollableFrame.frame, text=Global.selectLecture, font=(None, 20)).pack(expand=True, fill=tkinter.BOTH)

        f = tkinter.Frame(self.scrollableFrame.frame)
        f.pack(expand=True, fill=tkinter.X)

        row = 0
        for i, chapter in enumerate(chapterList):
            tkinter.Label(f, text=chapter["name"], anchor="w")\
                    .grid(row=row, column=0, columnspan=2, sticky="we")
            row += 1
            for j, lecture in enumerate(chapter["children"]):
                tkinter\
                    .Button(master=f, text=lecture["name"], anchor="w")\
                    .grid(row=row, column=0, sticky="we")
                tkinter\
                    .Label(master=f, text=lecture["status"], anchor="w")\
                    .grid(row=row, column=1, sticky="we", padx=5)

                row += 1

class UIManager:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title(Global.title)
        self.window.geometry("500x500")
        self.window.resizable(width=False, height=False)
        self.uclass = None

        self.sequenceNodes = [LoginScreen, CourseListScreen, LectureListScreen]
        self.sequenceEdges = [1, 2, 3]
        self.currentNode = 0

        self.courseNumber = None

        self.screen = self.sequenceNodes[self.currentNode](self.window, self)

    def run(self):
        self.screen.show()
        self.window.mainloop()

        if self.uclass:
            self.uclass.close()

    def nextScreen(self):
        '''
        Must be called from UI thread
        '''
        self.currentNode = self.sequenceEdges[self.currentNode]
        self.screen.destory()
        self.screen = self.sequenceNodes[self.currentNode](self.window, self)
        self.screen.show()

# def lectureSelectSequence(uclass, chapterList):
#     chapter = -1
#     print("*돌아가려면 back을 치세요.")
#     print("**위 [] 안의 번호를 기준으로 입력하세요.")
#     while True:
#         chapter = input("단원 번호를 입력하세요 : ")
#         if chapter == "back":
#             return -1, -1

#         chapter = checkIntAndRange(chapter, len(chapterList))
#         if chapter >= 0:
#             break
    
#     lecture = -1
#     while True:
#         lecture = input("강의 번호를 입력하세요 : ")
#         if lecture == "back":
#             return -1, -1

#         lecture = checkIntAndRange(lecture, len(chapterList[chapter]["children"]))
#         if lecture >= 0:
#             break

#     return chapter, lecture

# def finalSequence(uclass, chapter, lecture):
#     seconds = input("몇 초 늘리시겠습니까? : ")
#     uclass.freeMySoul(chapter, lecture, seconds)
#     print("성공")

if __name__ == "__main__":
    uiManager = UIManager()
    uiManager.run()