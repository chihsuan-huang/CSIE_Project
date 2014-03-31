import sys
import cv2
import cv2.cv as cv
import csv
import json
import time
import threading
import numpy as np
from lib.Frame import *
from lib.Keyword import *
from lib.Face import *
from lib.Point import *
from lib.MovieData import *
from lib.FaceCV import *
from lib.faceMatch import *


FLANN_INDEX_KDTREE = 1  # bug: flann enums are missing
FLANN_INDEX_LSH    = 6

OUTPUT_PATH = 'output/'

# mutithread for increase speed
class Pthread (threading.Thread):
    
    threadLock = threading.Lock()
    
    def __init__(self, threadID, name, keyword,startPoint, finishPoint, minCount, mergeCount):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.startPoint = startPoint
        self.finishPoint = finishPoint
        self.minCount = minCount
        self.mergeCount = mergeCount
        self.keyword = keyword

    def run(self):
        global faceLists
        print self.name + ' start'
        
        #merge faceLists
        mergeByFaceMatch(self.keyword, self.startPoint, self.finishPoint, self.minCount, self.mergeCount) 


def mergeByPosition(face1, face2):

    if( abs(face1.getFrame() - face2.getFrame()) > (24*30) ) or face1.character == face2.character:
        return False
    else:
        Pos1 = face1.getPoint()   
        Pos2 = face2.getPoint()
        #print Pos1, Pos2
        if abs(Pos1.x1 - Pos2.x1) < 20 and abs(Pos1.x2 - Pos2.x2) < 20 and abs(Pos1.y1 - Pos2.y1) < 20 and abs(Pos1.y2 - Pos2.y2) < 20:
            face2.character = face1.character
            return True
    return False


def outputCharacter(faceList):

    #Output character in bipartiteGraph as file
    with open ( OUTPUT_PATH+ 'character.txt', 'w') as outputResult:
        for face in faceList:
            outputResult.write( str(face.character) + "\n")

def readCharacter(faceList):

    characters = []
    with open(OUTPUT_PATH + 'character.txt', 'r') as readFile:
        lines = readFile.readlines()
        for line in lines:
            characters.append(line[:len(line)-1])

    i = 0
    for face in faceList:
        face.character = int(characters[i])
        i+=1

def mergeByFaceMatch(keyword, startPoint, endPoint, minCount, mergeCount):
  
    key = []
    for character in faceLists[keyword]:
        key.append(character)
    print len(key), len(faceLists[keyword])
    endPoint = len(faceLists[keyword]) 

    matchCount = 0
    try:
        for i in range(startPoint, endPoint):
            for j in range(startPoint, endPoint):
                if i == j:
                    continue
                for face1 in faceLists[keyword][key[i]]:
                    for face2 in faceLists[keyword][key[j]]:
                        if faceCV.faceMatch(minCount, face1, face2) or faceCV.faceMatch(minCount, face2, face1):
                            matchCount += 1  
                            if matchCount == mergeCount:
                                faceLists[keyword][key[i]] += faceLists[keyword][key[j]]
                                faceLists[keyword][key[j]] = []
                                break
                    if matchCount == mergeCount:
                        matchCount = 0
                        break
    except:
        tp, val, tb = sys.exc_info()
        print  sys.stderr, str(tp), str(val)

    '''
    matchCount = 0
    for i in range(startPoint, endPoint):
        for j in range(i+1, endPoint):
            for face1 in faceLists[ ]:
                for face2 in faceLists[ key[j] ]:
                    if faceCV.faceMatch(minCount, face1, face2):
                        matchCount += 1   
                        if matchCount == mergeCount:
                            weightDic[ key2[i] ] += weightDic[ key2[j] ] 
                            weightDic[ key2[j] ] = []
                            faceLists[ key[i] ] += faceLists[ key[j] ]
                            faceLists[ key[j] ] = []
                            break
                if matchCount == mergeCount:
                    matchCount = 0
                    break
    '''

def outputMergeResult(faceLists, fileName):

    with open (OUTPUT_PATH + str(fileName), 'w') as outputResult:
        for keyword in faceLists:
            for character in faceLists[keyword]:
                if  len(faceLists[keyword][character]) >= 1 :
                    outputResult.write( str(faceLists[keyword][character][0].character) + "\n")
                    for face in faceLists[keyword][character]: 
                        outputResult.write( str(face.getID()) + "\n" )
                    outputResult.write( "\n" )

def readMergeResult(mergeList, store, fileName):
    
    with open(OUTPUT_PATH +fileName, 'r') as readFile:
        lines = readFile.readlines()

        i = 0
        while i < len(lines)-1:
            line = lines[i]
            character = line[:len(line)-1]        
            while lines[i].strip():
                line = lines[i]
                mergeList[ int(line[:len(line)-1]) ] = store[int(line[: len(line)-1])]
                mergeList[ int(line[:len(line)-1]) ].character = character  
                i += 1
            i += 1
                 



