/**
 * The following functions are trimmed down versions 
 * of the original script used by the portal.
 */

// 과목 목록 조회
function viewCourseListTrimmed() {
    studyCourseList = undefined;
    CourseForm = new Object()
    CourseForm.curPage = 1;
    CourseForm.searchKey = "";
    CourseForm.searchTxt = "";
            
    MCourseWork.viewLearnerCourseList2(CourseForm, viewCourseListCallbackTrimmed);
}

// 과목 목록 조회 Callback
function viewCourseListCallbackTrimmed(ProcessResultListDTO) {
    studyCourseList	= ProcessResultListDTO.returnList;
}