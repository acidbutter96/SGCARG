import numpy as np
import pandas as pd
from datetime import datetime


#Carrega informações

#cota
COTA=pd.read_csv('COTA.csv',delimiter=';')
COTA['DATA']= pd.to_datetime(COTA['DATA'])

#histórico de operações de compra e venda
OPERACOES=pd.read_csv('OPERACOES.csv',delimiter=';')
OPERACOES['DATA']= pd.to_datetime(OPERACOES['DATA'], format="%d/%m/%Y")

#movimentações de conta corrente depósitos e saques
MOV_CC=pd.read_csv('CONTAC.csv',delimiter=';')
MOV_CC['DATA']= pd.to_datetime(MOV_CC['DATA'], format="%d/%m/%Y")

#preços dos ativos
PRECOS=pd.read_csv('PRECOS.csv',delimiter=';')
PRECOS['DATA']= pd.to_datetime(PRECOS['DATA'], format="%d/%m/%Y")


#substituir , por . e . por nada em seguida converter a variável da coluna de string para float

#identificar os elementos do dataframe

COTA.info()
OPERACOES.info()
MOV_CC.info()
PRECOS.info()


#definir lambda para ser aplicado em cada elemento que deve se tornar um float
strToFloat = lambda x: float(x.replace(".","").replace(",","."))

#colunas de COTA: PRECO E PATR
COTA[["PRECO","PATR"]]=COTA[["PRECO","PATR"]].applymap(strToFloat)

#coluna de OPERACOES: PRECO
OPERACOES[["QTD","PRECO"]]=OPERACOES[["QTD","PRECO"]].applymap(strToFloat)

#coluna de MOV_CC: MOV

MOV_CC["MOV"]=MOV_CC["MOV"].apply(strToFloat)

#coluna de PRECOS: PRECO

PRECOS["PRECO"] = PRECOS["PRECO"].apply(strToFloat)

