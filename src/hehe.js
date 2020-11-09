let [month, date, year] = new Date().toLocaleDateString("kr").split("/")
console.log(date)

let matched = "20201109".match(/([0-9]{4})([0-9]{2})([0-9]{2})/)
console.log(matched[0])
console.log(2020 > NaN)
console.log(parseInt(matched[2]))
console.log(parseInt(matched[3]))