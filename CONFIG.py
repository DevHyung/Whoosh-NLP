'''__________ DATA AREA  __________'''
DATA_DIR: str         = "data/" # data file directory name
Q_FILE_NAME: str      = "Q.txt"  # 질문 문장 file name
Q_MORP_FILE_NAME: str = "Q_MORP.txt" # 형태소 분석된 file name
INPUT_FILE_NALE: str = "input.txt"   # Query text file name
OUTPUT_FILE_NALE: str = "output.txt" # Result text file name
'''__________ Whoosh AREA  __________'''
indexdir = './ndx'  # Whoosh data index folder
searchLimit = 10 # whoosh search limit num, Default value 10