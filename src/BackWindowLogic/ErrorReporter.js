const { dialog } = require("electron")

function report(error) {
    console.log(error.message + "\n" + error.stack)
    dialog.showMessageBoxSync({
        title: error.name,
        message: error.message + "\n" + error.stack
    })
}

module.exports = {
    report: report
}