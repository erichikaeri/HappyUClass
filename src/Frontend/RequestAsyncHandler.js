const { ipcRenderer } = require("electron")

class RequestAsyncHandler {
    constructor() {
        this.queues = {}
        this.waitings = {}
        this.nameMap = {}
    }

    // https://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid
    _uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      }

    register(requestName, replyName) {
        if (this.nameMap[requestName] !== undefined
            || this.nameMap[replyName] !== undefined)
            throw new Error(`Duplicate request name or replay name: ${requestName}, ${replyName}`)

        this.nameMap[requestName] = replyName
        this.nameMap[replyName] = requestName

        ipcRenderer.on(replyName, (event, arg) => {
            let id = arg.id

            if (this.queues[id] === undefined)
                this.queues[id] = []

            this.queues[id].push(arg.arg)

            if (this.waitings[id] !== undefined) {
                this.waitings[id]()
                this.waitings[id] = undefined
            }
        })
    }

    request(requestName, arg) {
        let id = this._uuidv4()
        ipcRenderer.send(requestName, {
            id: id,
            arg: arg
        })

        return id
    }

    async getResponse(id) {
        let queue = this.queues[id]
        if (queue === undefined || queue.length === 0) {
            await new Promise(resolve => {
                this.waitings[id] = resolve
            })
        }

        return this.queues[id].shift()
    }

    close(id) {
        this.queues[id] = undefined
        this.waitings[id] = undefined
    }
}

const requestAsyncHandler = new RequestAsyncHandler()

module.exports = {
    requestAsyncHandler: requestAsyncHandler
}