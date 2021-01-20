import os, time, json, re, logging
import bisect

from kubernetes import client, config

GET_PODS_NAMESPACE = os.environ.get("GET_PODS_NAMESPACE")

formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter)

global recommendstock_set
recommendstock_set = set()

def getcurrentprice():
    config.load_incluster_config()
    dic = dict()

    try:
        api_instance = client.CoreV1Api()
        podlist = api_instance.list_namespaced_pod(GET_PODS_NAMESPACE)
    except:
        logging.warning('Failed getting pods list')
        return dic

    for pod in podlist.items:
        try:
            if pod.status.phase == "Succeeded":
                pod_name = pod.metadata.name
                api_response = api_instance.read_namespaced_pod_log(name=pod_name, namespace=GET_PODS_NAMESPACE)
                apires = api_response.split("\n")
                strd = re.sub(r".*(?=\{)", "", apires[-2])
                d = json.loads(strd.replace("'", '"'))
                dic.update(d)
        except:
            logging.warning("Failed updating the percentage increase dictionary by [" + str(pod_name) + "] pod")
    
    return dic


def recommend(stockpricedic):
    price_movement_limit_tuple = (())
    ls = []

    for stockid in stockpricedic.keys():
        price, price_movement = stockpricedic[stockid]
        plindex = bisect.bisect_left(ls, price - price_movement)
        price_movement_limit = price_movement_limit_tuple[plindex][1]

        if True: recommendstock_set.add(stockid)

    return

def main():
    stock_price_dic = getcurrentprice()
    
    recommend(stock_price_dic)

    logging.info(recommendstock_set)

    return

if __name__ == "__main__":
    main()