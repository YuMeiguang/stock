# 极速引擎
- 任何时候趋势都是王道，任何一个操作都要顺势而为，永远不要和趋势作对
- 启动方式 `nohup python3 -u stock.py >> index.html 2>&1 &`
- 管理台项目 后续继续开源，敬请期待 
- 如有疑问，请联系 470215591@qq.com
## 配置文件不提交
config.ini
## 主要功能
- 买点卖点预测
- 趋势预测
- 活跃度计算
- 选股 (强势股，业绩股)
- 短信提醒
- 活跃股推荐
- 低吸推荐
- 最高价和最低价
- 趋势翻转纠正
- 分钟级别数据获取
- 市场全量股票数据获取
- 个股模型预测

### config.ini
- 相关配置
### judgeTrend.py
 * 1)判断趋势
 * 2)获取涨跌幅
 * 3)预测最高价最低价
 * 4)预测买点和卖点
### stock.py
* 1)基本数据获取
* 2)分钟级别数据
### modify.py
* 1)修正脚本
* 2)修整买点卖点
* 3)增加修改标识
* 4)截止时间为11点
* 5)针对预测幅度为7以下的进行调整
### chooseStock.py
* 1)选股 强势  稳健  牛股
* 2)排除自选股列表数据
### smsSend.py
* 1)发送各类短信通知
* 2)避免发重复短信
### syn.py
* 1)同步当天所有股票的基本信息数据
* 2)调用其他模块进行新发型股票的拉取
### day_info.py
* 1)查询目前市场上所有股票 包含 00 60 300 68开头的
* 2)对发现新上市的股票进行汇总到股票名单里

# 常用sql
# 偏差计算
SELECT stock_name,stock_code,(pre_max_amplitude-real_amplitude)/(pre_max_amplitude+real_amplitude)*10 AS pre,pre_max_amplitude,real_amplitude
FROM stock_day_base_Info  ORDER BY pre_max_amplitude;

# 买点收益比计算
SELECT ((close_price-pre_buy_point)/pre_buy_point)*100  profitRatio,stock_name FROM stock_day_base_Info_imitate WHERE trend=1 AND DATE(create_time)='2020-04-20' AND close_price IS NOT NULL AND low_price<pre_buy_point ;
# 卖点收益比计算

# 计算10点后出现最低点股票
SELECT ((A.close_price-A.pre_buy_point)/A.pre_buy_point)*100  profitRatio,A.stock_name,A.pre_max_amplitude,B.now_time FROM stock_day_base_Info A,stock_data b WHERE A.trend=1 AND A.stock_code=b.stock_code AND DATE(A.create_time)='2020-04-21' AND A.low_price=B.lowest_price AND B.now_time>'2020-04-21 10:00:00' AND DATE(A.create_time)='2020-04-21' AND A.close_price IS NOT NULL AND A.low_price<=A.pre_buy_point ;

# 买点位置
SELECT A.stock_code,A.stock_name,A.pre_buy_point,B.end_price,A.pre_low_price,A.pre_max_amplitude,B.now_time
FROM stock_day_base_Info A,stock_data B WHERE
  A.stock_code=B.stock_code AND B.now_time>'2020-04-22 11:00:00' AND A.pre_buy_point>B.lowest_price
  AND  A.pre_max_amplitude>5 AND B.end_price<A.pre_low_price ORDER BY B.now_time DESC ;

# 预测成功率计算
SELECT stock_name,trend,(close_price-start_price)>0,start_price,create_time,yesterday_price FROM stock_day_base_Info;

# 合适买点的收益比

SELECT ((close_price-stock_day_base_Info.pre_buy_point)/yesterday_price)*100 AS 收益比,trend AS 趋势,stock_name AS 股票名 FROM stock_day_base_Info WHERE  stock_code in(SELECT DISTINCT(A.stock_code) FROM stock_day_base_Info A,stock_data B WHERE A.stock_code=B.stock_code AND b.now_time> '2020-04-27 10:00:00' AND A.pre_buy_point>B.lowest_price);

