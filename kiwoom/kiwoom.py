import os
import sys
import datetime
import schedule
import time

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *
from config.kiwoomType import *


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()


        print("Kiwoom class")

        self.reatlType=RealType()
        self.today=datetime.date.today()

        ######### evenloop 모음
        self.login_event_loop=None
        self.detail_account_info_event_loop=QEventLoop()
        self.calculator_event_loop=QEventLoop()
        self.loop=QEventLoop()

        ############################

        ####### 스크린번호 모음
        self.screen_my_info="2000"
        self.screen_calculation_stock="4000"
        self.screen_real_stock="5000" #종목별로 할당할 스크린 번호
        self.screen_meme_stock="6000" #종목별 할당할 주문용 스크린 번호
        self.screen_start_stop_real ="1000"

        ######### 변수모음
        self.account_num=None
        ##################

        

        ########계좌 관련 변수
        self.use_money=0
        self.use_money_percent=0.5
        ###############


        ####### 변수 모음
        self.account_stock_dict={} #내 계좌에 가지고 있는 종목
        self.not_account_stock_dict={} #미체결 요청에 대한 정보를 받는 dic
        self.condition_search_list=[] #조건검색에 등록된 정보를 저장하는 list
        self.portfolio_stock_dict={}
        self.jango_dict={}
        self.jeonsang_meme=[] #실시간 매수 매도
        ##############

        ########종목 분석 용
        self.calcul_data=[]




        self.get_ocx_instance()  #ocx 방식을 파이썬에 사용할 수 있게 변환
        self.event_slots()  #키움과 연결하기 위한 signal / slot 모음
        self.real_event_slots() #실시간 이벤트 시그널
        self.condition_slots()

        self.signal_login_commConnect() #로그인 시도
        self.get_account_info() #계좌번호 가져오기
        self.detail_account_info() # 예수금 가져오기
        self.detail_account_mystock()  #계좌평가잔고내역 요청
        self.condition_search()
        self.not_concluded_account() #미체결 요청


        self.read_code() # 저장된 종목들 불러온다.
        self.screen_number_setting()  #스크린 번호를 할당

        self.dynamicCall("SetRealReg(QString, QString, QString, QString)",self.screen_start_stop_real, '',self.reatlType.REALTYPE['장시작시간']['장운영구분'],"0" )

        for code in self.portfolio_stock_dict.keys():
            screen_num=self.portfolio_stock_dict[code]["스크린번호"]
            fids=self.reatlType.REALTYPE['주식체결']['체결시간']
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)",screen_num, code, fids,"1")
            print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s " %(code,screen_num,fids))



        
        self.calculator_fnc()


