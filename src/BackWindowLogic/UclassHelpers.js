const fetch = require("node-fetch");
const { CookieManager } = require("./CookieManager")

/**
 * A helper function to log in and make a cookie string that is ready for
 * use in http header for domain uclass.uos.ac.kr
 * (i.e. cookies are separated by semicolon).
 * 
 * @param {string} username - username.
 * @param {string} password - password.
 * @return {string} - cookie string.
 */
async function getUclassCookieString(username, password)
{
    /**
     * The way the portal works is, the portal main and the uclass
     * are separate pages with different login credentials. You cannot
     * log in to uclass with your normal username and password.
     * However when a user logs in through portal.uos.ac.kr, 
     * the user receives log in cookies, is redirected to psso.uos.ac.kr
     * for more cookies and is redirected back to portal.uos.ac.kr 
     * but this time since the user has the log in cookies, log in succeeds.
     * The psso.uos.ac.kr cookies are used the first time the user fetches
     * uclass.uos.ac.kr. Since the user does not have cookies for 
     * uclass.uos.ac.kr, the user is redirected to psso.uos.ac.kr to check
     * if the user logged in through the main page. If he did then the
     * user is given cookies for uclass.uos.ac.kr and is redirected
     * to uclass.uos.ac.kr where uclass login succeeds.
     * 
     */
    const loginUrl = "https://portal.uos.ac.kr/user/loginProcess.face"
    const uclassLoginUrl = "http://uclass.uos.ac.kr/sso_main.jsp"

    let cookieManager = new CookieManager()

    let data = 
    {
        "_enpass_login_" : "submit",
        "langKnd"        : "ko",
        "loginType"      : "normal",
        "returnUrl"      : "",
        "ssoId"          : username,
        "password"       : password
    }

    let dataWWW = new URLSearchParams();
    for (let key in data)
        dataWWW.append(key, data[key])

    let response = await fetch(loginUrl, {
        method: "POST",
        body: dataWWW,
        redirect: "manual"
    })

    if (response.status != 302)
        return null

    cookieManager.addCookiesFromResponse(response)

    if (response.headers.get("location") !== null)
        response = await cookieManager.followRedirects(response)
    else
        console.log("error")

    response = await fetch(uclassLoginUrl, {
        redirect: "manual"
    })

    response = await cookieManager.followRedirects(response)
    
    return cookieManager.toString(uclassLoginUrl)
}

module.exports = {
    getUclassCookieString: getUclassCookieString,
}