import requests
from datetime import datetime, timedelta
import csv

TERRA_API = "https://fcd.terra.dev/"
TXS_API = TERRA_API + "v1/txs?limit=100&account="

ALPHA_DEFI_API = "https://api.alphadefi.fund/"
LIQUIDATION_API = ALPHA_DEFI_API + "historical/kujira/profiles/?datetime="

KUJIRA_ORCA_AUST_VAULT = "terra13nk2cjepdzzwfqy740pxzpe3x75pd6g0grxm2z"
BLUNA = "terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp"
class WhaleSniper:
    def __init__(self):
        self._transactions = []
        self._bids = []
        self._liquidations = []

    def _get_ts(self) -> datetime:
        return datetime.utcnow()
    
    def get_transactions(self):
        self._transactions.clear()
        with open("whale_sniper/whale.txt", "r") as f:
            for w in f.readlines():
                address = w.strip("\n")
                res = requests.get(f"{TXS_API}{address}")
                self._transactions.append(res.json())
    
    def get_bids(self):
        self._bids.clear()
        for transaction in self._transactions:
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
                    timestamp = datetime.strptime(txs["timestamp"], "%Y-%m-%dT%H:%M:%SZ").isoformat(" ")

                    amount = wasm[8]["value"]
                    premium_slot = wasm[9]["value"]
                    strategy_activate_ltv = wasm[12]["value"]
                    strategy_activate_amount = wasm[13]["value"]
                    amount = amount[:-6] if len(amount) > 6 else amount[:-5]

                    rounted_num = round(int(amount))
                    rounted_num = f"{(rounted_num/1000):.1f}K" if (1000000 > rounted_num > 1000) else f"{(rounted_num/1000000):.1f}M" if rounted_num >= 1000000 else rounted_num
                    self._bids.append([timestamp, f"{sender_contract[6:14]}", rounted_num, f"{premium_slot}%", f"{strategy_activate_ltv}%", f"{int(strategy_activate_amount)/1000000000000}M"])

    def extract_bids(self):
        sorted_bids = sorted(self._bids, key=lambda t: datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S"), reverse=True)
        with open("whale_sniper/luna_whale.csv", "w") as csvfile:
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

    def get_liquidations(self):
        self._liquidations.clear()
        timestamp = (self._get_ts() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        res = requests.get(f"{LIQUIDATION_API}{timestamp}")
        for i in res.json():
            self._liquidations.append(i)

    def extract_liquidations(self):
        sorted_liquidations = sorted(self._liquidations, key=lambda t: t["Luna_Liquidation_Price"], reverse=True)
        with open("whale_sniper/luna_liquidation.csv", "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["Luna_Liquidation_Price", "Loan_Value"])
            writer.writeheader()
            for i in sorted_liquidations:
                rounted_num = round(int(i["Loan_Value"]))
                rounted_num = f"{(rounted_num/1000):.1f}K" if (1000000 > rounted_num > 1000) else f"{(rounted_num/1000000):.1f}M" if rounted_num >= 1000000 else rounted_num
                writer.writerow({
                        "Luna_Liquidation_Price": i["Luna_Liquidation_Price"],
                        "Loan_Value": rounted_num
                        })