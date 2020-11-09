/**
 * The following functions are trimmed down versions 
 * of the original script used by the portal.
 */

var StudyRecordDTO;
var lessonElementId = ""; // like LESN_20110414080318fc6370
var inStudyDate = "";
var recordUpdateComplete = false;

function viewStudyContents() {
    StudyRecordDTO = undefined
    recordUpdateComplete = false
    // 콘텐츠 정보 조회
    StudyWork.viewStudyContents(lessonElementId, viewStudyContentsCallback);
}

function viewStudyContentsCallback(ProcessResultDTO) {
    console.log("callback called")
    StudyRecordDTO = ProcessResultDTO.returnDto;
    inStudyDate = StudyRecordDTO.inStudyDate; // -1:학습기간이전, 0:학습기간중, 1:학습기간경과후
}

function editStudyRecord(seconds) {
    try {
        // 학습시간 계산
        StudyRecordDTO.studySessionTime = seconds;
        StudyWork.editStudyRecord(StudyRecordDTO, "date", inStudyDate, function(){ recordUpdateComplete = true });
    } catch(e) {
    }
}

var importPaths = ["/dwr/engine.js", "/dwr/util.js", "/dwr/interface/StudyWork.js"];
for (let path of importPaths)
{
    let s = window.document.createElement("script");
    s.src = path;
    window.document.head.appendChild(s);
}
console.log("This somehow prevents an error from being thrown. Do not remove")