if __name__ == '__main__':

    global faceLists, detector, matcher 
    global weightDic
    weightDic = {}
    mergeList = {}
    global faceCV 

    movieData  = MovieData( OUTPUT_PATH + 'preprocessedData.txt')
    #get data from preprocessing.py ouputfile
    faceList, keywords = movieData.getFaceAndKeyword(0, OUTPUT_PATH)
    print 'Face Number=', len(faceList)   
    
    faceCV = FaceCV(len(faceList))
    detector, matcher = faceCV.init_feature()


    store = {}
    for face in faceList:
        store[face.getID()] = face 
        
    #step1 find face in near position
    if len(sys.argv) > 3:
        print 'Step1 merge faceList by position'
        for i in range(0, len(faceList) ):
            for j in range(i, len(faceList) ):
                mergeByPosition(faceList[i], faceList[j])
        outputCharacter(faceList)
    else:    
        readCharacter(faceList)

    if len(sys.argv) > 1:
        
        print 'Step2 merge faceList by position'
        #step2 merge faceList -> faceLists by above result
        faceLists = {}
        #key = []
        #key2 = []


        '''
        for face in faceList:
            if face.character not in faceLists:
                faceLists[face.character] = []
                key.append(face.character)
            if face.character not in weightDic:
                weightDic[face.character] = []
                weightDic[face.character].append(face)
                key2.append(face.character)
            else:
                flag = 0
                for character in weightDic[face.character]:
                    if face.keywordID == character.keywordID:
                        flag = 1  # already in list
                if flag == 0:
                    weightDic[face.character].append(face)
                    key2.append(face.character)
            faceLists[face.character].append(face)
        ''' 
      
        for face in faceList:
            if face.keyword not in faceLists:
                faceLists[face.keyword] = {}
            if face.character not in faceLists[face.keyword]:
                faceLists[face.keyword][face.character] = []
                faceLists[face.keyword][face.character].append(face)
            else:
                faceLists[face.keyword][face.character].append(face)
    
    if len(sys.argv) > 2: 

        print 'Step3 merge faceList by match'
    
        
        #initailize mutithread
        minCount = 4
        mergeCount = 1
        threadID = 0

        
        threads = []
        for keyword in faceLists:
            thread = Pthread(threadID, 'Thread-'+ str(threadID), keyword, 0, len(faceLists[keyword].keys()), minCount, mergeCount)
            threadID += 1
            thread.start()
            threads.append(thread)
        

        #wait all threads complete 
        for thread in threads:
            thread.join()
         
       

        outputMergeResult(faceLists, 'faceLists.txt')

    readMergeResult(mergeList, store, 'faceLists.txt')
    print len(mergeList)

    #step4 start anlaytic
    print 'step4 start anlaytic'


    #build bipartitleGraph
    bipartitleGraph = {}
    for key in mergeList:
        face = mergeList[key]
        if face.keyword not in bipartitleGraph:
            bipartitleGraph[face.keyword] = {}
        if face.character not in bipartitleGraph[face.keyword]:
            bipartitleGraph[face.keyword][face.character] = []
            bipartitleGraph[face.keyword][face.character].append(face)
        else:
            bipartitleGraph[face.keyword][face.character].append(face)

    characterList = []
    print 'step5 find character'
    for word in bipartitleGraph: 
        print word,
        sortList =  sorted(bipartitleGraph[word], key = lambda k: len(bipartitleGraph[word][k]), reverse = True) 
        character1 = bipartitleGraph[word][sortList[0]]

        print len(bipartitleGraph[word]), len(bipartitleGraph[word][sortList[0]])
        print len(sortList)

        name = 0
        for character in sortList:
            cv2.imwrite(OUTPUT_PATH + '/sort/' + word + str(name) + '.jpg'  ,bipartitleGraph[word][character][0].getImg())
            name +=1
        i = 0
        if len(sortList) > 1:
            while i < len(character1):
                kp2, desc2 = detector.detectAndCompute(character1[i].getImg(), None)
                if len(kp2) > 130:
                    i+=1
                    break    
                i+=1
            
            i-=1
            img1 = character1[i].getImg()
            characterList.append(character1[i])
            for j in range(1, len(sortList)):
                character2 = bipartitleGraph[word][sortList[j]][0]
                #print character2.keyword
                if not faceCV.faceMatch(4, character1[i], character2) and faceCV.faceMatch(4, character2, character1[i]):
                    print 'good match'
                    img2 = character2.getImg()
                    break
            characterList.append(character2)



    #merge face in differernt keyword
    '''
    for i in range(0, len(characterList)):
        for j in range(i+1, len(characterList)):
            if characterList[i].character != characterList[j].character and characterList[i].keyword != characterList[j].keyword:
                match = faceCV.getMatchRate(characterList[i], characterList[j])
                if  match  > characterList[i].matchID:
                    characterList[i].matchID = characterList[j].character


    for i in range(0, len(characterList)):
        for j in range(i+1, len(characterList)):
            if characterList[i].matchID == characterList[j].character and \
                    characterList[j].matchID == characterList[i].character \
                    and characterList[i].keyword != characterList[j].keyword:
                print 'same1 character', characterList[i].character, characterList[j].character
                characterList[j].character =  characterList[i].character
    ''' 

    # way2
    mergeList = {}
    key = []
    word = {}
    for character in characterList:
        if character.character not in mergeList:
            mergeList[character.character] = []
            mergeList[character.character].append(character)
            key.append(character.character)
            word[character.character] = []
            word[character.character].append(character.keyword)
        else:
            mergeList[character.character].append(character)
            word[character.character].append(character.keyword)

    for i in range(0, len(mergeList)):
        for j in range(i+1, len(mergeList)):
            for face1 in  mergeList[key[i]]:
                for face2 in mergeList[key[j]]:
                    if face1.keyword in word[key[j]] or face1.character == face2.character:        
                        #print face1.keyword, face2.keyword, face1.character, face2.character
                        continue
                    if faceCV.faceMatch(16,face1, face2) or faceCV.faceMatch(16, face2, face1):
                        print 'same2 character'            
                        mergeList[key[i]] += mergeList[key[j]]
                        mergeList[key[j]] = []
                        #cv2.imwrite(OUTPUT_PATH  + str(face1.keyword) + '-' + str(face1.character) + '.jpg', face1.getImg())
                        #cv2.imwrite(OUTPUT_PATH  + str(face2.keyword) + '-' + str(face2.character) + '.jpg', face2.getImg())
    

    characterList = []
    for character in mergeList:
        for face in  mergeList[character]:
            face.character = character
            characterList.append(face)
    
    characterList.sort(key = lambda x : x.keyword, reverse = True)

    '''
    hasMatch = []
    characterNumber = len(characterList)
    for i in range(0, len(characterList)):
        for j in range(i+1, len(characterList)):
            if  characterList[i].keyword != characterList[j].keyword and characterList[i].character!= characterList[j].character and \
                    faceCV.getMatchRate(characterList[i], characterList[j]) > 45: #faceCV.faceMatch(24, characterList[i], characterList[j]):
                print 'same character', characterList[i].character, characterList[j].character
                #cv2.imwrite(OUTPUT_PATH  + str(characterList[i].keyword) + '-' + str(characterList[i].character) + '.jpg', characterList[i].getImg())
                #cv2.imwrite(OUTPUT_PATH  + str(characterList[j].keyword) + '-' + str(characterList[j].character) + '.jpg', characterList[j].getImg())
                if characterList[j].character in hasMatch:
                    characterList[i].character = characterList[j].character
                else:
                    characterList[j].character = characterList[i].character
                    hasMatch.append(characterList[i].character)
                characterNumber -= 1
    '''
    

    print 
    
    

    #bulid nodes
    characterDic = {}
    nodes = []
    i = 0
    for character in characterList:
        if character.character not in characterDic:
            nodes.append({'group':i, 'name': character.keyword + '-' + str(character.character) })
            characterDic[character.character] = i
            i+=1

    #bulid edges
    edges = []
    for i in range(0, len(characterList)/2):
        edges.append({'source': characterDic[characterList[i*2].character], 'target':characterDic[characterList[i*2+1].character], 'value': 5, 'label': characterList[i*2].keyword}) 
    
    print json.dumps({ 'nodes':nodes, 'links': edges})
 
    with open(OUTPUT_PATH + '/result/data.json', 'w') as outfile:
        json.dump({'nodes':nodes, 'links': edges}, outfile, indent = 4)



    for character in characterList:
        point = character.getPoint()
        face = character.getImg()
        #face = img[point.y1:point.y2, point.x1:point.x2]
        cv2.imwrite(OUTPUT_PATH + '/result/' + str(character.keyword) + '-' + str(character.character) + '.jpg', face)
    
       # cv2.imwrite(OUTPUT_PATH + '/result/' + str(character.keyword) + '-' + str(character.character) + '2.jpg', img)
       
    '''
    result = {}
    for character1 in characterList:
        for character2 in characterList:
            if character1.character not in result:
                result[character1.character] = {}
            if character1.getID() == character2.getID():
                continue
            elif character1.keyword == character2.keyword:    
                result[character1.character][character2.character] = character1.keyword
                print character1.keyword
    print result
    '''   