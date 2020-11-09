const sleep = require('util').promisify(setTimeout);
const fs = require("fs").promises

class UclassWindow {
    static uclassBaseUrl
        = "http://uclass.uos.ac.kr/"

    constructor(window, injectionFile) {
        this.win = window
        this.loadPromise = this.win.loadURL(UclassWindow.uclassBaseUrl)
        this.readinjectionPromise = fs.readFile(injectionFile)
        this.loggedIn = false
    }

    async setCookie(cookieString) {
        await this.loadPromise
        await this.win.webContents
            .executeJavaScript(`document.cookie = "${cookieString}"`)
        this.loggedIn = true
    }

    async inject() {
        let injection = await this.readinjectionPromise
        await this.win.webContents.executeJavaScript(injection.toString())
    }

    async loadUrl(url) {
        return await this.win.loadURL(url)
    }

    async execute(javascript) {
        return await this.win.webContents.executeJavaScript(javascript)
    }

    close()
    {
        this.win.close()
    }
}

class Fetcher {
    static uclassUrl
        = "http://uclass.uos.ac.kr/MCourse.do?cmd=viewLearnerCourseList"

    constructor(window) {
        this.uclass = new UclassWindow(window, "./src/BackWindowLogic/FetcherInjection.js")
        this.busy = false
    }

    async init(cookieString) {
        await this.uclass.setCookie(cookieString)
        await this.uclass.loadUrl(Fetcher.uclassUrl)
        await this.uclass.inject()
    }

    /**
     * Getter.
     * 
     * @param {boolean} fetchNew - refetches studyCourseList if true.
     * @return {Object} - studyCourseList
     * @throws {Busy} - if busy
     * @throws electron errors
     */
    async getStudyCourseList(fetchNew) {
        if (this.busy)
        {
            let error = new Error("wait for previous getStudyCourseList to return")
            error.name = "Busy"
            throw error
        }

        this.busy = true

        let studyCourseList;

        try {
            if (fetchNew)
                await this.uclass.execute("viewCourseListTrimmed();")

            while (true) {
                studyCourseList =
                    await this.uclass.execute("studyCourseList")

                if (studyCourseList === undefined ||
                    studyCourseList.length == 0)
                    await sleep(100)
                else
                    break
            }
        }
        catch (err) {
            throw err
        }
        finally {
            this.busy = false
        }

        return studyCourseList
    }

    close() {
        this.uclass.close()
    }
}

class Learner {
    static courseUrlFront
        = "http://uclass.uos.ac.kr/Main.do?cmd=viewCourseMain&mainDTO.courseId=";

    static courseUrlBack
        = "&gubun=study_course";

    static learnUrl
        = "http://uclass.uos.ac.kr/AuthGroupMenu.do?cmd=goMenu&mcd=menu_00087";

    constructor(window) {
        this.uclass = new UclassWindow(window, "./src/BackWindowLogic/LearnerInjection.js")
        this.currentCourseId = undefined
        this.busy = false
    }

    async init(cookieString) {
        await this.uclass.setCookie(cookieString)
    }

    async setCourse(courseId) {
        this.currentCourseId = courseId

        let url = Learner.courseUrlFront + courseId + Learner.courseUrlBack
        await this.uclass.loadUrl(url)
        await this.uclass.loadUrl(Learner.learnUrl)
        await this.uclass.inject()
    }

    /**
     * Updates study time and wait until it finishes.
     * 
     * @param {string} lessonElementId - lessonElementId (contained in studyCourseList).
     * @param {int} seconds - time in seconds to add to the current study time. 
     *      Negative value decreases the study time.
     * @throws {Busy} - if busy
     * @throws electron errors.
     */
    async learn(lessonElementId, seconds) {
        if (this.busy)
        {
            let error = new Error("wait for previous learn to return")
            error.name = "Busy"
            throw error
        }

        this.busy = true

        try {
            await this.uclass.execute(`lessonElementId = "${lessonElementId}"`)
            await this.uclass.execute("viewStudyContents()")

            while (true) {
                let dto = await this.uclass.execute("StudyRecordDTO")
                if (dto === undefined)
                    await sleep(100)
                else
                    break
            }

            await this.uclass.execute(`editStudyRecord(${seconds})`)

            while (true) {
                let complete = await this.uclass.execute("recordUpdateComplete")
                if (!complete)
                    await sleep(100)
                else
                    break
            }
        }
        catch (error) {
            throw error
        }
        finally {
            this.busy = false
        }
    }

    close() {
        this.uclass.close()
    }
}

module.exports = {
    Fetcher: Fetcher,
    Learner: Learner
}