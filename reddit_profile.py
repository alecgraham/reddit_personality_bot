
import requests
from requests.auth import HTTPBasicAuth
import sys
import json
from ibm_watson import PersonalityInsightsV3
import pandas as pd
from Naked.toolshed.shell import execute_js, muterun_js
from config import *

def getPersonalityInsight(data,username=None):
    try:
        #use saved profile to limit API calls
        with open('./data/profiles/'+username+'_profile.json') as json_file:
            profile = json.load(json_file)
        if len(data.split()) > profile['word_count'] * 2:
            raise 'error: old saved profile'
    except:
        personality_insights = PersonalityInsightsV3(
            version='2017-10-13',
            iam_apikey=iam_apikey,
            url='https://gateway-wdc.watsonplatform.net/personality-insights/api'
        )
        personality_insights.disable_SSL_verification()


        profile = personality_insights.profile(
            data,
            'application/json',
            content_type='text/plain',
            consumption_preferences=True,
            raw_scores=True
        ).get_result()
        #save user profile
        with open('./data/profiles/'+username+'_profile.json', 'w') as outfile:
            json.dump(profile, outfile)
    return profile

#No Longer using in favor of personality-text-summary node.js package executed in getSummary
def getFacetDescription(profile):
    facets=pd.read_csv("facets.csv")
    list = []
    i = 0
    for p in profile['personality']:
        list.append(pd.DataFrame.from_dict(pd.io.json.json_normalize(p['children']), orient = 'columns'))
        list[i]['big_five'] = p['name']
        i+=1
    df = pd.concat(list,ignore_index=True)
    df['abs_score'] = abs(.50 - df['percentile'])
    df_sorted = df.sort_values('abs_score', ascending=False).head(3)

    result=pd.merge(df_sorted,
                    facets,
                    left_on='trait_id',
                    right_on='facet_id')
    output=''
    for index,row in result.iterrows():
        if (row['percentile'] - .50) >= 0:
            output = output + ' You are '+ row['high_term'] + ': ' + str.lower(row['high_desc'])
        else:
            output = output + ' You are ' + row['low_term'] + ': ' + str.lower(row['low_desc'])
    return output[1:]

def getSummary(profile):
    with open('./data/temp.json','w+') as outfile:
        json.dump(profile, outfile)

    result = execute_js('summary.js')
    if result:
        return open('./data/temp.txt','r').read()
    else:
        return 'Could not generate profile summary.'

def getUserComments(user):
    after= 'start'
    sample = ''
    while after is not None:
        if after == 'start':
            r = requests.get(r'https://www.reddit.com/user/'+user+'/comments/.json',headers = {'User-agent': reddit_agent})
        else:
            r = requests.get(r'https://www.reddit.com/user/'+user+'/comments/.json?after='+after,headers = {'User-agent': reddit_agent})
        data = r.json()
        #find errors

        try:
            before = data['data']['before']
            after= data['data']['after']
            for child in data['data']['children']:
                id = child['data']['id']
                author = child['data']['author']
                body = child['data']['body']
                score = child['data']['score']
                edited = child['data']['edited']
                #print(child['data']['id']," ", child['data']['author'],child['data']['body'])
                lines = body.split('\n')
                for line in lines:
                    if not line or line.startswith('&gt;'):
                        continue
                    sample+= line + '\n'

        except:
            error = {"error": data['error'],
                "message":data['message']
                }
            return error
    return sample

def getBigFive(profile):
    big_five = {}
    for p in profile['personality']:
        big_five.update({p['name']:p['percentile']})
    return dict(sorted(big_five.items(), key=lambda kv: kv[1], reverse=True))

def bigFiveDescription(big_five):
    output = '"Big Five" Personality Traits (% = percentile)'
    for trait in big_five:
        output += '\n\n* ' + trait + ': ' + str(round(big_five[trait]*100)) + '%'
    return output

def getStrength(word_count):
    #Weak (100~1500 words), Decent (1500~3500 words), Strong (3500~6000 words) and Very Strong (6000+ words)
    if word_count <=1500:
        return 'Weak'
    elif word_count <= 3500:
        return 'Decent'
    elif word_count <= 6000:
        return 'Strong'
    else:
        return 'Very Strong'
class reddit_profile:
    def __init__(self,username):
        self.username = username
        comments = getUserComments(self.username)
        self.big_five = {}
        self.description =''
        try:
            if len(comments.split()) > 100:
                self.description += 'Profile for /u/'+ self.username + ':\n\n'
                ibm_profile = getPersonalityInsight(comments,self.username)
                self.Strength = getStrength(ibm_profile['word_count'])
                self.big_five = getBigFive(ibm_profile)
                self.description += 'Word Count: ' + str(ibm_profile['word_count']) + '. Profile Strength: ' + self.Strength + '.\n\n'
                self.description += getSummary(ibm_profile) +'\n\n'+ bigFiveDescription(self.big_five)
            else:
                self.description += '/u/'+self.username + ' does not have enough comments to analyze.'
        except:
            self.description += 'Error getting comments for'+ '/u/'+ self.username +str(comments['error']) +': '+comments['message']
