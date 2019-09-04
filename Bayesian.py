import numpy as np
import pymongo
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

"""
函数说明:将切分的实验样本词条整理成不重复的词条列表，也就是词汇表

Parameters:
    dataSet - 整理的样本数据集
Returns:
    vocabSet - 返回不重复的词条列表，也就是词汇表
"""


def createVocabList(dataSet):
    vocabSet = set([])  # 创建一个空的不重复列表
    for document in dataSet:
        vocabSet = vocabSet | set(document)  # 取并集
    return list(vocabSet)


"""
函数说明:根据vocabList词汇表，将inputSet向量化，向量的每个元素为1或0

Parameters:
    vocabList - createVocabList返回的列表
    inputSet - 切分的词条列表
Returns:
    returnVec - 文档向量,词集模型
"""


def setOfWords2Vec(vocabList, inputSet):
    returnVec = [0] * len(vocabList)  # 创建一个其中所含元素都为0的向量
    for word in inputSet:  # 遍历每个词条
        if word in vocabList:  # 如果词条存在于词汇表中，则置1
            returnVec[vocabList.index(word)] = 1
        else:
            # print("the word: %s is not in my Vocabulary!" % word)
            msg = "the word: %s is not in my Vocabulary!"
    return returnVec  # 返回文档向量


"""
函数说明:朴素贝叶斯分类器训练函数

Parameters:
    trainMatrix - 训练文档矩阵，即setOfWords2Vec返回的returnVec构成的矩阵
    trainCategory - 训练类别标签向量，即loadDataSet返回的classVec
Returns:
    p0Vect - 侮辱类的条件概率数组
    p1Vect - 非侮辱类的条件概率数组
    pAbusive - 文档属于侮辱类的概率
"""


def trainNB0(trainMatrix, trainCategory):
    numTrainDocs = len(trainMatrix)  # 计算训练的文档数目
    numWords = len(trainMatrix[0])  # 计算每篇文档的词条数

    p2Num = np.ones(numWords);
    p1Num = np.ones(numWords)  # 创建numpy.ones数组,词条出现数初始化为1，拉普拉斯平滑
    p0Num = np.ones(numWords)
    pn1Num = np.ones(numWords);
    pn2Num = np.ones(numWords);

    sum2 = 0.0;
    sum1 = 0.0;
    sum0 = 0.0;
    sumn1 = 0.0;
    sumn2 = 0.0
    for i in range(numTrainDocs):
        if trainCategory[i] == 1:
            p1Num += trainMatrix[i]
            sum1 += 1
        elif trainCategory[i] == 2:
            p2Num += trainMatrix[i]
            sum2 += 1
        elif trainCategory[i] == -1:
            pn1Num += trainMatrix[i]
            sumn1 += 1
        elif trainCategory[i] == -2:
            pn2Num += trainMatrix[i]
            sumn2 += 1
        else:
            p0Num += trainMatrix[i]
            sum0 += 1

    psumNum = p1Num + p2Num + pn1Num + pn2Num + p0Num
    pn1 = sumn1 / float(numTrainDocs)
    pn2 = sumn2 / float(numTrainDocs)
    p1 = sum1 / float(numTrainDocs)
    p2 = sum2 / float(numTrainDocs)
    p0 = sum0 / float(numTrainDocs)

    p2Vect = 100 * (p2Num / psumNum)  # 强正
    p1Vect = 100 * (p1Num / psumNum)  # 微正
    p0Vect = 100 * (p0Num / psumNum)  # 中性
    pn1Vect = 100 * (pn1Num / psumNum)  # 微负
    pn2Vect = 100 * (pn2Num / psumNum)  # 强负

    return p2Vect, p1Vect, p0Vect, pn1Vect, pn2Vect, p2, p1, p0, pn1, pn2  # 返回属于侮辱类的条件概率数组，属于非侮辱类的条件概率数组，文档属于侮辱类的概率


"""
函数说明:朴素贝叶斯分类器分类函数

Parameters:
    vec2Classify - 待分类的词条数组
    p0Vec - 侮辱类的条件概率数组
    p1Vec -非侮辱类的条件概率数组
    pClass1 - 文档属于侮辱类的概率
Returns:
    0 - 属于非侮辱类
    1 - 属于侮辱类
"""


