import os, logging, time, datetime, re

from kubernetes import client, config
from kubernetes.client.models import V1Job, V1ObjectMeta, V1Container, V1PodSpec, V1EnvVar

formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter)

GET_RECOMMENDER_NAMESPACE = os.environ.get("GET_RECOMMENDER_NAMESPACE")
TRADE_PWD = os.environ.get("TRADE_PWD")
LOGIN_ID = os.environ.get("LOGIN_ID")
LOGIN_PASS = os.environ.get("LOGIN_PASS")
LOGIN_PAGE_ID = os.environ.get("LOGIN_PAGE_ID")
LOGIN_CONTROL_ID = os.environ.get("LOGIN_CONTROL_ID")
GET_PRICE_PAGE_ID = os.environ.get("GET_PRICE_PAGE_ID")
GET_PRICE_DATA_STORE_ID = os.environ.get("GET_PRICE_DATA_STORE_ID")
GET_PRICE_CONTROL_ID = os.environ.get("GET_PRICE_CONTROL_ID")
GET_BUYING_POWER_PAGE_ID = os.environ.get("GET_BUYING_POWER_PAGE_ID")
GET_BUYING_POWER_DATA_STORE_ID = os.environ.get("GET_BUYING_POWER_DATA_STORE_ID")
GET_BUYING_POWER_CONTROL_ID = os.environ.get("GET_BUYING_POWER_CONTROL_ID")
GET_STOCK_HOLDINGS_PAGE_ID = os.environ.get("GET_STOCK_HOLDINGS_PAGE_ID")
GET_STOCK_HOLDINGS_DATA_STORE_ID = os.environ.get("GET_STOCK_HOLDINGS_DATA_STORE_ID")
GET_STOCK_HOLDINGS_CONTROL_ID = os.environ.get("GET_STOCK_HOLDINGS_CONTROL_ID")
BUY_ORDER_PAGE_ID = os.environ.get("BUY_ORDER_PAGE_ID")
BUY_ORDER_CONTROL_ID = os.environ.get("BUY_ORDER_CONTROL_ID")
SELL_ORDER_PAGE_ID = os.environ.get("SELL_ORDER_PAGE_ID")
SELL_ORDER_CONTROL_ID = os.environ.get("SELL_ORDER_CONTROL_ID")
ORDER_CANCEL_PAGE_ID = os.environ.get("BUY_ORDER_CANCEL_PAGE_ID")
ORDER_CANCEL_CONTROL_ID = os.environ.get("BUY_ORDER_CANCEL_CONTROL_ID")

class tradeClient():
    def __init__(self):
        self.recommend_stocks_set = set()
        self.new_recommend_stocks_set = set()

        config.load_incluster_config()

    def getcurrentrecommendstocks(self):
        try:
            api_instance = client.CoreV1Api()
            podlist = api_instance.list_namespaced_pod(namespace=GET_RECOMMENDER_NAMESPACE)
            logging.info("Successed getting pods list from recommend namespace")
        except:
            logging.warning('Failed getting pods list from recommend namespace')
            return 

        for pod in podlist.items:
            try:
                if pod.status.phase == "Succeeded":
                    pod_name = pod.metadata.name
                    api_response = api_instance.read_namespaced_pod_log(name=pod_name, namespace=GET_RECOMMENDER_NAMESPACE)
                    apires = api_response.split("\n")
                    strs = re.sub(r".*(?=\{)", "", apires[-2])
                    s = set(strs.replace("'", "").replace("{", "").replace("}", "").replace(" ", "").split(","))
                    self.new_recommend_stocks_set |= s
                    logging.info("Successed get recommend stocks from pod {}".format(pod_name))
            except:
                logging.warning("Failed to get recommend stocks from pod {}".format(pod_name))

        self.new_recommend_stocks_set -= self.recommend_stocks_set
        
        return 


    def request_traders(self):
        for stockid in self.new_recommend_stocks_set:
            self.request_trader(stockid=stockid)

        return


    def request_trader(self, stockid):
        config.load_incluster_config()

        v1 = client.BatchV1Api()

        job=client.V1Job()
        job.metadata=client.V1ObjectMeta(name="trader{}".format(stockid))

        container=client.V1Container(name="trader{}".format(stockid), image="outk/trader:v0.0.1", image_pull_policy="IfNotPresent")
        container.env = [
            V1EnvVar(name="STOCK_ID", value=stockid),
            V1EnvVar(name="TRADE_PWD", value=TRADE_PWD),
            V1EnvVar(name="LOGIN_ID", value=LOGIN_ID),
            V1EnvVar(name="LOGIN_PASS", value=LOGIN_PASS),
            V1EnvVar(name="LOGIN_PAGE_ID", value=LOGIN_PAGE_ID),
            V1EnvVar(name="LOGIN_CONTROL_ID", value=LOGIN_CONTROL_ID),
            V1EnvVar(name="GET_PRICE_PAGE_ID", value=GET_PRICE_PAGE_ID),
            V1EnvVar(name="GET_PRICE_DATA_STORE_ID", value=GET_PRICE_DATA_STORE_ID),
            V1EnvVar(name="GET_PRICE_CONTROL_ID", value=GET_PRICE_CONTROL_ID),
            V1EnvVar(name="GET_BUYING_POWER_PAGE_ID", value=GET_BUYING_POWER_PAGE_ID),
            V1EnvVar(name="GET_BUYING_POWER_DATA_STORE_ID", value=GET_BUYING_POWER_DATA_STORE_ID),
            V1EnvVar(name="GET_BUYING_POWER_CONTROL_ID", value=GET_BUYING_POWER_CONTROL_ID),
            V1EnvVar(name="GET_STOCK_HOLDINGS_PAGE_ID", value=GET_STOCK_HOLDINGS_PAGE_ID),
            V1EnvVar(name="GET_STOCK_HOLDINGS_DATA_STORE_ID", value=GET_STOCK_HOLDINGS_DATA_STORE_ID),
            V1EnvVar(name="GET_STOCK_HOLDINGS_CONTROL_ID", value=GET_STOCK_HOLDINGS_CONTROL_ID),
            V1EnvVar(name="BUY_ORDER_PAGE_ID", value=BUY_ORDER_PAGE_ID),
            V1EnvVar(name="BUY_ORDER_CONTROL_ID", value=BUY_ORDER_CONTROL_ID),
            V1EnvVar(name="SELL_ORDER_PAGE_ID", value=SELL_ORDER_PAGE_ID),
            V1EnvVar(name="SELL_ORDER_CONTROL_ID", value=SELL_ORDER_CONTROL_ID),
            V1EnvVar(name="ORDER_CANCEL_PAGE_ID", value=ORDER_CANCEL_PAGE_ID),
            V1EnvVar(name="ORDER_CANCEL_CONTROL_ID", value=ORDER_CANCEL_CONTROL_ID)
        ]

        spec=client.V1PodSpec(containers=[container], restart_policy="Never")
        podtemplatespec = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(name="trader{}".format(stockid)), spec=spec)

        jobspec = client.V1JobSpec(template=podtemplatespec, ttl_seconds_after_finished=12*60*60)
        job.spec = jobspec

        v1.create_namespaced_job(namespace="trader",body=job)

        logging.info("trader{} job created.".format(stockid))

        return


if __name__ == "__main__":
    trade_client = tradeClient()
    while datetime.datetime.now().hour < 6:
        trade_client.getcurrentrecommendstocks()
        trade_client.request_traders()
        trade_client.recommend_stocks_set |= trade_client.new_recommend_stocks_set
        trade_client.new_recommend_stocks_set.clear()

        time.sleep(60)