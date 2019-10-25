# Prometheus p2peye_exporter

## 为什么做
P2P 网上理财平台众多，集中导航平台`网贷天眼`上也是五花八门。为了便于简洁列表展示及方便排序筛选。同时不想交互数据库，就用 Prometheus + exporter + Grafana 方式来实现。

## 指标数据
```
# HELP build_info 
# TYPE build_info gauge
build_info{github="https://github.com/evandeng2009/p2peye_exporter",version="2019-01-28"} 1.0
# HELP p2peye_rebate P2peye rebates
# TYPE p2peye_rebate gauge
p2peye_rebate{all_roi="116.67",all_roi_rate="28%",beginner_flag="是",comment_url="https://zonefang.p2peye.com/comment/",duration="1个月",location="福建省福州市",min_amount="5000",online_date="2014年02月20日",p2peye_return="35",registered_capital="100000000",return_per_day="7.78",solution="方案-1",url="https://licai.p2peye.com/rebate/280-1-10.html",user="evand",vendor="众房宝"} 1.0
p2peye_rebate{all_roi="198.33",all_roi_rate="23.8%",beginner_flag="是",comment_url="https://zonefang.p2peye.com/comment/",duration="1个月",location="福建省福州市",min_amount="10000",online_date="2014年02月20日",p2peye_return="75",registered_capital="100000000",return_per_day="6.61",solution="方案-2",url="https://licai.p2peye.com/rebate/280-1-10.html",user="evand",vendor="众房宝"} 1.0
p2peye_rebate{all_roi="530",all_roi_rate="21.2%",beginner_flag="是",comment_url="https://zonefang.p2peye.com/comment/",duration="1个月",location="福建省福州市",min_amount="30000",online_date="2014年02月20日",p2peye_return="240",registered_capital="100000000",return_per_day="5.89",solution="方案-3",url="https://licai.p2peye.com/rebate/280-1-10.html",user="evand",vendor="众房宝"} 1.0
p2peye_rebate{all_roi="505",all_roi_rate="20.2%",beginner_flag="是",comment_url="https://zonefang.p2peye.com/comment/",duration="3个月",location="福建省福州市",min_amount="10000",online_date="2014年02月20日",p2peye_return="80",registered_capital="100000000",return_per_day="5.61",solution="方案-4",url="https://licai.p2peye.com/rebate/280-1-10.html",user="evand",vendor="众房宝"} 1.0
```

## 看板变量
![看板变量](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/dashboard_variables.png)
* 平台变量 `label_values(p2peye_rebate, vendor)`
![平台变量](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/vendor_definiton.png)
* 新手变量 `label_values(p2peye_rebate{vendor=~"$vendor"}, beginner_flag)`
![新手变量](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/beginner_definiton.png)
* 周期变量 `label_values(p2peye_rebate{vendor=~"$vendor", beginner_flag=~"$beginner_flag"}, duration)`
![周期变量](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/duration_definiton.png)

## 数据看板
* 标的筛选 table `p2peye_rebate{vendor=~"$vendor", beginner_flag=~"$beginner_flag", duration=~"$duration"}`
![标的筛选](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/rebate_selector.png)
* 标的分布 graph的 series 和 time, Legend 使用{{vendor}} `count(p2peye_rebate) by(vendor)`
![标的分布](https://github.com/evandeng2009/p2peye_exporter/raw/master/docs/trend_series.png)

# 参数配置
* 端口默认 8047
```Python
# Get app port
def get_port():
    if 'p2peye_port' in os.environ.keys():
        app_port = os.environ.get('p2peye_exporter_port')
    else:
        app_port = 8087
    return app_port
```
* 账号密码 浏览器登录时 F12 从 post 请求参数中复制获取密码参数值
```Python
user_name = 'p2peye_user_name'
user_password = 'p2peye_user_password_in_browser_request'
```
* 看板配置 Prometheus 采集频率和看板时间范围推荐设置为每天和最近 24 小时

## 编译运行
* 直接运行`build_install.sh`
* 或者运行`p2peye_exporter.py`
* 最后打开如 127.0.0.1:8087/metrics 查看指标数据