# 趋势正确的话收益比

SELECT ((close_price-pre_buy_point)/yesterday_price)*100 AS 收益比,trend AS 趋势,stock_name AS 股票名 FROM stock_day_base_Info WHERE (trend>0)=(close_price-start_price>0) AND stock_code in(SELECT DISTINCT(A.stock_code) FROM stock_day_base_Info A,stock_data B WHERE A.stock_code=B.stock_code AND b.now_time> '2020-04-27 10:00:00' AND A.pre_buy_point>B.lowest_price);

# 九点四十趋势确定卖出收益比
SELECT A.stock_name,((B.end_price-A.close_price)/A.yesterday_price)*100 FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE A.forty_trend=0 AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

# 九点四十后趋势向下随时卖出收益比
SELECT SUM(((B.end_price-A.close_price)/A.yesterday_price)*100)/1452 FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE A.forty_trend=0 AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

SELECT A.stock_name,((B.end_price-A.close_price)/A.yesterday_price)*100 FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE  A.forty_trend=1 AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

SELECT count(*) FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE  A.forty_trend=1 AND A.trend=1 AND A.close_price>A.start_price AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

SELECT count(*) FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE  A.forty_trend=0 AND A.trend=-1 AND A.close_price<A.start_price  AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

1260+77/2276


SELECT count(*) FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE  A.trend=1 AND A.close_price>A.start_price AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

SELECT count(*) FROM stock_day_base_Info_imitate A,stock_data_imitate B WHERE   A.trend=-1 AND A.close_price<A.start_price  AND A.stock_code=B.stock_code AND B.now_time='2020-04-28 09:40:00' ;

1264+349/2264  上涨的准确率较高

1700 +86/2264   下跌的准确率较高

# 收益率
SELECT A.stock_name  AS 股票名字,A.pre_buy_point AS 买点,B.end_price,(B.end_price- A.pre_buy_point)/A.yesterday_price*100 目前收益比,A.trend AS 趋势,pre_max_amplitude AS 估计振幅,B.now_time FROM stock_day_base_Info A,stock_data B WHERE A.stock_code=B.stock_code AND b.now_time> '2020-04-29 10:00:00' AND A.pre_low_price<B.end_price AND A.stock_code in(SELECT DISTINCT(A.stock_code) FROM stock_day_base_Info A,stock_data B WHERE A.stock_code=B.stock_code AND b.now_time BETWEEN '2020-04-29 10:00:00' AND '2020-04-29 15:00:00' AND A.pre_buy_point>B.lowest_price) ORDER BY B.now_time DESC,目前收益比 DESC ;
# 趋势股选股逻辑

INSERT INTO  hold_stock(stock_code,stock_name,create_time)
SELECT A.stock_code,A.stock_name,now()
FROM
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-29' AND rize_amplitude >-1) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-28' AND rize_amplitude >-2 AND amplitude>=3) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-2 AND amplitude>=3) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-23' AND rize_amplitude >-2 AND amplitude>=3) D
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code;

SELECT *
FROM hold_stock WHERE stock_code IN(SELECT A.stock_code
FROM
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-29' AND rize_amplitude >-1) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-28' AND rize_amplitude >-2 AND amplitude>=3) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-2 AND amplitude>=3) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-23' AND rize_amplitude >-2 AND amplitude>=3) D
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code);

# 回调股选股逻辑

SELECT A.stock_code,A.stock_name,now()
FROM
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-29' AND rize_amplitude >-1) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-28' AND rize_amplitude >-5 AND rize_amplitude<-1 AND amplitude>=4) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-8  AND rize_amplitude<-2 AND amplitude>=4) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-23' AND rize_amplitude >-8  AND  rize_amplitude<-2 AND amplitude>=4) D
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code ;


