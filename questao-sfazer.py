import pandas as pd
import numpy as np
from datetime import datetime

#adicionei para ver o plot
import matplotlib.pyplot as plt

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


strToFloat = lambda x: float(x.replace(".","").replace(",","."))
strToInt = lambda x: int(float(x.replace(".","").replace(",",".")))
COTA[["PRECO","PATR"]]=COTA[["PRECO","PATR"]].applymap(strToFloat)
#COTA["QTD"]=COTA["QTD"].apply(strToInt)
#coluna de OPERACOES: PRECO
OPERACOES["PRECO"]=OPERACOES["PRECO"].apply(strToFloat)
OPERACOES["QTD"]=OPERACOES["QTD"].apply(strToInt)

#coluna de MOV_CC: MOV

MOV_CC["MOV"]=MOV_CC["MOV"].apply(strToFloat)

#coluna de PRECOS: PRECO

PRECOS["PRECO"] = PRECOS["PRECO"].apply(strToFloat)
#troca sinal da quantidade em ordens de compra (positivo) e venda (negativo) para padronizar como processaremos as ordens

for row,i in OPERACOES.iterrows():
    if i.MOV=='C':
        OPERACOES.loc[row,'QTD']=i.QTD
    else:
        OPERACOES.loc[row,'QTD']=-i.QTD

#popula histórico POSICAO
#aqui processamos todas as ordens e montamos um histórico de posição dizendo se a carteira estava comprada ou não em um ativo dia a dia

POS_AT=pd.DataFrame({'DATA':pd.Series([], dtype='datetime64[ns]'),'ATIVO':pd.Series([], dtype='str'),'POS':pd.Series([], dtype='float')})

for row,i in OPERACOES.iterrows():
    POS_AT_SW=pd.DataFrame({'DATA':pd.Series([], dtype='datetime64[ns]'),'ATIVO':pd.Series([], dtype='str'),'POS':pd.Series([], dtype='float')})
    POS_AT_SW.DATA=PRECOS.loc[(PRECOS.DATA>=i.DATA) & (PRECOS.ATIVO==i.ATIVO)].DATA.unique()
    POS_AT_SW.ATIVO=i.ATIVO
    POS_AT_SW.POS=i.QTD
    POS_AT=POS_AT.append(POS_AT_SW).reset_index(drop=True)

POS_AT=POS_AT.groupby(['ATIVO','DATA'],as_index=False).sum()



#popula histórico da Conta Corrente que deve ter o impacto:
# 1 - das movimentações de aplicações e resgates
# 2 - das operações de compra e venda de ativos

POS_CC=pd.DataFrame({'DATA':pd.Series([], dtype='datetime64[ns]'),'SALDO':pd.Series([], dtype='float')})
POS_CC.DATA=MOV_CC.DATA[0:1]
POS_CC.SALDO=MOV_CC.MOV[0:1]

#POPULA MOVIMENTAÇÕES NA CC
for row,i in MOV_CC.iterrows():
    POS_CC_SW=pd.DataFrame({'DATA':pd.Series([], dtype='datetime64[ns]'),'SALDO':pd.Series([], dtype='float')})
    POS_CC_SW.DATA=PRECOS.loc[PRECOS.DATA>=i.DATA].DATA.unique()
    POS_CC_SW.SALDO=i.MOV
    POS_CC=POS_CC.append(POS_CC_SW).reset_index(drop=True)
    
#popula histórico OPERAÇÕES NA CC
for row,i in OPERACOES.iterrows():
    POS_CC_SW=pd.DataFrame({'DATA':pd.Series([], dtype='datetime64[ns]'),'SALDO':pd.Series([], dtype='float')})
    POS_CC_SW.DATA=PRECOS.loc[(PRECOS.DATA>=i.DATA) & (PRECOS.ATIVO==i.ATIVO)].DATA.unique()
    POS_CC_SW.SALDO=-i.QTD*i.PRECO
    POS_CC=POS_CC.append(POS_CC_SW).reset_index(drop=True)


POS_CC.groupby(['DATA']).sum()

#Preparação para CÁLCULO DO RESULTADO
#aqui montamos uma nova tabela para processarmos o resultado diário (PNL=profit and loss)

PNL=POS_AT.merge(OPERACOES,how='left',left_on=['DATA','ATIVO'], right_on=['DATA','ATIVO'])
PNL=PNL.rename(columns={'PRECO': "PRECO_MOV"})
PNL=PNL.merge(PRECOS,how='left',left_on=['DATA','ATIVO'], right_on=['DATA','ATIVO'])
PNL['PRECOANT']=pd.Series([],dtype='float')
for i in PNL.ATIVO.unique():
    PNL.loc[PNL.ATIVO==i,'PRECOANT']=PNL.loc[PNL.ATIVO==i].PRECO.shift(periods=1)
PNL['POS$']=PNL['POS']*PNL['PRECO']


#cálculo do patrimônio diário
PATR=pd.concat([PNL[['DATA','POS$']].groupby(['DATA'],as_index=False).sum().rename(columns={'POS$': 'PATR'}),
           POS_CC.groupby(['DATA']).sum().rename(columns={'SALDO': 'PATR'})],
           ignore_index=True,sort=True).groupby(['DATA'],as_index=False).sum()


#cálculo da cota diária

COTA=COTA.append(PATR,ignore_index=True,sort=False).reset_index(drop=True)
COTA.QTD=COTA.iloc[0].QTD
COTA.PRECO=COTA.PATR/COTA.QTD

#POPULA COTAS com Movimentações de CC 
for row,i in MOV_CC.iterrows():
    if row>0:
        COTA.loc[COTA.DATA>=i.DATA,'QTD']=(COTA.loc[COTA.DATA==i.DATA,'QTD'].values[0]+i.MOV/COTA.loc[COTA.DATA.shift(periods=-1)==i.DATA,'PRECO'].values[0])
        COTA.PRECO=COTA.PATR/COTA.QTD
        

p=COTA[['DATA','PRECO']].plot(x ='DATA', y='PRECO', kind = 'line')


#CÁLCULO DO RESULTADO

PNL=PNL.fillna(0)#preenche vazios com zero
PNL=PNL.merge(PATR,how='left',left_on=['DATA'], right_on=['DATA'])#insere coluna com patrimônio diário

PNL.head()

#nesta variável PNL temos para todas as datas, as posições de fechamento dos ativos (POS), 
#as movimentações (QTD), o preço q a movimentação ocorreu (PRECO_MOV)
#preço de fechamento (PRECO) e o  preco do dia anterior (PRECOANT)

