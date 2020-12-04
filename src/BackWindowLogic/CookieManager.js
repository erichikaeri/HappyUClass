const fetch = require("node-fetch")

function makeCookieObjects(response)
{
    let ret = []
    let domain = new URL(response.url).hostname
    let cookies = response.headers.get("set-cookie")
    if (cookies === null) return null;

    cookies = cookies.split(',')

    for (let cookieString of cookies)
    {
        let cookieObject = {}
        cookieObject["Domain"] = domain

        cookieString = cookieString.trim()
        let entries = cookieString.split(';')
        
        for (let entry of entries)
        {
            let [ key, value ] = entry.split('=')
            if (!["Path", "Expires", "Max-Age", "Domain", "Secure", "HttpOnly"].some(e => e === key))
                cookieObject["keyValue"] = { key: key, value: value}
            else
                cookieObject[key] = value
        }

        ret.push(cookieObject)
    }

    return ret
}

function cookieToString(cookie, domain)
{
    if (cookie["Domain"] !== domain)
        return ""

    return cookie.keyValue.key + "=" + cookie.keyValue.value
}

class CookieManager
{
    constructor()
    {
        this.cookies = {}
    }

    /**
     * Parses and adds cookies from the Response object returned by fetch.
     * 
     * @param {Object} response - Response object returned by fetch.
     */
    addCookiesFromResponse(response)
    {
        let newCookies = makeCookieObjects(response)
        if (newCookies === null) return

        let domain = new URL(response.url).hostname

        if (this.cookies[domain] === undefined)
        {
            this.cookies[domain] = newCookies
            return
        }

        newCookies.forEach((cookie) => {
            let exists = this.cookies[domain].find(e => e.keyValue.key == cookie.keyValue.key)
            if (exists === undefined)
                this.cookies[domain].push(cookie)
            else
                exists.keyValue.value = cookie.value
        })
    }

    /**
     * Follows redirects until response has no location header 
     * accumulating cookies encountered in the process.
     * 
     * @param {Object} response - Response object returned by fetch
     *      that has location header to follow. Does nothing if None.
     * @return {Object} - the last response after following redirects.
     */
    async followRedirects(response)
    {
        do
        {
            let url = response.headers.get("location")
            if (url == null) break;
    
            response = await fetch(url, {
                headers:
                {
                    cookie: this.toString(url),
                },
                redirect: "manual"
            })
    
            this.addCookiesFromResponse(response)
    
        } while (true)

        return response
    }

    /**
     * Returns the cookie string for the given url.
     * 
     * @param {string} url - url.
     * @return {string} - the cookie string
     */
    toString(url)
    {
        let cookieStrings = []
        let domain = new URL(url).hostname

        if (this.cookies[domain] === undefined)
            return ""

        this.cookies[domain].forEach((e) => {
            let cookieString = cookieToString(e, domain)

            if (cookieString.length > 0)
                cookieStrings.push(cookieString)
        })
        return cookieStrings.join(';')
    }
}

module.exports = {
    CookieManager: CookieManager
}