INSERT INTO  hold_stock(stock_code,stock_name,create_time)
SELECT A.stock_code,A.stock_name,now()
FROM
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-29' AND rize_amplitude >-1) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-28' AND rize_amplitude >-5 AND rize_amplitude<-1 AND amplitude>=4) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-8  AND rize_amplitude<-2 AND amplitude>=4) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-23' AND rize_amplitude >-8  AND  rize_amplitude<-2 AND amplitude>=4) D
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code ;


# 弱势趋势转升股票
SELECT A.stock_code,A.stock_name AS 股票名,((A.open_price-A.yesterday_price)/A.yesterday_price)*100 AS 当天开盘涨幅,(A.rize_amplitude-((A.open_price-A.yesterday_price)/A.yesterday_price)*100) AS 当天买入收益比,A.rize_amplitude AS 当天涨幅,((O.open_price-O.yesterday_price)/O.yesterday_price)*100 AS 第二天开盘涨幅,((O.end_price-O.yesterday_price)/O.yesterday_price)*100 AS 第二天收盘涨幅,((A.yesterday_price-E.yesterday_price)/E.yesterday_price)*100 AS 回调幅度,A.yesterday_price,E.yesterday_price
FROM
  (SELECT stock_code,stock_name,yesterday_price,rize_amplitude,open_price,end_price FROM hold_stock_day_info WHERE  deal_date='2020-04-28') O,
  (SELECT stock_code,stock_name,yesterday_price,rize_amplitude,open_price,end_price FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-2) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-24' AND rize_amplitude >-3 AND amplitude>=3) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-23' AND rize_amplitude >-4 AND amplitude>=3) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-22' AND rize_amplitude >-5 AND amplitude>=3) D,
  (SELECT stock_code,stock_name,yesterday_price FROM hold_stock_day_info WHERE  deal_date='2020-02-25') E
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code AND D.stock_code=E.stock_code AND o.stock_code=A.stock_code AND ((A.yesterday_price-E.yesterday_price)/E.yesterday_price)*100<-20 AND ((E.yesterday_price-A.yesterday_price)/E.yesterday_price)>-60  ORDER BY 回调幅度 ;
# 选股
SELECT A.stock_code,A.stock_name AS 股票名,((A.yesterday_price-E.yesterday_price)/E.yesterday_price)*100 AS 回调幅度,((A.open_price-A.yesterday_price)/A.yesterday_price)*100 AS 当天开盘涨幅,(A.rize_amplitude-((A.open_price-A.yesterday_price)/A.yesterday_price)*100) AS 当天买入收益比,A.yesterday_price,E.yesterday_price
FROM
  (SELECT stock_code,stock_name,yesterday_price,rize_amplitude,open_price,end_price FROM hold_stock_day_info WHERE  deal_date='2020-04-30' AND rize_amplitude >-2) A,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-29' AND rize_amplitude >-3 AND amplitude>=3) B,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-28' AND rize_amplitude >-4 AND amplitude>=3) C,
  (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE  deal_date='2020-04-27' AND rize_amplitude >-5 AND amplitude>=3) D,
  (SELECT stock_code,stock_name,yesterday_price FROM hold_stock_day_info WHERE  deal_date='2020-02-25') E
where A.stock_code = B.stock_code AND B.stock_code=C.stock_code AND C.stock_code=D.stock_code AND D.stock_code=E.stock_code AND ((A.yesterday_price-E.yesterday_price)/E.yesterday_price)*100<-20 AND ((E.yesterday_price-A.yesterday_price)/E.yesterday_price)>-60  ORDER BY 回调幅度 ;

# 十字星选股
SELECT * FROM hold_stock_day_info where deal_date='2020-10-26' and ((high_price-low_price)/yesterday_price)*100>6 and abs(((end_price-open_price)/yesterday_price)*100)<2 and stock_code like '300%' AND stock_code in(select stock_code from hold_stock);;

