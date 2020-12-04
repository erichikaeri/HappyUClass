const fs = require("fs")
// const ffmpeg = require("ffmpeg-static")
const { spawn } = require("child_process")
const path = require("path")

class ParsingError extends Error {
    constructor(message) {
        super(message)
        this.name = "ParsingError"
    }
}

class DownloadError extends Error {
    constructor(message) {
        super(message)
        this.name = "DownloadError"
    }
}

function parseUrl(url) {
    if (!(url.includes("youtube") || url.includes("youtu.be"))){
        let error = new ParsingError(`Url was ${url}`)
        throw error
    }

    return url
}

class Downloader {
    /**
     * Downloads from youtube. Support for Uclass hosted videos
     * will be added someday.
     * 
     * @param {string} url - youtube url.
     * @param {string} savePath - save path.
     * @param {function} onProgress - callback function whose parameter is
     *      percentage completed (string). Do not count on this function to check 
     *      if download is complete.
     * @throws {ParsingError} - if url is not youtube or parser is stupid.
     * @throws {DownloadError} - if download fails.
     * 
     */
    async download(url, savePath, onProgress) {
        url = parseUrl(url)

        let outputPath = path.join(savePath, String.raw`%(title)s.%(ext)s`)

        const cp = spawn(
            path.join(".", "External", "python-3.8.6-embed-win32", "python"), 
            [
                path.join(".", "External", "youtube-dl.exe"),
                url,
                // "-f",
                // "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
                // "--ffmpeg-location",
                // ffmpeg,
                "--merge-output-format",
                "mp4",
                "-o",
                outputPath
            ])

        let stdoutLog = []
        let stderrLog = []

        function parsePercentage(data, log) {
            log.push(data.toString())
            let fullString = log.join("")
            const re = /\[download\] *(\d+(\.\d+)?)%/g;
        
            let m = null;
            do {
                let temp = re.exec(fullString);
                if (temp === null)
                    break;
        
                m = temp
            } while (true);
        
            if (m !== null)
                onProgress(m[1])
        }

        cp.stdout.on("data", (data) => parsePercentage(data, stdoutLog))
        cp.stderr.on("data", (data) => parsePercentage(data, stderrLog))

        await new Promise(resolve => {
            cp.on("close", resolve)
        })

        let stdoutString = stdoutLog.join("")
        let stderrString = stderrLog.join("")

        if (stdoutString.includes("ERROR") ||
            stderrString.includes("ERROR")) {

            let i = stdoutString.indexOf("ERROR")
            let j = stderrString.indexOf("ERROR")

            console.log(i)
            console.log(j)

            throw new DownloadError(stdoutString.substring(i) + stderrString.substring(j))
        }
    }
}

module.exports = {
    Downloader: Downloader
}