def classifyNB(vec2Classify, pnVec, p0Vec, p1Vec, pClass1, pClass2):
    # 分词后的文本向量和三种类型的词库相乘
    pn = sum(vec2Classify * pnVec) * (pClass1)
    p0 = sum(vec2Classify * p0Vec) * (pClass2)
    p1 = sum(vec2Classify * p1Vec) * (1.0 - pClass1 - pClass2)
    psum = pn + p0 + p1
    pn = pn / psum   # 新闻为消极的概率
    p0 = p0 / psum   # 新闻为中性的概率
    p1 = p1 / psum   # 新闻为积极的概率
    print(pClass1, pClass2, pn, p0, p1)
    if p1 >= p0:
        if p1 >= pn:
            if p1>0.5:
                return 2
            else:
                return 1
        else:
            if pn>0.5:
                return -2
            else:
                return -1
    else:
        if p0 > pn:
            return 0
        else:
            if pn > 0.5:
                return -2
            else:
                return -1


"""
函数说明:文本预处理（分词，去停用词）

Parameters:
    text - 未分词的文本内容
    stopWords - 停用词
Returns:
    text_segment - 分词处理后的文本
"""


def textSegment(text, stopWords):
    word_cut = jieba.cut(text, cut_all=False)
    word_list = list(word_cut)
    text_segment = list()
    for t in word_list:
        if t not in stopWords:
            text_segment.append(t)

    return text_segment


"""
函数说明:提取新闻中的关键词

Parameters:
    content - 文本内容
Returns:
    keywords - 关键词
"""
def get_keywords(content):
    p = list()
    for i in content:
        print(i)
        temp = (" ".join(word for word in i))  # 转化成可以操作的文本形式
        p.append(temp)

    vectorizer = CountVectorizer(max_features=10000)   # 取前10000个关键词，max_features可以改变
    count = vectorizer.fit_transform(p)
    keywords=vectorizer.get_feature_names()  # 输出关键词

    return keywords


"""
函数说明:朴素贝叶斯训练器,训练词库存入数据库

Parameters:
    text_segment - 分词预处理后的文本(字典)
    text_sentiment - 文本情感倾向
Returns:
    无
"""


def bayesianTrain():
    cilent = pymongo.MongoClient('localhost', 27017)
    db = cilent['KDX']
    col = db['TrainNews6']
    sw = db['StopWords']

    '''分词'''
    text = dict()
    text_title = list()
    text_sentiment = dict()
    for each in col.find():
        text[each['title']] = each['content']
        text_title.append(each['title'])
        text_sentiment[each['title']] = each['sentiment']

    stopwords = list()  # 停用词词典
    for each in sw.find():
        stopwords.append(each['word'])

    text_segment = dict()
    for i, j in text.items():
        word_cut = jieba.cut(j, cut_all=False)   # 分词，不适用精确分词模式
        word_list = list(word_cut)
        temp = list()
        for t in word_list:
            if t not in stopwords:
                temp.append(t)
        text_segment[i] = temp

    '''训练贝叶斯分类器'''
    docList = []  # 分词后文档内容
    classList = []  # 分类标准，人工标记的数据
    for i, j in text_segment.items():
        docList.append(j)
    for i, j in text_sentiment.items():
        classList.append(j)

    kyList=[]  # tf-idf筛选过后的文档内容
    keywords = get_keywords(docList)
    for each in docList:
        temp=list()
        for i in each:
            if i in keywords:
                temp.append(i)
        kyList.append(temp)
    print(len(kyList), len(docList))

    for i in range(0, len(docList)):
        print(i, len(docList[i]), len(kyList[i]))

    vocabList = createVocabList(kyList)  # 创建词汇表，不重复
    trainingSet = list(range(len(text_sentiment)))

    trainMat = [];
    trainClasses = []  # 创建训练集矩阵和训练集类别标签系向量
    for docIndex in trainingSet:  # 遍历训练集
        trainMat.append(setOfWords2Vec(vocabList, kyList[docIndex]))  # 将生成的词集模型添加到训练矩阵中
        trainClasses.append(classList[docIndex])  # 将类别添加到训练集类别标签系向量中
    p2V, p1V, p0V, pn1V, pn2V, p2, p1, p0, pn1, pn2 = trainNB0(np.array(trainMat), np.array(trainClasses))  # 训练朴素贝叶斯模型

    col_tw = db['TrainWords6']
    for each in zip(vocabList, p2V, p1V, p0V, pn1V, pn2V):
        col_tw.insert_one({'word': each[0],
                           'p2V': each[1],
                           'p1V': each[2],
                           'p0V': each[3],
                           'p-1V': each[4],
                           'p-2V': each[5]})
    col_tw.insert_one({'pn2': pn2})
    col_tw.insert_one({'pn1': pn1})
    col_tw.insert_one({'p1': p1})
    col_tw.insert_one({'p2': p2})
    col_tw.insert_one({'p0': p0})