#########################################

    



    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def condition_slots(self):
        self.OnReceiveConditionVer.connect(self.receive_condition)      #조건검색식 리스트 받아올떄 발생하는 이벤트
        #self.OnReceiveRealCondition.connect(self.receive_real_condition)    #실시간으로 조건검색에 검색될때 발생하는 이벤트
        self.OnReceiveTrCondition.connect(self.receive_tr_condition)    #조건검색에 검색된 종목리스트 가져오는 이벤트


    def receive_condition(self):
        condition_info = self.dynamicCall("GetConditionNameList()").split(';')


        for condition_name_idx_str in condition_info:
            if len(condition_name_idx_str) == 0:
                continue
            condition_idx, condition_name =condition_name_idx_str.split('^')
            if condition_name == "단기스윙":
                self.send_condition(self.screen_my_info, condition_name, condition_idx,0)  #단순 조건검색
            elif condition_name == "상한가":
                self.send_condition(self.screen_my_info,condition_name,condition_idx,0) #상한가 조건검색
    
    def send_condition(self, scrNum, condition_name, nidx, nsearch):
        # nSearch: 조회구분, 0:조건검색, 1:실시간 조건검색
        result = self.dynamicCall("SendCondition(QString, QString, int, int)" , scrNum, condition_name, nidx, nsearch)
        if result == 1:
            print("조건검색 등록 %s"  %condition_name)    

    def send_real_condition(self,scrNum,condition_name, nidx, nsearch):
        self.dynamicCall("SendCondition(QString, QString, int, int)" , scrNum, condition_name, nidx, nsearch)
        

    def receive_tr_condition(self, scrNum, strCodeList, strConditionName, nIndex, nNext):
        print("Received Tr condition, strCodelist, strConditionName, nIndex, nNext, scrNum: %s %s %s %s %s" %(strCodeList,strConditionName,nIndex,nNext,scrNum))
        for stock_code in strCodeList.split(';'):
            if len(stock_code) == 6 : #종목코드가 6자리인지 확인
                if strConditionName=="상한가":
                    self.jeonsang_meme.append(stock_code)
                self.condition_search_list.append(stock_code)
        self.loop.exit()

    #def buy_real_stock(self, code): #실시간 매매
    #     order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
    #                                       ["신규매수", self.realtime_buy_sell[code]["주문용스크린번호"], self.account_num, 1, code, 30, 0, self.reatlType.SENDTYPE['거래구분']['시장가'], ""])
          
        

                
        
        

    #def receive_real_condition(self, strCode, strType, strConditionName, strConditionIndex):
        # strType: 이벤트 종류, "I":종목편입, "D": 종목이탈
        # strConditionName 조건식 이름
        # strConditionIndedx: 조건명 인덱스
    #    print("Received real condition, %s, %s %s %s" %(strCode, strType, strConditionName, strConditionIndex))
    #    if strType == "I" and strCode not in self.realtime_buy_sell:
    #        print("15억 검색기 종목 검색!!")
    #        self.realtime_buy_sell.update({strCode:{}})
    #        
    #def set_real(self, scrNum, strCodeList, strFidList, strRealType):
    #    self.dynamicCall("SetRealReg(QString, QString, QString, QString)",scrNum, strCodeList, strFidList, strRealType)




        




    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def login_slot(self,errCode):
        print(errors(errCode))

        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop=QEventLoop()
        self.login_event_loop.exec_()


    def get_account_info(self):
        account_list=self.dynamicCall("GetLoginInfo(String)","ACCNO")

        self.account_num=account_num=account_list.split(';')[0]

        print("나의 계좌번호 %s " % self.account_num)

    def detail_account_info(self):
        print("예수금을 요청하는 부분")

        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, string)","예수금상세현황요청","opw00001","0",self.screen_my_info)

        self.detail_account_info_event_loop=QEventLoop()
        self.detail_account_info_event_loop.exec_()


    def detail_account_mystock(self,sPrevNext="0"):
        print("계좌평가 잔고내역 요청")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, string)","계좌평가잔고내역요청","opw00018",sPrevNext,self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    
    def not_concluded_account(self, sPrevNext="0"):
        print("미체결 요청")

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청","opt10075",sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()







    def trdata_slot(self,sScrNo,sRQName,sTrCode,sRecordName,sPrevNext):
        '''
        tr요청을 받는 구역이다! 슬롯이다!
        :param sScrNo: 스크린번호
        :param sRQName : 내가 요청햇을 때 지은 이름
        :param sTrCode: 요청id, tr코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''
        
        if sRQName=="예수금상세현황요청":
            deposit=self.dynamicCall("GetCommData(String, String, int, String)",sTrCode, sRQName, 0, "예수금")

            print("예수금 %s" % deposit)
            print("예수금 형변환 %s" % int(deposit))

            self.use_money=int(deposit) *self.use_money_percent
            self.use_money=self.use_money/4

            ok_deposit=self.dynamicCall("GetCommData(String, String, int, String)",sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % ok_deposit)
            print("출금가능금액 형변환 %s" % int(ok_deposit))

            self.detail_account_info_event_loop.exit()
        
        

        if sRQName=="계좌평가잔고내역요청":

            total_buy_money=self.dynamicCall("GetCommData(String, String, int, String)",sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result=int(total_buy_money)

            print("총매입금액 %s" % total_buy_money_result)

            total_profit_loss_rate=self.dynamicCall("GetCommData(String, String, int, String)",sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result=float(total_profit_loss_rate)

            print("총수익률(%s) : %s" % ("%", total_profit_loss_rate_result))

            rows=self.dynamicCall("GetRepeatCnt(QStringm,QString)",sTrCode, sRQName)
            cnt=0
            for i in range(rows):
                code =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "종목번호") 
                code=code.strip()[1:]

                code_nm=self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "종목명")
                stock_quantity =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "보유수량")
                buy_price =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "매입가")
                learn_rate =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "수익률(%)")
                current_price =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "현재가")
                total_chegual_price =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "매입금액")
                possible_quantity =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})
                
        
                
                code_nm=code_nm.strip()
                print(code_nm)
                stock_quantity=int(stock_quantity.strip())
                buy_price=int(buy_price.strip())
                learn_rate=float(learn_rate.strip())
                current_price=int(current_price.strip())
                total_chegual_price=int(total_chegual_price.strip()) 
                possible_quantity=int(possible_quantity.strip()) 
                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})
    
                cnt+=1
                
            
            print("계좌에 가지고 있는 종목 %s" % self.account_stock_dict)
            print("계좌에 보유종목 카운트 %s " %cnt)

            if sPrevNext=="2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()




        elif sRQName=="실시간미체결요청":
            
            rows=self.dynamicCall("GetRepeatCnt(QStringm,QString)",sTrCode, sRQName)

            for i in range(rows):
                code =self.dynamicCall("GetCommData(QString, QString,int, QString)",sTrCode, sRQName, i, "종목코드") 
                code_nm=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "종목명")
                order_no=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "주문번호")
                order_status=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "주문상태")  #접수,확인,체결
                order_quantity=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "주문수량")
                order_price=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "주문가격")
                order_gubun=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "주문구분")  # -매도, +매수, 정정 ,취소
                not_quantity=self.dynamicCall("GetCommData(QString, QString, i nt, QString)",sTrCode, sRQName, i, "미체결수량")
                ok_quantity=self.dynamicCall("GetCommData(QString, QString, int, QString)",sTrCode, sRQName, i, "체결량")

                code=code.strip()
                code_nm=code_nm.strip()
                order_no=int(order_no.strip())
                order_status=order_status.strip()
                order_quantity=int(order_quantity.strip())
                order_price=int(order_price.strip())
                order_gubun=order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity=int(not_quantity.strip())
                ok_quantity=int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no]={}
                
                self.not_account_stock_dict[order_no].update({"종목코드": code})
                self.not_account_stock_dict[order_no].update({"종목명": code_nm})
                self.not_account_stock_dict[order_no].update({"주문번호": order_no})
                self.not_account_stock_dict[order_no].update({"주문상태": order_status})
                self.not_account_stock_dict[order_no].update({"주문수량": order_quantity})
                self.not_account_stock_dict[order_no].update({"주문가격": order_price})
                self.not_account_stock_dict[order_no].update({"주문구분": order_gubun})
                self.not_account_stock_dict[order_no].update({"미체결수량": not_quantity})
                self.not_account_stock_dict[order_no].update({"체결량": ok_quantity})

                print("미체결 종목 : %s " % self.not_account_stock_dict[order_no])

            self.detail_account_info_event_loop.exit()

            
            
        
        if sRQName=="주식일봉차트조회":
            code=self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,0,"종목코드")
            code=code.strip()
            print("%s 일봉데이터 요청" %code)

            cnt=self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("데이터 일수 %s " %cnt)

            #data=self.dynamicCall("GetCommDataEx(QString,QString),sTrCode,sRQName"))
            # [ "","현재가","거래량,"거래대금...],["","현재가","거래량","거래대금"].. 이런식으로나옴

            #한번 조회시 600일치까지 일봉데이터 받을 수 있다.
            for i in range(cnt):
                data=[]

                current_price=int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가"))
                value=int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량"))
                trading_value=int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금"))
                date=int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자"))
                start_price=float(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가"))
                high_price=float(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가"))
                low_price=int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가"))

                data.append("")
                data.append(current_price)
                data.append(value)
                data.append(trading_value)
                data.append(date)
                data.append(start_price)
                data.append(high_price)
                data.append(low_price)
                data.append("")

                self.calcul_data.append(data.copy())
                    
            
            
            
            if sPrevNext=="2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)

            
            else:
                print("총 일수 %s" % len(self.calcul_data))

                pass_success=False
                pass_success2=False
                cnt=0
                print(self.calcul_data[0])
                max_value=self.calcul_data[0][2] #거래량 가장 많이 터진날의 거래량
                d=float(self.calcul_data[1][1]/self.calcul_data[2][1])-1 #2일전 종가 대비 1일전 종가등락율
                d*=100

                b=float(self.calcul_data[0][1]/self.calcul_data[1][1])-1 #전일 종가 대비 현재가 등락율
                b*=100
                for i in range(0,8):
                    if max_value<=self.calcul_data[i][2]:
                        max_value=self.calcul_data[i][2]
                
                for i in range(0,8):
                    a=(float((self.calcul_data[i][6])/self.calcul_data[i][5]))-1 #당일 시가 대비 고가 등락율
                    a*=100
                    c=(float((self.calcul_data[i][6])/self.calcul_data[i+1][1]))-1 #전일 종가 대비 고가 등락율
                    c*=100
               
                   # print("당일 시가 대비 고가 등락율 계산 : %.2f" %a)
                   # print("전일 종가 대비 고가 등락율 계산 : %.2f" %c)
                    if a>=10 and c>=15:  #시가대비 고가 등락율이 10%이상 캔들이 3개 이상 나올것 전일 종가대비 고가등락율 15%이상 
                        cnt+=1
                    
                    if cnt>=2: #장대양봉이 3개이상 나왓다면
                        if self.calcul_data[0][2] <= max_value/5 or self.calcul_data[1][2] <= max_value/5: #최근 2틀간 거래량이 급등하는 동안 제일 많이 터진 거래량 기준 1/5이하로 줄었다면
                            if b<-3 or d<-3:  # 이틀간 거래량이 줄고 이틀간 6%이상 빠졋을 경우 통과
                                pass_success=True
                              
                                print("거래대금 : %s" %self.calcul_data[0][3])
                                
                if cnt>=3 and ((b<-3 and d<-3) or b<-6) and self.calcul_data[0][2] <= max_value/5 and self.calcul_data[1][2] <= max_value/5:
                    code_nm=self.dynamicCall("GetMasterCodeName(QString)", code)
                    f=open("files/realcondition_stock.txt","a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close() 
                f=(float(self.calcul_data[0][1]/self.calcul_data[1][1])-1)*100
                if  self.calcul_data[0][3]>30000 and f>29: #전일 상한가이고 거래대금 300억이상
                    pass_success2=True


            
           
                if pass_success == True or pass_success2==True:
                    print("조건부 통과됨")

                    code_nm=self.dynamicCall("GetMasterCodeName(QString)", code)

                    f=open("files/condition_stock.txt","a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()
                    if pass_success2==True:
                        print("전상조건 통과")

                        code_nm=self.dynamicCall("GetMasterCodeName(QString)", code)
                        f=open("files/jeonsang.txt","a", encoding="utf8")
                        f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                        f.close()
                
                elif pass_success==False:
                    print("조건부 통과 못함")
                



                
                
                
                self.calcul_data.clear()
                self.calculator_event_loop.exit()
                
                



    def get_code_list_by_market(self,market_code):
        '''
        종목 코드들 반환
        :param market_code:
        :return:
        '''

        code_list=self.dynamicCall("GetCodeListByMarket(QString)",market_code)
        code_list=code_list.split(";")[:-1]

        return code_list
    

    def calculator_fnc(self):
        '''
        종목 분석 실행용 함수
        return;
        '''
        code_list=self.condition_search_list
        print(code_list)
        print("검색식에 포착된 종목의 갯수 %s" % len(code_list))

        for code in code_list:

            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)

            print(" %s : KOSDAQ Stock Code : %s is updating... " % (len(code_list),code))

            self.day_kiwoom_db(code=code, date=self.today)
            





    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(3600)

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date !=None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
            
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081",sPrevNext,self.screen_calculation_stock)
        self.calculator_event_loop.exec_()

    
    def read_code(self):
        if os.path.exists("files/condition_stock.txt"):
            
            f=open("files/condition_stock.txt", "r", encoding="utf8")

            lines=f.readlines()
            for line in lines:
                if line !="":

                    ls=line.split("\t")
                    
                    stock_code=ls[0]  
                    stock_name=ls[1]
                    stock_price=int(ls[2].split("\n")[0])
                    stock_price=abs(stock_price)

                self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})
            if os.path.exists("files/jeonsnag.txt"):
                s=open("files/jeonsang.txt", "r", encoding="utf8")
                lines=s.readlines()
                for line in lines:
                    if line !="":

                        ls=line.split("\t")
                    
                        stock_code=ls[0]  
                        stock_name=ls[1]
                        stock_price=int(ls[2].split("\n")[0])
                        stock_price=abs(stock_price)

                    self.jeonsang_meme.append(stock_code)
            
            f.close()

            #print(self.portfolio_stock_dict)
    



    
    def screen_number_setting(self):

        screen_overwrite=[]

        #계좌평가잔고내역에 있는 종목
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        
        #미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code=self.not_account_stock_dict[order_number]['종목코드']

            if code not in screen_overwrite:
                screen_overwrite.append(code)
        
        #포트폴리오에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        
        #스크린번호 할당
        cnt=0
        for code in screen_overwrite:

            temp_screen=int(self.screen_real_stock)
            meme_screen=int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen+=1   #"5000"->"5001"
                self.screen_real_stock=str(temp_screen)
            
            if (cnt % 50) == 0:
                meme_screen+=1
                self.screen_meme_stock=str(meme_screen)
            
            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호" : str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호" : str(self.screen_meme_stock)})
            
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호" :str(self.screen_real_stock),"주문용스크린번호": str(self.screen_meme_stock)}})

            cnt +=1
        print(self.portfolio_stock_dict)

    
    def realdata_slot(self, sCode, sRealType, sRealData):
        
        if sRealType =="장시작시간":
            fid=self.reatlType.REALTYPE[sRealType]['장운영구분']
            value=self.dynamicCall("GetCommRealData(QString,int)", sCode, fid)

            if value == '0':
                print("장 시작 전")
            
            elif value == '3':
                print("장 시작")
            
            elif value== '2':
                print("장 종료, 동시호가로 넘어감")
            
            elif value== '4':
                print("3시30분 장 종료")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(String,String)", self.portfolio_stock_dict[code]['스크린번호'],code)
                
                QTest.qWait(5000)

                self.file_delete()
                #self.calculator_fnc()

                sys.exit()
        
        elif sRealType =="주식체결":
            a = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['체결시간'])  #"HHMMSS"
            b = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['현재가'])  #+(-) 2500
            b=abs(int(b))

            c = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['전일대비'])  # 출력 : +(-)50
            c = abs(int(c))

            d = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['등락율'])  #+(-) 12.98
            d = float(d)

            e = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['(최우선)매도호가'])
            e = abs(int(e))

            f = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['(최우선)매수호가'])
            f = abs(int(f))

            g = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['거래량'])
            g = abs(int(g))

            h = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['누적거래량'])
            h = abs(int(h))

            i = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['고가'])
            i = abs(int(i))

            j = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['시가'])
            j = abs(int(j))

            k = self.dynamicCall("GetCommRealData(QString, int)" , sCode, self.reatlType.REALTYPE[sRealType]['저가'])
            k = abs(int(k))

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode : {}})
            
            self.portfolio_stock_dict[sCode].update({"체결시간": a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비": c})
            self.portfolio_stock_dict[sCode].update({"등락율": d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": f})
            self.portfolio_stock_dict[sCode].update({"거래량": g})
            self.portfolio_stock_dict[sCode].update({"누적거래량": h})
            self.portfolio_stock_dict[sCode].update({"고가": i})
            self.portfolio_stock_dict[sCode].update({"시가": j})
            self.portfolio_stock_dict[sCode].update({"저가": k})
            print(self.portfolio_stock_dict[sCode])
            

            # 계좌잔고평가내역에 있고 오늘 산 잔고에는 없을 경우 
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                asd = self.account_stock_dict[sCode]
                
                meme_rate=float((b-asd['매입가'])/asd['매입가'])*100 #등락율 구하기

                if asd['보유수량'] > 0 and  (meme_rate>8 or meme_rate < -10):
                    print("%s %s" % ("신규매도를 한다", sCode))
                    order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                    ["신규매도", self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 2, 
                                    sCode, asd['보유수량'], 0, self.reatlType.SENDTYPE['거래구분']['시장가'], ""] )
                    print(order_success)
                    
                    if order_success == 0:
                        print("매도주문 전달 성공")
                        file=open("files/buy_sell_result.txt","a", encoding="utf8")
                        file.write("%s\t%s\t%s\t%s\t%s\t%.2f\n" % (self.today ,sCode,asd['종목명'] ,asd['매입가'],f,(f/asd['매입가']-1)*100))
                        del self.account_stock_dict[sCode]
                    else:
                        print("매도주문 전달 실패")


            
            # 오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():
                jd = self.jango_dict[sCode]
                meme_rate = (b - jd['매입단가']) / jd['매입단가'] * 100
                meme_rate=int(abs(meme_rate))

                if int(jd['보유수량']) > 0 and (meme_rate > 8 or meme_rate < -6) and sCode not in self.jeonsang_meme:
                    print("%s %s" % ("신규매도를 한다2", sCode))
                    order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, int, QString, QString)", ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"]
                                                     ,self.account_num, 2, sCode, jd['보유수량'], 0, self.reatlType.SENDTYPE['거래구분']['시장가'], ""])
                    print(order_success)
                    if order_success == 0:
                        print("매도주문 전달 성공")
                        file=open("files/buy_sell_result.txt","a", encoding="utf8")
                        file.write("%s\t%s\t%s\t%s\t%s\t%.2f\n" % (self.today,sCode,jd['종목명'] ,jd['매입단가'],f,(f/jd['매입단가']-1)*100 ))
                    else:
                        print("매도주문 전달 실패")
                    
                if int(jd['보유수량']) > 0 and (meme_rate > 3 or meme_rate < -3) and sCode in self.jeonsang_meme:
                    print("%s %s" % ("신규매도를 한다2", sCode))
                    order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, int, QString, QString)", ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"]
                                                     ,self.account_num, 2, sCode, jd['보유수량'], 0, self.reatlType.SENDTYPE['거래구분']['시장가'], ""])
                    if order_success == 0:
                        print("매도주문 전달 성공")
                        file=open("files/buy_sell_result.txt","a", encoding="utf8")
                        file.write("%s\t%s\t%s\t%s\t%s\t%.2f\n" % (self.today,sCode,jd['종목명'] ,jd['매입단가'],f,(f/jd['매입단가']-1)*100))
                    else:
                        print("매도주문 전달 실패")
   
                    
                



            
            # 오늘 산 잔고에 없을 경우 등락율이 -2%이상
            elif d <-2 and sCode not in self.jango_dict and sCode in self.portfolio_stock_dict:
                print("%s %s" % ("신규매수를 한다", sCode))

                quantity = 10
                print(quantity)

                order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                                 ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode, quantity, 0, self.reatlType.SENDTYPE['거래구분']['시장가'], ""])
                
                if order_success == 0:
                    print("매수주문 전달 성공")
                else:
                    print("매수주문 전달 실패")




            
            not_meme_list =  self.not_account_stock_dict.copy()
            for order_num in not_meme_list:
                code=self.not_account_stock_dict[order_num]["종목코드"]
                meme_price=self.not_account_stock_dict[order_num]['주문가격']
                not_quantity=self.not_account_stock_dict[order_num]['미체결수량']
                order_gubun=self.not_account_stock_dict[order_num]['주문구분']
                

                if order_gubun == "매수" and not_quantity > 0 and e > meme_price:
                    order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                                     ["매수취소", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 3, code, 0, 0, self.reatlType.SENDTYPE['거래구분']['지정가'],  order_num])
                    
                    if order_success == 0:
                        print("매수취소 전달 성공")
                    else:
                        print("매수취소 전달 실패")
                
                elif not_quantity == 0:
                    del self.not_account_stock_dict[order_num]

    
    def chejan_slot(self, sGubun, nItemCnt, sFIdList):

        if int(sGubun) == 0:
            account_num = self.dynamicCall("GetChejanData(int)" ,self.reatlType.REALTYPE['주문체결']['계좌번호'])
            sCode =(self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['종목코드']))
            sCode=str(sCode)
            sCode=sCode[1:]
            stock_name = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()

            origin_order_number = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['주문체결']['원주문번호'])
            order_number = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['주문체결']['주문번호'])

            order_status = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['주문상태'])

            order_quan = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)

            order_price = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['주문가격'])
            order_price = int(order_price)

            not_chegual_quan = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['미체결수량'])
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['주문구분'])
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            chegual_time_str = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['주문체결']['주문/체결시간'])

            chegual_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['주문체결']['체결가'])

            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['체결량'])

            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
            
            current_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['주문체결']['현재가'])
            current_price = abs(int(current_price))

            first_sell_price = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['(최우선)매도호가'])

            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['주문체결']['(최우선)매수호가'])

            first_buy_price = abs(int(first_buy_price))


            ###### 새로 들어온 주문이면 주문번호 할당
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number : {}})

            self.not_account_stock_dict[order_number].update({"종목코드" : sCode})
            self.not_account_stock_dict[order_number].update({"주문번호" : order_number})
            self.not_account_stock_dict[order_number].update({"종목명" : stock_name})
            self.not_account_stock_dict[order_number].update({"주문상태" : order_status})
            self.not_account_stock_dict[order_number].update({"주문수량" : order_quan})
            self.not_account_stock_dict[order_number].update({"주문가격" : order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량" : not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"원주문번호": origin_order_number})
            self.not_account_stock_dict[order_number].update({"주문구분" : order_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간" : chegual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가" : chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량" : chegual_quantity})
            self.not_account_stock_dict[order_number].update({"현재가" : current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가" : first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매수호가" : first_buy_price})

            print(self.not_account_stock_dict)

        
        elif int(sGubun) == 1:
            account_num = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)" , self.reatlType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name=self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['종목명'])
            stock_name=stock_name.strip()

            current_price =self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['주문가능수량'])
            lie_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['총매입가'])
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.reatlType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.reatlType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))


            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode: {}})
            
            self.jango_dict[sCode].update({"현재가": current_price})
            self.jango_dict[sCode].update({"종목코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": like_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가": total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})

            if stock_quan == 0:
                del self.jango_dict[sCode]
                print(self.portfolio_stock_dict)
                self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[sCode]['스크린번호'], sCode)



    def condition_search(self):
        print("조건 검색식에 대한 정보 요청")
        self.dynamicCall("GetConditionLoad()") #조건 검색 정보 요청
        self.loop.exec_()








    

    #송수신 메시지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        print("스크린: %s, 요청이름: %s, tr코드: %s --- %s" %(sScrNo, sRQName, sTrCode, msg))
    
    #파일 삭제
    def file_delete(self):
        if os.path.isfile("files/condition_stock.txt"):
            os.remove("files/condition_stock.txt")
            os.remove("files/jeonsang.txt")
    
        




              


              





            

        




                    




                

            






            


        


        



    
















        





    















    


    


    
    