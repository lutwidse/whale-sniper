import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
#LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo

API = "https://fcd.terra.dev/v1/txs?limit=100&account="
KUJIRA_ORCA_AUST_VAULT = "terra13nk2cjepdzzwfqy740pxzpe3x75pd6g0grxm2z"
BLUNA = "terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp"

class WhaleSniper:
    def __init__(self):
        self.transactions = []
        self.bids = []

    def init(self):
        self.transactions = []
        self.bids = []

    def get_transactions(self):
        with open("whale_sniper/whale.txt", "r") as f:
            for w in f.readlines():
                address = w.strip("\n")
                res = requests.get(f"{API}{address}")
                self.transactions.append(res.json())
    
    def get_bids(self):
        for transaction in self.transactions:
            for txs in transaction["txs"]:
                if len(txs["logs"]) == 0:
                    continue
                
                logs = txs["logs"][0]
                if len(logs) != 3:
                    continue
                
                events = logs["events"]
                if len(events) != 4:
                    continue
                
                sender_contract = events[0]["attributes"][0]["value"]
                from_contract = events[1]["attributes"]
                wasm = events[3]["attributes"]
                
                if len(from_contract) !=16:
                    continue
                
                if from_contract[3]["value"] != KUJIRA_ORCA_AUST_VAULT:
                    continue
                
                collateral_token = wasm[10]["value"]
                if collateral_token == BLUNA:
                    timestamp = txs["timestamp"]
                    utc_timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=ZoneInfo("US/Central"))
                    #local_timestamp = utc_timestamp.astimezone(LOCAL_TIMEZONE)

                    amount = wasm[8]["value"]
                    premium_slot = wasm[9]["value"]
                    strategy_activate_ltv = wasm[12]["value"]
                    strategy_activate_amount = wasm[13]["value"]
                    amount = amount[:-6] if len(amount) > 6 else amount[:-5]
                    self.bids.append([utc_timestamp.isoformat(" "), f"{sender_contract[6:14]}", f"{'{:.2f}'.format((int(amount)/100000))}M", f"{premium_slot}%", f"{strategy_activate_ltv}%", f"{int(strategy_activate_amount)/1000000000000}M"])

    def extract_bids(self):
        sorted_bids = sorted(self.bids, key=lambda t: datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S%z"), reverse=True)
        with open("whale_sniper/whale_bot.csv", "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "sender", "amount", "premium_slot", "strategy_activate_ltv", "strategy_activate_amount"])
            writer.writeheader()
            for i in sorted_bids:
                writer.writerow({
                        "timestamp": i[0],
                        "sender": i[1],
                        "amount": i[2],
                        "premium_slot": i[3],
                        "strategy_activate_ltv": i[4],
                        "strategy_activate_amount": i[5]
                        })
    
    def get_extracted_bids(self):
        with open("whale_sniper/whale_bot.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile)
            b = ""
            for i, j in enumerate(reader):
                b += (
                      f"{j['timestamp']} - {j['sender']} \n"
                    + f"[Amount] {j['amount']} [Premium] {j['premium_slot']} [BLT] {j['strategy_activate_ltv']} [ARCT] {j['strategy_activate_amount']} \n\n")
                if i == 4:
                    return b