from django.shortcuts import render
from django.http import JsonResponse
import Shared_Utils_Lib.sharedLibAbhishek as sharedLib
import tweepy
import re
import pandas as pd
import os
from nltk.corpus import stopwords
import nltk 
from textblob import TextBlob
from withGMTime import withGMT
import plotly.offline as py
import plotly
import plotly.graph_objects as go
import sys
from flow.views import myuser_login_required

consumerKey='X4NhJbwDZvxVmRSArQeGKsG1g'
consumerSecret='wUiobJtAuo7616ZfgYaStTwLx6OhQ61Ua7Zpn3uEWYoRa22YUC'
keyy='1210898299907035136-xUASVLwC0KTbdPE4VTbjSKmsFSMC5V'
secrett='zov6IEnzbowvgU9dGO8d9H3Bt6WJLO34ZdPIlINgS54Ts'
auth = tweepy.OAuthHandler(consumerKey,consumerSecret)
auth.set_access_token(keyy,secrett)
api = tweepy.API(auth)

# def twitterAuth():
#     consumerKey='X4NhJbwDZvxVmRSArQeGKsG1g'
#     consumerSecret='wUiobJtAuo7616ZfgYaStTwLx6OhQ61Ua7Zpn3uEWYoRa22YUC'
#     keyy='1210898299907035136-xUASVLwC0KTbdPE4VTbjSKmsFSMC5V'
#     secrett='zov6IEnzbowvgU9dGO8d9H3Bt6WJLO34ZdPIlINgS54Ts'
#     auth = tweepy.OAuthHandler(consumerKey,consumerSecret)
#     auth.set_access_token(keyy,secrett)
#     api = tweepy.API(auth)
#     #api.update_status(status='Test')
#     return api

def sentiment_textblob(feedback): 
    senti = TextBlob(feedback) 
    polarity = senti.sentiment.polarity 
    if -1 <= polarity < -0.5: 
        label = 'Too Negative' 
    elif -0.5 <= polarity < -0.1: 
        label = 'Negative' 
    elif -0.1 <= polarity < 0.2: 
        label = 'Neutral'
    elif 0.2 <= polarity < 0.6: 
        label = 'Positive' 
    elif 0.6 <= polarity <= 1: 
        label = 'Too Positive' 
    return polarity, label
@myuser_login_required
def twitterInit(request):
    username = sharedLib.getUserName(request) 
#         print(sys.exc_info()[1])
    data={'user':username,'gmtTime':withGMT(username)}
    return render(request, 'flow/usecase_templates/twitter.html', data)
@myuser_login_required
def displayHashTag(request):
    username = sharedLib.getUserName(request)
    #api=twitterAuth()
    worldwide_trends=api.trends_place(1)
    trandingHashtag=[tweets['name'] for tweets in worldwide_trends[0]['trends']]  
    filteredHashTag=[]
    for hashTag in trandingHashtag: 
        if(hashTag.startswith('#') and bool(re.match('[a-zA-Z0-9_]+$',hashTag.split('#')[-1]))):
            filteredHashTag.append(hashTag)
        elif(bool(re.match('[a-zA-Z0-9_]+$',hashTag))):
            filteredHashTag.append(hashTag)
    data={'user':username,'filteredHashTag':filteredHashTag}
    return JsonResponse(data)

# def getHashTag(request):
#     username = sharedLib.getUserName(request)
#     global hashtag
#     hashtag = request.GET.get('hashtag', None)
#     data={'user':username}
#     return JsonResponse(data)

#def getHashTagNameFromUser(request):
    
@myuser_login_required
def tweetSentiment(request):
    print("inside tweetSentiment*********")
    username = sharedLib.getUserName(request)
    hashtag=None
    selectedhashtag = request.GET.get('hashtag')
    userEntered=request.GET.get('enterHash')
    print("selectedhashtag= ",selectedhashtag)   
    print("userEntered = ",userEntered)
    if(userEntered!=''):
        hashtag=userEntered
    else:
        hashtag=selectedhashtag
    
    #api=twitterAuth()
    df = pd.DataFrame()
    text = []
    user=[]
    tweetTime=[]
