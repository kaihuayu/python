import requests

 
from pyquery import PyQuery as pq
 
def get_page(url):
    """发起请求 获得源码"""
    r = requests.get(url)
    r.encoding = 'gb2312'    
    html = r.text   
    #html =html.decode('gb2312').encode('utf8')
    return html
 
def parse(text):
    doc = pq(text)
    # 获得每一行的tr标签 alt是行的类名
    #tds = doc('table.list_table tbody tr.head').items()
    print(doc('.list_table:eq(1) tr.head ').html())# doc  类名标签 获取内容
    tds = doc('.list_table:eq(1)  tr.head ').items()
    i=0
    with open('collegelist.csv', 'a+', encoding='utf8') as f:
        for td in tds :
            
            i=i+1
            #rank = td.find('td:first-child').text()      
            #city = td.find('td:nth-child(0)').text()
            if i>3:
                code = td.find('td:nth-child(2)').text() #  下面第几个TD
                name = td.find('td:nth-child(3)').text()
                print(code)
                #f.write(rank + ',')
                f.write(name + ',')
                #f.write(city + ',')
                f.write(code + ',\n')
    print("complete!")
 
if __name__ == "__main__":
    url = "http://vip.stock.finance.sina.com.cn/q/go.php/vInvestConsult/kind/rzrq/index.phtml"
    text = get_page(url)
    #print(text).encode(type)
    parse(text)
