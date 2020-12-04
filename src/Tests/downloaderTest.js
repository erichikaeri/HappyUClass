const { Downloader } = require("../BackWindowLogic/Downloader")

const zankoku = "https://youtu.be/y5wkebBCwAE"
const ML = "https://www.youtube.com/watch?v=UrX02HQTtLA&feature=emb_title&ab_channel=ha-jinyu"
const socsci = "https://youtu.be/x9k15SIvPDU"

process.chdir("../")

async function main()
{
    let dl = new Downloader()

    try {
        await dl.download(zankoku, ".\\", (percentage) => {
            console.log(percentage)
        })
    } catch (error) {
        console.log(error.message)
    }
}

main()