#     if(hashtag.startswith('#')):
#         hashtag='https://api.twitter.com/1.1/search/tweets.json?q=%23'+hashtag.split('#')[-1]
#     print("hashtag.startswith('#')= ",hashtag.startswith('#'))
#     print("hashtag ********** =",hashtag)
    
    for tweet in tweepy.Cursor(api.search, q=hashtag,lang='en').items(200): 
        text.append(tweet.text)
        user.append(tweet.user.screen_name)
        tweetTime.append(tweet.created_at)
    if(len(text)!=0):
        try:
            df['text']=text
            df['user']=user
            df['createdAt']=tweetTime
            words = set(nltk.corpus.words.words())
            stopword_set = set(stopwords.words("english"))
            refinedTweets=[]
            for tweet in df['text']:
                refinedWords=[]
                for word in tweet.split(' '):
                    word=re.sub(r'[|!|.|:|+|?|,|-|*|%|/]','',word)
                    if(bool(re.match('[a-zA-Z_]+$',word)) and not word.startswith('RT') and word in words and not word in stopword_set and len(word)!=1):
                        refinedWords.append(word)
                refinedTweets.append(' '.join(refinedWords))   
            df['refinedTweets']=refinedTweets
            global final_df
            final_df = pd.DataFrame()
            final_user=[]
            final_text=[]
            final_time=[]
            text_sentiment=[]
            for i in range(df.shape[0]):
                if(len(df['refinedTweets'][i])!=0):
                    score,sentiment=sentiment_textblob(df['refinedTweets'][i])
                    final_user.append(df['user'][i])
                    final_text.append(df['text'][i])
                    final_time.append(df['createdAt'][i])
                    text_sentiment.append(sentiment)
            final_df['User']=final_user
            final_df['Tweets']=final_text
            final_df['CreatedAt']=final_time
            final_df['Sentiments']=text_sentiment
            global DataFrame
            DataFrame=[]
            DataFrame.append(list(final_df.columns))
            for i in range(final_df.shape[0]):
                 DataFrame.append(list(final_df.iloc[i]))
            data={}
            data['user']=username
            #data['DataFrame']=DataFrame
            data['gmtTime']=withGMT(username)
            data['error']='false'
            #return render(request, 'flow/usecase_templates/tweetTable.html', data)
            return JsonResponse(data)
        except:
            data={}
            data['user']=username
            data['gmtTime']=withGMT(username)
            data['error']='True'
            data['errorMsg']=str(sys.exc_info())
            return JsonResponse(data)
    elif(len(text)==0):
        data={}
        data['user']=username
        data['gmtTime']=withGMT(username)
        data['error']='True'
        data['errorMsg']="The given <b>"+hashtag+"</b> Hashtag or word contains only Non-English Tweets so, can't do analysis."
        #return render(request, 'flow/usecase_templates/twitter.html', data)
        return JsonResponse(data)
@myuser_login_required
def viewResult(request):
    username = sharedLib.getUserName(request)
    data={}
    data['user']=username
    data['DataFrame']=DataFrame
    data['gmtTime']=withGMT(username)
    return render(request, 'flow/usecase_templates/tweetTable.html', data)
    
@myuser_login_required    
def pieChart(request):
    username = sharedLib.getUserName(request)
    graphPath=sharedLib.getFilePath('twitterSentiment', username)+'pie.html'
    print("graphPath= ",graphPath)
    return render(request,graphPath)
@myuser_login_required                          
def getPieChart(request):
    username = sharedLib.getUserName(request)  
    sentiments = final_df['Sentiments'].astype(str).value_counts()
    fig = {"data": [{"labels": sentiments.index ,"values": sentiments.values,"type": "pie"}]} 
    py.plot(fig, filename=sharedLib.getFilePath('twitterSentiment', username)+'pie', auto_open=False) 
    data={}
    data['user']=username
    data['pieImage']='pieChart'
    return render(request,'flow/usecase_templates/twitterPieChart.html', data)     
@myuser_login_required
def tableAppend(request):
    username = sharedLib.getUserName(request)  
    data={}
    data['user']=username
    data['DataFrame']=DataFrame
    data['gmtTime']=withGMT(username)
    return render(request, 'flow/usecase_templates/tweetDisplayTable.html', data)