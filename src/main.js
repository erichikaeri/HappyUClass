const { dialog, app, BrowserWindow, ipcMain } = require("electron")
const { getUclassCookieString } = require("./BackWindowLogic/UclassHelpers")
const { Fetcher, Learner } = require("./BackWindowLogic/UclassWindow")
const { Downloader } = require("./BackWindowLogic/Downloader")
const { report } = require("./BackWindowLogic/ErrorReporter")

const dl = new Downloader()
let g_fetcher = undefined
let g_learner = undefined

function createWindow(show = true) {
    // show = true

    const win = new BrowserWindow({
        width: 600,
        height: 600,
        webPreferences: {
            nodeIntegration: true
        },
        resizable: false,
        show: show
    })

    // win.openDevTools()

    return win
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

/**
 * Handles the login request
 * 
 * @param {Object} arg - has username and password as members.
 * @return {boolean} - true if succeeded else false.
 */
ipcMain.on("loginRequest", async (event, arg) => {
    let ret;

    let uclassCookieString =
        await getUclassCookieString(arg.username, arg.password)

    if (uclassCookieString === null)
        ret = false
    else {
        g_fetcher.init(uclassCookieString)
        g_learner.init(uclassCookieString)
        ret = true
    }

    event.reply("loginReply", ret)
})

/**
 * Handles the request for study course list
 * 
 * @param {Object} arg - fetches anew if true. Returns cached otherwise.
 * @return {Object} - studyCourseList.
 */
ipcMain.on("studyCourseListRequest", async (event, arg) => {
    let ret = {
        id: arg.id,
        arg: {
            studyCourseList: undefined,
            error: undefined
        }
    }

    try {
        ret.arg.studyCourseList = await g_fetcher.getStudyCourseList(arg.arg)
    }
    catch (error) {
        if (error.name !== "Busy")
            report(error)

        ret.arg.error = error.name
    }

    event.reply("studyCourseListReply", ret)
})

/**
 * Handles the request to update study time.
 * The context needs to be set to the right course before this can happen.
 * See setCourseRequest.
 * 
 * @param {Object} arg - Contains lessonId (string) and seconds (int).
 * @return {Object} - seconds learned.
 */
ipcMain.on("learnRequest", async (event, arg) => {
    let args = arg.arg

    let ret = {
        id: arg.id,
        arg: {
            seconds: 0,
            error: undefined
        }
    }

    try {
        await g_learner.learn(args.lessonId, args.seconds)
        ret.arg.seconds = args.seconds
    }
    catch (error) {
        if (error.name !== "Busy")
            report(error)
        
        ret.arg.error = error.name
    }

    event.reply("learnReply", ret)
})

/**
 * Before calling updateStudyTime, course needs to be set in the context.
 * This handles just that.
 * 
 * @param {int} arg - course index.
 */
ipcMain.on("setCourseRequest", async (event, arg) => {
    let course = (await g_fetcher.getStudyCourseList())[arg]
    g_learner.setCourse(course.courseDTO.courseId)
    event.reply("setCourseReply", arg)
})

/**
 * @param {Object} arg - has members lessonElementId and url
 * @return {Object} - lessonElementId (string), percentage (int), status (string)
 */
ipcMain.on("downloadRequest", async (event, arg) => {
    let id = arg.id
    let content = arg.arg

    let savePath = dialog.showOpenDialogSync({
        properties: ["openDirectory"]
    })

    let ret = {
        id: id,
        arg: {
            lessonElementId: content.lessonElementId,
            percentage: 0,
            status: "downloading",
            error: undefined
        }
    }
    
    if (savePath === undefined) {
        ret.arg.status = "cancelled"
    }
    else {
        savePath = savePath[0]
    
        try {
            await dl.download(content.url, savePath, (curPerc) => {
                console.log(curPerc)
                ret.arg.percentage = curPerc
                event.reply("downloadReply", ret)
            })

            ret.arg.status = "done"
    
        } catch (error) {
            report(error)
            ret.arg.status = "error"
            ret.arg.error = error.name
        }
    }

    event.reply("downloadReply", ret)
})

/**
 * Creates fetcher window and UI window.
 */
async function main() {
    await app.whenReady()

    // init background windows
    g_fetcher = new Fetcher(createWindow(false))
    g_learner = new Learner(createWindow(false))

    // init UI window
    const uiWin = createWindow(true)
    uiWin.removeMenu()

    uiWin.on("close", () => {
        g_fetcher.close()
        g_learner.close()
    })

    uiWin.loadFile("./src/Html/main.html")
}

main()