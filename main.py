def checkIntAndRange(checkThis, length):
    try:
        checkThis = int(checkThis)
    except:
        print("정수를 입력하세요.")
        return -1

    if checkThis not in range(0, length):
        print("범위 내의 정수를 입력하세요.")
        return -1

    return checkThis

def loginSequence(uclass):
    while True:
        try:
            userId = input("와이즈 아이디 : ")
            password = input("와이즈 비밀번호 : ")

            print("로그인 하는 중...")
            uclass.login(userId, password)
            break
        except:
            print("로그인 실패")

def courseListSequence(uclass):
    print("불러오는 중...")
    courseList = uclass.fetchCourseList()

    for i, course in enumerate(courseList):
        print("[{}] {}".format(i, course))
    
    while True:
        courseNum = input("과목을 선택하세요: ")
        courseNum = checkIntAndRange(courseNum, len(courseList))
        if courseNum >= 0:
            return courseNum

def lectureListSequence(uclass, course):
    print("불러오는 중...")
    chapterList = uclass.fetchLectureList(course)

    maxLen = 0
    for chapter in chapterList:
        for lecture in chapter["children"]:
            maxLen = max(maxLen, len(lecture["name"]))
    
    maxLen += 3

    for i, chapter in enumerate(chapterList):
        print("[{}] {}".format(i, chapter["name"]))
        for j, lecture in enumerate(chapter["children"]):
            print("\t[{}] {}".format(j, lecture["name"]))
            print("\t\t{}\n".format(lecture["status"]))

    return chapterList
    
def lectureSelectSequence(uclass, chapterList):
    chapter = -1
    print("*돌아가려면 back을 치세요.")
    print("**위 [] 안의 번호를 기준으로 입력하세요.")
    while True:
        chapter = input("단원 번호를 입력하세요 : ")
        if chapter == "back":
            return -1, -1

        chapter = checkIntAndRange(chapter, len(chapterList))
        if chapter >= 0:
            break
    
    lecture = -1
    while True:
        lecture = input("강의 번호를 입력하세요 : ")
        if lecture == "back":
            return -1, -1

        lecture = checkIntAndRange(lecture, len(chapterList[chapter]["children"]))
        if lecture >= 0:
            break

    return chapter, lecture

def finalSequence(uclass, chapter, lecture):
    seconds = input("몇 초 늘리시겠습니까? : ")
    uclass.freeMySoul(chapter, lecture, seconds)
    print("성공")

if __name__ == "__main__":
    print("초기화 하는 중... 좀 걸림")
    from UClassBrowser import UClassBrowser

    with UClassBrowser() as uclass:
        loginSequence(uclass)

        while True:
            course = courseListSequence(uclass)
            chapterList = lectureListSequence(uclass, course)

            while True:
                chapter, lecture = lectureSelectSequence(uclass, chapterList)
                if chapter < 0:
                    break

                finalSequence(uclass, chapter, lecture)
        