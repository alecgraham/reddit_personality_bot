
const readline = require('readline');
const fs = require('fs');
const PersonalityTextSummaries = require('personality-text-summary');
const v3EnglishTextSummaries = new PersonalityTextSummaries({
  locale: 'en',
  version: 'v3'
});

var rawdata = fs.readFileSync('./data/temp.json')
var personalityProfile = JSON.parse(rawdata)

var textSummary = v3EnglishTextSummaries.getSummary(personalityProfile);
fs.writeFile("./data/temp.txt", textSummary,(err) => {
  if(err) console.log(err);
  console.log("Summary generated.");
});