"""
函数说明:朴素贝叶斯分类器

Parameters:
    text_segment - 分词预处理后的文本(字典)
    vocabList - 训练好的词集模型
    p0V - 正面词词集
    p1V - 负面词词集
    pSpam - 先验概率
Returns:
    text_sentiment - 文本情感类型
"""


def category(text_segment, vocabList, pnV, p0V, p1V, pSpam, pNone):
    wordVector = setOfWords2Vec(vocabList, text_segment)  # 测试集的词集模型
    text_sentiment = classifyNB(np.array(wordVector), pnV, p0V, p1V, pSpam, pNone)  # 分类
    return text_sentiment


if __name__ == '__main__':
    # bayesianTrain()  # 训练分类器(备注：除非要重新训练训练集，否则不用该语句）

    cilent = pymongo.MongoClient('localhost', 27017)  # 读取训练好的词集
    db = cilent['KDX']
    col = db['TrainWords6']

    # 读取词库
    vocabList = list();
    p2V = list();
    p1V = list();
    p0V = list();
    pn1V = list();
    pn2V = list();
    p2 = 0;
    p1 = 0;
    p0 = 0;
    pn1 = 0;
    pn2 = 0;
    for each in col.find():
        if 'p2' in each.keys():
            p2 = each['p2']
        elif 'p1' in each.keys():
            p1 = each['p1']
        elif 'p0' in each.keys():
            p0 = each['p0']
        elif 'pn1' in each.keys():
            pn1 = each['pn1']
        elif 'pn2' in each.keys():
            pn2 = each['pn2']
        else:
            vocabList.append(each['word'])
            p2V.append(each['p2V'])
            p1V.append(each['p1V'])
            p0V.append(each['p0V'])
            pn1V.append(each['p-1V'])
            pn2V.append(each['p-2V'])

    strongp = 2;
    strongn = 2  # 分别为强正权重和强负权重
    p1wV = list();
    pn1wV = list();
    p0wV = list()
    for i in range(0, len(p1V)):
        p1wV.append(strongp * p2V[i] + p1V[i])
        pn1wV.append(strongn * pn2V[i] + pn1V[i])
    p0wV = p0V
    pSpam = pn1 + pn2
    pNone = p0

    col2 = db['TestNews']
    data = dict()
    for each in col2.find():
        data[each['url']] = each['content']

    sw = db['StopWords']  # 读取停用词
    stopWords = list()
    for each in sw.find():
        stopWords.append(each['word'])

    count = 1
    for i, j in data.items():
        text_segment = textSegment(j, stopWords)
        sentiment = category(text_segment, vocabList, pn1wV, p0wV, p1wV, pSpam, pNone)
        if sentiment == -2:
            print('第' + str(count) + '文本的情感类型为：强负')
        elif sentiment == -1:
            print('第' + str(count) + '文本的情感类型为：微负')
        elif sentiment == 0:
            print('第' + str(count) + '文本的情感类型为：中性')
        elif sentiment == 1:
            print('第' + str(count) + '文本的情感类型为：微正')
        elif sentiment == 2:
            print('第' + str(count) + '文本的情感类型为：强正')
        else:
            print('无法识别文本情感类型')
        col2.update_one({'url': i}, {'$set': {'sentiment1': sentiment}})
        count = count + 1