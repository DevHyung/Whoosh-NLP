# -*- coding:utf-8 -*-
"""
    data/
        ㄴinput.txt              = 비슷한 문장 찾으려는 query file
        ㄴoutput.txt (만들어짐)   = 비슷한 문장 찾은 결과
        ㄴQ.txt (예시)           = 대화 데이터셋 원문
        ㄴQ_MORP.txt(예시)       = 대화 데이터셋 형태소 분석된거
"""
import operator
import os
from CONFIG import *
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from typing import List, TextIO, Dict
import time

def log(tag, text)-> None:
    '''
        Log pring function
    '''
    # Info tag
    if (tag == 'i'):
        print("[INFO] " + text)
    # Error tag
    elif (tag == 'e'):
        print("[ERROR] " + text)
    # Success tag
    elif (tag == 's'):
        print("[SUCCESS] " + text)

def get_data_from_txt(_filename)-> List[str]:
    """
    :param _filename: 파일이름
    :return: data List
    """
    dataList :List[str] = []
    f : TextIO = open(file=_filename, mode='r', encoding='utf8')

    for line in f.readlines():
        dataList.append(line.strip())

    f.close()
    log('s', "{} 파일에서 {} 줄 불러옴".format(_filename, len(dataList)))

    return dataList

def extract_morp_str(_morpStr: str) -> str:
    """
    :param _morpStr: morp long string
    :return: 품사만 남은 string
    """
    tmp: str = ""
    splitList = _morpStr.split(' ')
    for morp in splitList:
        try:
            tmp += morp.split('/')[1] + " "
        except:  # 공백인 경우, 형태소분석결과가 없음
            pass
    return tmp.strip()


def get_morp_from_list(_sentece)-> str:
    """
    :param _sentece: 원본문장 ' 오늘 날씨가 좋네 ' 같은
    :return: 원본문장에 해당하는 형태소 품사만 남은 str
    """
    idx: int = QList.index(_sentece)
    morpStr: str = extract_morp_str(QMList[idx])
    return morpStr

if __name__ == "__main__":
    '''_____ Data Load Area _____'''
    # Load dataset data
    QList: List[str] = get_data_from_txt(DATA_DIR + Q_FILE_NAME)
    QMList: List[str] = get_data_from_txt(DATA_DIR + Q_MORP_FILE_NAME)
    tuneQMList :List[str] = [] # Q와 QM 리스트에서 실제로 whoosh DB에 들어가는 tune된 QM List

    '''_____ Whoosh DB create + insert Area _____'''
    # Set index directory
    if not os.path.exists(indexdir):
        os.makedirs(indexdir)

    # Set schema
    schema = Schema(title=TEXT(stored=True),
                    path=ID(stored=True),
                    content=NGRAMWORDS(minsize=2, maxsize=3, stored=True),
                    idx=ID(stored=True))
    # create schema
    ix = create_in(indexdir, schema)

    # Define the writer for search Inverted
    writer = ix.writer()

    # Preprocess
    for fori in range(len(QMList)):
        tuneQMList.append(extract_morp_str(QMList[fori]))

    # Build DB
    for fori in range( len(QList) ):
        writer.add_document(title=u"{}".format(QList[fori]),
                            path=u"/wt",
                            content=u"{}".format(tuneQMList[fori]),
                            idx=u"{}".format(fori))
    writer.commit()

    '''_____ Search Area _____'''
    f: TextIO = open(DATA_DIR + INPUT_FILE_NALE,'r',encoding='utf8')
    querys: List[str] = f.readlines()

    outF: TextIO = open(DATA_DIR + OUTPUT_FILE_NALE, 'w', encoding='utf8')

    # Search
    with ix.searcher() as searcher:
        qp = QueryParser("content", ix.schema)
        idx = 1 # 단순히 몇번째 검색중인지 index 변수
        start = time.time()# time checking

        for query in querys:
            dataDict: Dict[int, int] = {}
            query: str = query.strip()

            log('i', "{}번째 검색중..".format(idx))
            idx += 1

            queryIdx = QList.index(query)
            morpStr = get_morp_from_list(query)
            splitMorp = morpStr.split(' ')

            # bi-gram weight sum
            for fori in range(len(splitMorp) - 1):
                user_q = qp.parse(u'{}'.format(splitMorp[fori]+" "+splitMorp[fori+1]))
                results = searcher.search(user_q, limit=searchLimit)
                for r in results:
                    try:
                        dataDict[r['idx']] += r.score
                    except:
                        dataDict[r['idx']] = r.score

            # Tri-gram weight sum
            # 여기를 지우면 단순하게 bi-gram 까지만의 weight sum 을 이용
            for fori in range(len(splitMorp) - 2):
                user_q = qp.parse(u'{}'.format(splitMorp[fori]+" "+splitMorp[fori+1]+" "+splitMorp[fori+2]))
                results = searcher.search(user_q, limit=searchLimit)
                for r in results:
                    try:
                        dataDict[r['idx']] += r.score
                    except:
                        dataDict[r['idx']] = r.score

            # 정렬후 랭킹별로 뽑아냄
            sortedTmp = sorted(dataDict.items(), key=operator.itemgetter(1), reverse=True)
            while True:
                top = sortedTmp.pop(0)
                if int(top[0]) == queryIdx: # 자기랑 같은 문장은 제외
                    pass
                else:
                    outF.write(QList[int(top[0])] + '\n')
                    break
        end = time.time() # time checking end
        # print(end-start) # only bi-gram = 42.87초, 개당 0.21초  | include tri-gram 57.36초 개당 0.28초
    f.close()
    outF.close()